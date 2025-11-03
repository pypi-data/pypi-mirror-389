import hashlib
import os
import time
from typing import Optional, Callable, Any, Tuple
import threading
from pathlib import Path

import boto3
from botocore.config import Config as BotoCoreConfig
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectionClosedError, ReadTimeoutError
from boto3.s3.transfer import TransferConfig, S3UploadFailedError
from rich import filesize
from tqdm import tqdm

from bayes.client import minio_storage_client
from bayes.client.base import BayesGQLClient
from bayes.model.file.settings import BayesEnvConfig, BayesSettings
from bayes.usercases import dataset_usecase
from bayes.usercases.disk_usecase import IgnoreService, DiskService
from bayes.model.file.openbayes_ignore import IGNORE_FILE_NAME, IGNORE_CLEANUPS, OpenBayesIgnoreSettings
from bayes.usercases.upload_state_manager import UploadStateManager

# 分块上传阈值（8MB）
MULTIPART_THRESHOLD_BYTES = 8 * 1024 * 1024

# 分块上传配置（大于 8MB 开启分块）
transfer_config = TransferConfig(multipart_threshold=MULTIPART_THRESHOLD_BYTES, max_concurrency=5)

# 创建一个进度条回调类
class ProgressPercentage:
    def __init__(self, filename, start_bytes=0):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = start_bytes
        self._lock = threading.Lock()
        self.progress_bar = tqdm(
            total=self._size, 
            unit='B', 
            unit_scale=True, 
            desc=os.path.basename(filename),
            initial=start_bytes  # 从已上传的字节数开始
        )

    def __call__(self, bytes_amount):
        # 当回调被调用时，更新进度条
        with self._lock:
            self._seen_so_far += bytes_amount
            self.progress_bar.update(bytes_amount)
            if self._seen_so_far >= self._size:
                self.progress_bar.close()

# 维护 s3 客户端到会话的映射，便于在通用函数中获取到会话进行刷新
_S3_CLIENT_TO_SESSION = {}


def _build_s3_client(endpoint: str, access_key: str, secret_key: str):
    # 开启 botocore 自带的重试（自适应）作为底层兜底，应用层仍会再做显式重试
    config = BotoCoreConfig(retries={"max_attempts": 10, "mode": "adaptive"})
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=config,
    )


def _unwrap_client_error(e: Exception) -> Tuple[Optional[ClientError], Exception]:
    # boto3 小文件 upload_file 失败常抛 S3UploadFailedError，内部包裹 ClientError
    if isinstance(e, S3UploadFailedError) and hasattr(e, "original_error"):
        orig = getattr(e, "original_error")
        if isinstance(orig, ClientError):
            return orig, e
    if isinstance(e, ClientError):
        return e, e
    return None, e


def _is_auth_related_error(e: Exception) -> bool:
    ce, _ = _unwrap_client_error(e)
    if ce is None:
        return False
    # 仅将明确的认证/签名/凭证相关错误视为需要刷新；
    # 注意：对象不存在的 404（如 NoSuchKey）不应触发刷新，否则会在每个新文件上反复刷新导致凭证抖动
    code = ce.response.get("Error", {}).get("Code", "")
    if code in {
        "AccessDenied",
        "SignatureDoesNotMatch",
        "InvalidAccessKeyId",
        "ExpiredToken",
        "InvalidToken",
        "NoSuchBucket",
        "NoSuchUpload",
        # 可按需补充与认证直接相关的错误码
    }:
        return True
    return False


def _is_transient_error(e: Exception) -> bool:
    # 网络/临时性错误（包括 5xx）
    if isinstance(e, (EndpointConnectionError, ConnectionClosedError, ReadTimeoutError)):
        return True
    ce, _ = _unwrap_client_error(e)
    if ce is not None:
        status = ce.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status and 500 <= int(status) < 600:
            return True
    return False


def _call_with_retry(s3_client, func: Callable[[Any], Any], session=None, max_attempts: int = 5,
                     initial_backoff: float = 0.5):
    attempt = 0
    last_exception = None
    while attempt < max_attempts:
        try:
            return func(s3_client)
        except Exception as e:  # noqa: B902 - 捕获 boto3/网络相关异常
            last_exception = e
            should_refresh = session is not None and _is_auth_related_error(e)
            should_retry = _is_transient_error(e) or should_refresh
            if not should_retry:
                break
            # 刷新凭证（若需要）
            if should_refresh and session is not None:
                try:
                    old_client_id = id(session.s3_client)
                    session.refresh()
                    s3_client = session.s3_client
                    # 更新映射
                    _S3_CLIENT_TO_SESSION.pop(old_client_id, None)
                    _S3_CLIENT_TO_SESSION[id(s3_client)] = session
                except Exception:
                    # 刷新失败直接继续退避重试
                    pass
            # 退避
            sleep_s = initial_backoff * (2 ** attempt)
            time.sleep(min(sleep_s, 8.0))
            attempt += 1
            continue
    raise last_exception if last_exception else RuntimeError("Unknown error without exception")


class UploadSession:
    """封装一次上传会话，支持凭证刷新与 s3 客户端重建。"""

    def __init__(self, party_name: str, dataset_id: str, version: int, directory: str):
        self.party_name = party_name
        self.dataset_id = dataset_id
        self.version = version
        self.directory = directory
        self.policy = None
        self.s3_client = None
        self.bucket_name = ""
        self.minio_path = ""
        self._last_refresh_time = 0.0
        self.refresh()

    def refresh(self):
        self.policy = get_datasetVersion_upload_policy(
            self.party_name, self.dataset_id, self.version, self.directory
        )
        self.s3_client = _build_s3_client(
            self.policy.endpoint, self.policy.accessKey, self.policy.secretKey
        )
        self.bucket_name, self.minio_path = extract_bucket_and_path(self.policy.path)
        self._last_refresh_time = time.time()
        _S3_CLIENT_TO_SESSION[id(self.s3_client)] = self

def get_datasetVersion_upload_policy(party_name:str, datasetId:str, version:int, key:str):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)

    # api server 的接口会对 key 进行相关的校验
    return minio_storage_client.get_datasetVersion_upload_policy(
        gql_client, party_name, datasetId, version, key
    )


def upload(party_name:str, datasetId:str, abs_dataset_path:str, version:int, directory:str):
    try:
        print(f"正在准备上传数据集 {datasetId}...")

        print("正在获取上传授权...")
        session = UploadSession(party_name, datasetId, version, directory)
        s3_client = session.s3_client
        bucket_name, minio_path = session.bucket_name, session.minio_path
        
        # 检查路径是文件还是目录
        is_file = os.path.isfile(abs_dataset_path)
        
        if is_file:
            # 上传单个文件
            print(f"开始上传文件: {os.path.basename(abs_dataset_path)}")
            
            # 构建远程文件路径
            file_name = os.path.basename(abs_dataset_path)
            remote_file_path = f"{minio_path}/{file_name}".replace("\\", "/")
            
            # 使用支持断点续传的上传函数
            result = upload_file_with_resume(s3_client, bucket_name, abs_dataset_path, remote_file_path, session=session)
            
            if result["success"]:
                if result.get("skipped", False):
                    print(f"\n✅ 上传成功! 文件已存在，已跳过上传")
                else:
                    print(f"\n✅ 上传成功!")
                print(f"数据集 {datasetId} 的版本 v{version} 已更新")
                return True
            else:
                print(f"\n❌ 上传失败: {result.get('error', '未知错误')}")
                return False
        else:
            # 上传文件夹
            print(f"开始上传文件，请耐心等待...")
            file_count = count_files(abs_dataset_path)
            print(f"共发现 {file_count} 个文件")
            
            result = upload_folder(s3_client, bucket_name, abs_dataset_path, minio_path, session=session)
            
            if result["success"]:
                print(f"\n✅ 上传成功! 已上传 {result['uploaded']} 个文件，跳过 {result['skipped']} 个已存在文件")
                print(f"数据集 {datasetId} 的版本 v{version} 已更新")
                return True
            else:
                print(f"\n❌ 上传过程中出现错误: {result['error']}")
                print(f"已上传 {result['uploaded']} 个文件，{result['failed']} 个文件上传失败")
                return False
            
    except Exception as e:
        print(f"\n❌ 上传失败: {str(e)}")
        return False


def count_files(directory):
    """计算目录中的文件总数"""
    count = 0
    for _, _, files in os.walk(directory):
        count += len(files)
    return count


def get_md5(file_path):
    """计算文件 MD5 哈希值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def file_exists_in_s3(s3_client, bucket, key, local_file_path):
    """检查 MinIO 中是否已经存在相同的文件（通过文件大小 & MD5 校验）"""
    try:
        # 尝试获取会话，以便在头部请求失败时做刷新/重试
        session = _S3_CLIENT_TO_SESSION.get(id(s3_client))
        response = _call_with_retry(
            s3_client,
            lambda c: c.head_object(Bucket=bucket, Key=key),
            session=session,
        )
        remote_size = response["ContentLength"]
        remote_etag = response.get("ETag", "").strip('"')
        
        # 获取本地文件大小
        local_size = os.path.getsize(local_file_path)
        
        # 如果文件大小不同，则肯定不是同一个文件
        if local_size != remote_size:
            return False
            
        # 检查 ETag 是否为多部分上传格式（包含连字符）
        if "-" in remote_etag:
            # 对于多部分上传的文件，仅比较文件大小
            # 或者可以实现更复杂的分块 MD5 计算（如下注释部分）
            return True
        else:
            # 对于小文件，直接比较 MD5
            local_md5 = get_md5(local_file_path)
            return local_md5 == remote_etag
            
    except ClientError:
        return False  # 文件不存在
    except Exception:
        return False


def upload_folder(s3_client, bucket_name, local_folder, remote_folder, session=None):
    """递归上传整个文件夹（保留目录结构 & 断点续传 & 忽略文件）"""
    results = {
        "success": True,
        "uploaded": 0,
        "skipped": 0,
        "failed": 0,
        "ignored": 0,
        "error": None
    }
    
    try:
        # 仅在目录可写且 .openbayesignore 不存在时创建默认文件；
        # 如果是只读或文件不存在，则不创建，忽略逻辑退化为仅使用内置清单
        ignore_file_path = Path(local_folder) / IGNORE_FILE_NAME
        if not ignore_file_path.exists():
            # 判断目录是否可写
            if os.access(local_folder, os.W_OK):
                try:
                    template_content = OpenBayesIgnoreSettings.read_template()
                    with open(ignore_file_path, 'w', encoding='utf-8') as f:
                        f.write(template_content)
                except Exception:
                    # 写入失败时，继续走仅使用内置清单的逻辑
                    pass
        ignore_service = IgnoreService(str(ignore_file_path), IGNORE_CLEANUPS)
        disk_service = DiskService(ignore_service)
        
        print(f"正在分析文件列表...")
        
        # 获取被忽略的文件
        ignored_files, ignored_dirs, err = ignore_service.ignored(local_folder)
        if err is not None:
            results["success"] = False
            results["error"] = str(err)
            return results
            
        # 使用 left 方法获取未被忽略的文件列表
        unignored_files, _, err = ignore_service.left(local_folder)
        if err is not None:
            results["success"] = False
            results["error"] = str(err)
            return results
        
        # 计算被忽略的文件数量
        total_files = 0
        for _, _, files in os.walk(local_folder):
            total_files += len(files)
        
        results["ignored"] = total_files - len(unignored_files)
        
        print(f"剔除在 {IGNORE_FILE_NAME} 中忽略的文件及文件夹...")
        print(f"共有文件 {len(unignored_files)} 个需要上传，忽略了 {results['ignored']} 个文件")
        
        # 打印被忽略的文件和目录
        if ignored_files:
            print("\n被忽略的文件列表:")
            for file in ignored_files:
                print(f"  - {file}")
                
        if ignored_dirs:
            print("\n被忽略的目录列表:")
            for dir in ignored_dirs:
                print(f"  - {dir}/")
        
        # 上传未被忽略的文件
        for local_file_path in unignored_files:
            # 计算相对路径
            relative_path = os.path.relpath(local_file_path, local_folder)
            remote_file_path = f"{remote_folder}/{relative_path}".replace("\\", "/")  # 处理 Windows 路径

            # 使用支持断点续传的上传函数
            result = upload_file_with_resume(s3_client, bucket_name, local_file_path, remote_file_path, session=session)
            
            if result["success"]:
                if result.get("skipped", False):
                    results["skipped"] += 1
                else:
                    results["uploaded"] += 1
            else:
                results["failed"] += 1
                results["success"] = False
                if not results["error"]:
                    results["error"] = result.get("error", "未知错误")
        
        return results
    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
        return results
        

def extract_bucket_and_path(path: str):
    path = path.lstrip('/')
    parts = path.split('/', 1)
    return [parts[0], parts[1] if len(parts) > 1 else ""]


def upload_file_with_resume(s3_client, bucket_name, local_file_path, remote_file_path, session=None):
    """使用自实现的断点续传上传文件到MinIO
    
    Args:
        s3_client: boto3 S3客户端
        bucket_name: 目标桶名
        local_file_path: 本地文件路径
        remote_file_path: 远程文件路径
        
    Returns:
        字典，包含上传结果信息
    """
    # 初始化状态管理器
    state_manager = UploadStateManager()
    
    try:
        # 检查文件是否已经上传
        if file_exists_in_s3(s3_client, bucket_name, remote_file_path, local_file_path):
            print(f"↷ 跳过: {local_file_path} (已存在)")
            # 清除可能存在的状态文件
            state_manager.clear_state(local_file_path, bucket_name, remote_file_path)
            return {"success": True, "skipped": True}

        # 获取文件大小
        file_size = os.path.getsize(local_file_path)
        
        # 小文件直接上传（不需要断点续传）
        if file_size < MULTIPART_THRESHOLD_BYTES:  # 小于分块上传阈值的文件
            progress_callback = ProgressPercentage(local_file_path)
            _call_with_retry(
                s3_client,
                lambda c: c.upload_file(
                    local_file_path,
                    bucket_name,
                    remote_file_path,
                    Config=transfer_config,
                    Callback=progress_callback,
                ),
                session=session,
            )
            print(f"↑ 已上传: {local_file_path}")
            return {"success": True, "skipped": False}
        
        # 大文件使用分块上传 + 断点续传
        # 查找之前的上传状态
        state = state_manager.get_state(local_file_path, bucket_name, remote_file_path)
        
        # 设置分块大小：至少5MB，且保证总分片数不超过10000（S3/MinIO 上限）
        # 令 part_size >= ceil(file_size / 10000)
        min_size_for_limit = (file_size + 10000 - 1) // 10000
        part_size = max(5 * 1024 * 1024, min_size_for_limit)
        
        # 计算分块数量
        total_parts = (file_size + part_size - 1) // part_size
        
        if state and state.get('upload_id'):
            # 恢复之前的上传
            print(f"找到未完成的上传任务，正在恢复: {os.path.basename(local_file_path)}")
            upload_id = state['upload_id']
            completed_parts = state['parts']
            
            try:
                # 验证上传ID是否仍然有效
                _call_with_retry(
                    s3_client,
                    lambda c: c.list_parts(Bucket=bucket_name, Key=remote_file_path, UploadId=upload_id),
                    session=session,
                )
                print(f"恢复上传ID: {upload_id}")
                # 若状态中记录了历史分片大小，则优先复用，避免分片边界错位
                saved_part_size = state.get('part_size')
                if saved_part_size is not None:
                    part_size = max(5 * 1024 * 1024, int(saved_part_size))
                    total_parts = (file_size + part_size - 1) // part_size
                    print(f"按历史分块大小恢复: {filesize.decimal(part_size)}，共 {total_parts} 个分块")
                    # 如果历史分片大小导致总分片数仍然超过上限，则中止旧上传并重新创建
                    if total_parts > 10000:
                        print("历史分块大小会导致分片数超过 10000，上限受限。正在中止旧上传并重启以增大分块大小...")
                        try:
                            _call_with_retry(
                                s3_client,
                                lambda c: c.abort_multipart_upload(
                                    Bucket=bucket_name,
                                    Key=remote_file_path,
                                    UploadId=upload_id,
                                ),
                                session=session,
                            )
                        except Exception:
                            # 忽略中止异常，继续重启
                            pass
                        state_manager.clear_state(local_file_path, bucket_name, remote_file_path)
                        # 按新的安全分块大小重启
                        min_size_for_limit = (file_size + 10000 - 1) // 10000
                        part_size = max(5 * 1024 * 1024, min_size_for_limit)
                        print(f"开始新的分块上传: {os.path.basename(local_file_path)}")
                        response = _call_with_retry(
                            s3_client,
                            lambda c: c.create_multipart_upload(Bucket=bucket_name, Key=remote_file_path),
                            session=session,
                        )
                        upload_id = response['UploadId']
                        completed_parts = []
                        state_manager.save_state(
                            local_file_path, bucket_name, remote_file_path,
                            upload_id, completed_parts, part_size=part_size
                        )
                        print(f"创建新的上传ID: {upload_id}")
                else:
                    # 旧版本状态文件无法确定历史分片大小，安全起见中止旧上传并重启
                    print("检测到旧版上传状态（缺少分片大小），为避免分片错位，正在中止旧上传并重启...")
                    try:
                        _call_with_retry(
                            s3_client,
                            lambda c: c.abort_multipart_upload(
                                Bucket=bucket_name,
                                Key=remote_file_path,
                                UploadId=upload_id,
                            ),
                            session=session,
                        )
                    except Exception:
                        pass
                    state_manager.clear_state(local_file_path, bucket_name, remote_file_path)
                    # 重新开始新的上传
                    min_size_for_limit = (file_size + 10000 - 1) // 10000
                    part_size = max(5 * 1024 * 1024, min_size_for_limit)
                    print(f"开始新的分块上传: {os.path.basename(local_file_path)}")
                    response = _call_with_retry(
                        s3_client,
                        lambda c: c.create_multipart_upload(Bucket=bucket_name, Key=remote_file_path),
                        session=session,
                    )
                    upload_id = response['UploadId']
                    completed_parts = []
                    state_manager.save_state(
                        local_file_path, bucket_name, remote_file_path,
                        upload_id, completed_parts, part_size=part_size
                    )
                    print(f"创建新的上传ID: {upload_id}")
                print(f"已上传 {len(completed_parts)} 个分块，共 {total_parts} 个分块")
            except Exception as e:
                # 上传ID无效，需要重新开始
                print(f"无法恢复之前的上传: {e}")
                state = None
                completed_parts = []
        else:
            # 开始新的上传
            print(f"开始新的分块上传: {os.path.basename(local_file_path)}")
            response = _call_with_retry(
                s3_client,
                lambda c: c.create_multipart_upload(Bucket=bucket_name, Key=remote_file_path),
                session=session,
            )
            upload_id = response['UploadId']
            completed_parts = []
            # 保存初始状态
            state_manager.save_state(
                local_file_path, bucket_name, remote_file_path, 
                upload_id, completed_parts, part_size=part_size
            )
            print(f"创建新的上传ID: {upload_id}")
        
        # 计算已完成的字节数
        completed_bytes = 0
        for part in completed_parts:
            part_num = part['PartNumber']
            # 估算完成的字节数
            if part_num < total_parts:
                completed_bytes += part_size
            else:
                completed_bytes += file_size % part_size or part_size
        
        # 创建进度条，直接设置初始值为已完成字节数
        progress = tqdm(
            total=file_size,
            unit='B',
            unit_scale=True,
            desc=os.path.basename(local_file_path),
            initial=completed_bytes  # 关键修改：设置初始值
        )
        
        # 已上传分块的编号集合
        uploaded_part_numbers = {part['PartNumber'] for part in completed_parts}
        
        try:
            # 打开文件
            with open(local_file_path, 'rb') as f:
                # 上传每个分块
                for part_num in range(1, total_parts + 1):
                    # 如果该分块已上传，跳过
                    if part_num in uploaded_part_numbers:
                        continue
                    
                    # 定位到正确的文件位置
                    f.seek((part_num - 1) * part_size)
                    
                    # 读取当前分块
                    if part_num == total_parts:
                        # 最后一个分块可能较小
                        data = f.read(file_size - (part_num - 1) * part_size)
                    else:
                        data = f.read(part_size)
                    
                    # 上传分块
                    response = _call_with_retry(
                        s3_client,
                        lambda c: c.upload_part(
                            Bucket=bucket_name,
                            Key=remote_file_path,
                            PartNumber=part_num,
                            UploadId=upload_id,
                            Body=data,
                        ),
                        session=session,
                    )
                    
                    # 记录已上传的分块
                    etag = response['ETag']
                    completed_parts.append({
                        'PartNumber': part_num,
                        'ETag': etag
                    })
                    
                    # 更新进度条
                    progress.update(len(data))
                    
                    # 保存上传状态（记录分片大小，保证可恢复性）
                    state_manager.save_state(
                        local_file_path, bucket_name, remote_file_path,
                        upload_id, completed_parts, part_size=part_size
                    )
            
            # 完成分块上传
            completed_parts.sort(key=lambda x: x['PartNumber'])
            _call_with_retry(
                s3_client,
                lambda c: c.complete_multipart_upload(
                    Bucket=bucket_name,
                    Key=remote_file_path,
                    UploadId=upload_id,
                    MultipartUpload={'Parts': completed_parts},
                ),
                session=session,
            )
            
            # 关闭进度条
            progress.close()
            
            # 清除状态文件
            state_manager.clear_state(local_file_path, bucket_name, remote_file_path)
            
            print(f"↑ 已上传: {local_file_path}")
            return {"success": True, "skipped": False}
            
        except KeyboardInterrupt:
            # 用户中断，保存当前状态
            progress.close()
            print(f"\n上传已暂停: {local_file_path}")
            print(f"上传进度已保存，下次运行时将继续上传")
            return {"success": False, "error": "用户中断"}
            
        except Exception as e:
            # 其他错误
            progress.close()
            print(f"✗ 上传出错: {local_file_path} - {str(e)}")
            return {"success": False, "error": str(e)}
            
    except Exception as e:
        print(f"✗ 上传失败: {local_file_path} - {str(e)}")
        return {"success": False, "error": str(e)}


def upload_file(s3_client, bucket_name, local_file_path, remote_file_path):
    return upload_file_with_resume(s3_client, bucket_name, local_file_path, remote_file_path)


def upload_source_code(party_name: str, source_code_path: str, storageType: str):
    try:
        print(f"正在准备上传源代码...")
        print("正在获取上传授权...")
        policy = get_source_code_upload_policy(party_name, storageType)

        s3_client = boto3.client(
            "s3",
            endpoint_url=policy.endpoint,
            aws_access_key_id=policy.accessKey,
            aws_secret_access_key=policy.secretKey
        )
        
        bucket_name, minio_path = extract_bucket_and_path(policy.path)
        
        # Check if source_code_path exists
        if not os.path.exists(source_code_path):
            print(f"❌ 路径不存在: {source_code_path}")
            return None
            
        print(f"开始扫描文件，请稍候...")
        
        # Get all files in the directory and subdirectories
        all_files = []
        total_size = 0
        for root, _, files in os.walk(source_code_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                all_files.append((file_path, file_size))
                total_size += file_size
        
        total_files = len(all_files)
        print(f"共发现 {total_files} 个文件，总计 {filesize.decimal(total_size)}，开始上传...")
        
        # Create a single progress bar for all files
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc="上传进度"
        ) as overall_progress:
            
            # Upload each file and update the overall progress
            uploaded_count = 0
            failed_count = 0
            
            for local_file_path, file_size in all_files:
                try:
                    # Calculate relative path
                    relative_path = os.path.relpath(local_file_path, source_code_path)
                    remote_file_path = f"{minio_path}/{relative_path}".replace("\\", "/")
                    
                    # Show current file being uploaded (without progress)
                    current_file = os.path.basename(local_file_path)
                    overall_progress.set_description(f"上传: {current_file}")
                    
                    # Define callback for updating overall progress
                    def progress_callback(bytes_amount):
                        overall_progress.update(bytes_amount)
                    
                    # Upload file
                    s3_client.upload_file(
                        local_file_path,
                        bucket_name,
                        remote_file_path,
                        Callback=progress_callback
                    )
                    
                    uploaded_count += 1
                    
                    # Update description to show progress
                    percentage = int((uploaded_count / total_files) * 100)
                    overall_progress.set_description(f"上传进度: {percentage}% ({uploaded_count}/{total_files})")
                    
                except Exception as e:
                    print(f"\n✗ 上传失败: {local_file_path} - {str(e)}")
                    failed_count += 1

        if failed_count == 0:
            print(f"\n✅ 源代码上传成功! 已上传 {uploaded_count} 个文件")
            return policy.id
        else:
            print(f"\n⚠️ 源代码上传部分完成: 成功 {uploaded_count} 个文件，失败 {failed_count} 个文件")
            return None
            
    except Exception as e:
        print(f"\n❌ 上传失败: {str(e)}")
        return None


def get_source_code_upload_policy(party_name: str, storageType: str):
    default_env: Optional[BayesEnvConfig] = BayesSettings().default_env
    gql_client = BayesGQLClient(default_env.graphQL, default_env.token)
    policy = minio_storage_client.get_source_code_upload_policy(gql_client, party_name, storageType)
    return policy