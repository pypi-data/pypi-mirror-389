"""
Upload utilities for XiaoShi AI Hub SDK using GitPython
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import List, Optional, Union, Callable, Dict, Any
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone

from xiaoshiai_hub.client import DEFAULT_BASE_URL

try:
    from git import Repo, GitCommandError, InvalidGitRepositoryError
except ImportError:
    raise ImportError(
        "GitPython is required for upload functionality. "
        "Install it with: pip install gitpython"
    )

try:
    from tqdm.auto import tqdm
except ImportError:
    tqdm = None

from .exceptions import HubException, AuthenticationError, RepositoryNotFoundError, EncryptionError


class UploadError(HubException):
    """Raised when an upload operation fails."""
    pass


def _build_git_url(
    base_url: Optional[str],
    organization: str,
    repo_type: str,
    repo_name: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
) -> str:
    """
    Build Git repository URL with authentication.
    
    Args:
        base_url: Base URL of the Hub API
        organization: Organization name
        repo_type: Repository type ("models" or "datasets")
        repo_name: Repository name
        username: Username for authentication
        password: Password for authentication
        token: Token for authentication
        
    Returns:
        Git repository URL with embedded credentials
    """
    # Parse base URL to get the host
    base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
    parsed = urlparse(base_url)
    host = parsed.netloc
    scheme = parsed.scheme or 'https'
    
    # Build repository path
    repo_path = f"moha/{organization}/{repo_type}/{repo_name}.git"
    
    # Add authentication to URL
    if token:
        # Use token as username with empty password
        netloc = f"oauth2:{token}@{host}"
    elif username and password:
        netloc = f"{username}:{password}@{host}"
    else:
        netloc = host
    
    # Construct full URL
    git_url = urlunparse((scheme, netloc, repo_path, '', '', ''))
    
    return git_url


def _calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _should_encrypt_file(file_path: str, encryption_exclude: List[str]) -> bool:
    """
    Check if a file should be encrypted based on exclude patterns.

    Args:
        file_path: Relative path of the file (relative to folder_path)
        encryption_exclude: List of patterns to exclude from encryption

    Returns:
        True if file should be encrypted, False otherwise
    """
    import fnmatch

    if not encryption_exclude:
        return True

    for pattern in encryption_exclude:
        # Match against the full relative path
        if fnmatch.fnmatch(file_path, pattern):
            return False

    return True


def _create_encryption_metadata(
    encrypted_files: List[Dict[str, Any]],
    algorithm: str,
    version: str = "1.0"
) -> Dict[str, Any]:
    """
    Create encryption metadata structure.

    Args:
        encrypted_files: List of encrypted file information
        algorithm: Encryption algorithm used
        version: Metadata format version

    Returns:
        Encryption metadata dictionary
    """
    return {
        "version": version,
        "createAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "files": encrypted_files
    }


def _write_encryption_metadata(repo_path: Path, metadata: Dict[str, Any]) -> None:
    """
    Write encryption metadata to .moha_encryption file.

    Args:
        repo_path: Path to the repository
        metadata: Encryption metadata dictionary
    """
    metadata_file = repo_path / ".moha_encryption"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"Encryption metadata written to .moha_encryption")


def _count_files_in_directory(directory: str, ignore_patterns: Optional[List[str]] = None) -> int:
    """
    Count total number of files in a directory.

    Args:
        directory: Directory path
        ignore_patterns: List of patterns to ignore (e.g., ['.git', '__pycache__'])

    Returns:
        Total number of files
    """
    import fnmatch

    count = 0

    for root, dirs, files in os.walk(directory):
        # Get relative path from directory
        rel_root = os.path.relpath(root, directory)

        if ignore_patterns:
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
            )]

        if ignore_patterns:
            filtered_files = []
            for f in files:
                # Construct relative file path
                if rel_root == '.':
                    rel_file_path = f
                else:
                    rel_file_path = os.path.join(rel_root, f)

                # Check if file matches any ignore pattern
                should_ignore = any(
                    fnmatch.fnmatch(rel_file_path, pattern) for pattern in ignore_patterns
                )
                if not should_ignore:
                    filtered_files.append(f)
            files = filtered_files

        count += len(files)

    return count


def upload_folder(
    folder_path: Union[str, Path],
    repo_id: str,
    repo_type: str = "models",
    revision: str = "main",
    commit_message: Optional[str] = None,
    commit_description: Optional[str] = None,
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
    ignore_patterns: Optional[List[str]] = None, # 上传的时候忽略的文件
    encryption_key: Optional[Union[str, bytes]] = None,
    encryption_exclude: Optional[List[str]] = None, # 加密的时候排除的文件
    encryption_algorithm: Optional[str] = None,
    temp_dir: Optional[Union[str, Path]] = None,
    skip_lfs: Optional[bool] = True,
) -> str:
    """
    Upload a folder to a repository using Git.

    This function clones the repository, copies files from the folder,
    commits the changes, and pushes to the remote repository.

    Args:
        folder_path: Path to the folder to upload
        repo_id: Repository ID in the format "organization/repo_name"
        repo_type: Type of repository ("models" or "datasets")
        revision: Branch to upload to (default: "main")
        commit_message: Commit message (default: "Upload folder")
        commit_description: Additional commit description
        base_url: Base URL of the Hub API
        username: Username for authentication
        password: Password for authentication
        token: Token for authentication (preferred over username/password)
        ignore_patterns: List of patterns to ignore (e.g., ['.git', '*.pyc', '__pycache__'])
        encryption_key: Encryption key for encrypted repositories (string for symmetric, PEM for asymmetric)
        encryption_exclude: List of file patterns to exclude from encryption (e.g., ['*.txt', 'README.md'])
        encryption_algorithm: Encryption algorithm to use (default: 'aes-256-cbc')
            - Symmetric: 'aes-256-cbc', 'aes-256-gcm'
            - Asymmetric: 'rsa-oaep', 'rsa-pkcs1v15' (requires RSA public key in PEM format)
        temp_dir: Custom temporary directory path for cloning repository (default: system temp directory)
        skip_lfs: Skip LFS files when cloning the repository (default: True)

    Returns:
        Commit hash of the uploaded changes

    Raises:
        RepositoryNotFoundError: If the repository does not exist
        EncryptionError: If repository requires encryption but encryption_key is not provided

    Example:
        >>> commit_hash = upload_folder(
        ...     folder_path="./my_model",
        ...     repo_id="demo/my-model",
        ...     repo_type="models",
        ...     commit_message="Upload model files",
        ...     token="your-token",
        ... )

        >>> # Upload to encrypted repository
        >>> commit_hash = upload_folder(
        ...     folder_path="./my_model",
        ...     repo_id="demo/encrypted-model",
        ...     repo_type="models",
        ...     encryption_key="my-secret-key",
        ...     encryption_exclude=["README.md", "*.txt"],
        ...     token="your-token",
        ... )
    """
    import tempfile
    import fnmatch
    from .client import HubClient

    parts = repo_id.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid repo_id format: {repo_id}. Expected 'organization/repo_name'")

    organization, repo_name = parts
    client = HubClient(
        base_url=base_url,
        username=username,
        password=password,
        token=token,
    )
    is_encrypted = bool(encryption_key)
    # Validate folder path
    folder_path = Path(folder_path)
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    if not folder_path.is_dir():
        raise ValueError(f"Path is not a directory: {folder_path}")

    if ignore_patterns is None:
        ignore_patterns = []

    if encryption_exclude is None:
        encryption_exclude = []
    
    # Build Git URL
    git_url = _build_git_url(
        base_url=base_url,
        organization=organization,
        repo_type=repo_type,
        repo_name=repo_name,
        username=username,
        password=password,
        token=token,
    )
    
    if temp_dir is not None:
        import uuid
        temp_dir_path = Path(temp_dir)
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        unique_dir = temp_dir_path / f"upload_{uuid.uuid4().hex[:8]}"
        unique_dir.mkdir(parents=True, exist_ok=True)
        temp_context = None
        working_temp_dir = unique_dir
    else:
        temp_context = tempfile.TemporaryDirectory()
        working_temp_dir = Path(temp_context.__enter__())
        unique_dir = None

    try:
        repo_path = working_temp_dir / "repo"

        try:
            try:
                env_mapping = None
                if skip_lfs:
                    env_mapping={'GIT_LFS_SKIP_SMUDGE': "1"}
                repo = Repo.clone_from(
                    git_url,
                    repo_path,
                    branch=revision,
                    depth=1,
                    env=env_mapping,
                )
            except GitCommandError as e:
                if "Authentication failed" in str(e) or "authentication" in str(e).lower():
                    raise AuthenticationError(f"Authentication failed: {e}")
                raise UploadError(f"Failed to clone repository: {e}")
            
            # 过滤掉忽略的文件，需要上传的文件总数
            total_files = _count_files_in_directory(str(folder_path), ignore_patterns)
            print(f"Copying files from {folder_path} to repository...")
            progress_bar = None
            if tqdm is not None and total_files > 0:
                progress_bar = tqdm(
                    total=total_files,
                    unit='file',
                    desc="Copying files",
                    leave=True,
                )
            
            files_copied = 0
            files_to_encrypt = []  # 标记哪些文件需要加密

            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [d for d in dirs if not any(
                    fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns
                )]

                # 相对路径
                rel_root = os.path.relpath(root, folder_path)
                if rel_root == '.':
                    dest_root = repo_path
                else:
                    dest_root = repo_path / rel_root

                # Create destination directory
                dest_root.mkdir(parents=True, exist_ok=True)

                # Copy files
                for file in files:
                    # Construct relative file path (relative to folder_path)
                    if rel_root == '.':
                        rel_file_path = file
                    else:
                        rel_file_path = os.path.join(rel_root, file)

                    # Check ignore patterns using full relative path
                    if any(fnmatch.fnmatch(rel_file_path, pattern) for pattern in ignore_patterns):
                        continue

                    src_file = Path(root) / file
                    dest_file = dest_root / file

                    # Copy file
                    shutil.copy2(src_file, dest_file)
                    files_copied += 1

                    # 把需要加密的文件写入列表 (使用完整相对路径)
                    if is_encrypted and _should_encrypt_file(rel_file_path, encryption_exclude):
                        files_to_encrypt.append(dest_file)

                    if progress_bar is not None:
                        progress_bar.update(1)

            if progress_bar is not None:
                progress_bar.close()

            print(f"Copied {files_copied} files")

            # 处理加密元数据文件
            metadata_file = repo_path / ".moha_encryption"

            # 加密
            if is_encrypted and files_to_encrypt:
                # Determine encryption algorithm
                from .encryption import EncryptionAlgorithm, encrypt_file as encrypt_file_func

                if encryption_algorithm is None:
                    algorithm = EncryptionAlgorithm.AES_256_CBC
                else:
                    try:
                        algorithm = EncryptionAlgorithm(encryption_algorithm)
                    except ValueError:
                        raise EncryptionError(
                            f"Invalid encryption algorithm: {encryption_algorithm}. "
                            f"Supported algorithms: {', '.join([a.value for a in EncryptionAlgorithm])}"
                        )

                print(f"Encrypting {len(files_to_encrypt)} files using {algorithm.value}...")
                encrypt_progress = None
                if tqdm is not None:
                    encrypt_progress = tqdm(
                        total=len(files_to_encrypt),
                        unit='file',
                        desc="Encrypting files",
                        leave=True,
                    )

                # 收集加密文件的元数据
                encrypted_files_metadata = []

                for file_path in files_to_encrypt:
                    # 加密文件
                    encrypt_file_func(file_path, encryption_key, algorithm)

                    # 计算加密后的文件信息
                    encrypted_size = file_path.stat().st_size
                    encrypted_hash = _calculate_file_hash(file_path)

                    # 获取相对于 repo_path 的路径
                    rel_path = file_path.relative_to(repo_path)

                    # 添加到元数据列表
                    encrypted_files_metadata.append({
                        "path": str(rel_path),
                        "algorithm": algorithm.value,
                        "encryptedSize": encrypted_size,
                        "encryptedHash": encrypted_hash,
                    })

                    if encrypt_progress is not None:
                        encrypt_progress.update(1)

                if encrypt_progress is not None:
                    encrypt_progress.close()

                print(f"Encrypted {len(files_to_encrypt)} files")

                # 写入加密元数据文件
                encryption_metadata = _create_encryption_metadata(
                    encrypted_files=encrypted_files_metadata,
                    algorithm=algorithm.value
                )
                _write_encryption_metadata(repo_path, encryption_metadata)
            else:
                # 如果不是加密上传，删除可能存在的加密元数据文件
                if metadata_file.exists():
                    metadata_file.unlink()
                    print("Removed .moha_encryption file (non-encrypted upload)")

            repo.git.add(A=True)
            
            if not repo.is_dirty() and not repo.untracked_files:
                print("No changes to commit")
                return repo.head.commit.hexsha
            
            if commit_message is None:
                commit_message = f"Upload folder from {folder_path.name}"
            
            full_message = commit_message
            if commit_description:
                full_message = f"{commit_message}\n\n{commit_description}"
            
            # Commit changes
            print(f"Committing changes: {commit_message}")
            commit = repo.index.commit(full_message)
            try:
                origin = repo.remote(name='origin')
                origin.push(refspec=f'{revision}:{revision}')
            except GitCommandError as e:
                if "Authentication failed" in str(e) or "authentication" in str(e).lower():
                    raise AuthenticationError(f"Authentication failed during push: {e}")
                raise UploadError(f"Failed to push changes: {e}")
            
            print(f"Successfully uploaded to {repo_id}")
            print(f"Commit hash: {commit.hexsha}")
            
            return commit.hexsha

        except (GitCommandError, InvalidGitRepositoryError) as e:
            raise UploadError(f"Git operation failed: {e}")
    finally:
        # Clean up temporary directory
        if temp_context is not None:
            # Clean up system temp directory
            try:
                temp_context.__exit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
        elif unique_dir is not None:
            # Clean up custom temp directory
            try:
                import shutil as shutil_cleanup
                shutil_cleanup.rmtree(unique_dir, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors


def upload_file(
    path_or_fileobj: Union[str, Path, bytes],
    path_in_repo: str,
    repo_id: str,
    repo_type: str = "models",
    revision: str = "main",
    commit_message: Optional[str] = None,
    commit_description: Optional[str] = None,
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    token: Optional[str] = None,
    encryption_key: Optional[Union[str, bytes]] = None,
    encryption_algorithm: Optional[str] = None,
    temp_dir: Optional[Union[str, Path]] = None,
    skip_lfs: Optional[bool] = True, # 当克隆仓库的时候，跳过lfs的大文件下载,只需要下载lfs文件指针
) -> str:
    """
    Upload a single file to a repository.

    Args:
        path_or_fileobj: Path to the file or file content as bytes
        path_in_repo: Path where the file should be stored in the repository
        repo_id: Repository ID in the format "organization/repo_name"
        repo_type: Type of repository ("models" or "datasets")
        revision: Branch to upload to (default: "main")
        commit_message: Commit message
        commit_description: Additional commit description
        base_url: Base URL of the Hub API
        username: Username for authentication
        password: Password for authentication
        token: Token for authentication
        encryption_key: Encryption key for encrypted repositories (string for symmetric, PEM for asymmetric)
        encryption_algorithm: Encryption algorithm to use (default: 'aes-256-cbc')
            - Symmetric: 'aes-256-cbc', 'aes-256-gcm'
            - Asymmetric: 'rsa-oaep', 'rsa-pkcs1v15' (requires RSA public key in PEM format)
        temp_dir: Custom temporary directory path for cloning repository (default: system temp directory)
        skip_lfs: Skip LFS files when cloning the repository (default: True)

    Returns:
        Commit hash of the uploaded file

    Raises:
        RepositoryNotFoundError: If the repository does not exist
        EncryptionError: If repository requires encryption but encryption_key is not provided

    Example:
        >>> commit_hash = upload_file(
        ...     path_or_fileobj="./config.yaml",
        ...     path_in_repo="config.yaml",
        ...     repo_id="demo/my-model",
        ...     commit_message="Upload config file",
        ...     token="your-token",
        ... )

        >>> # Upload to encrypted repository
        >>> commit_hash = upload_file(
        ...     path_or_fileobj="./model.bin",
        ...     path_in_repo="model.bin",
        ...     repo_id="demo/encrypted-model",
        ...     encryption_key="my-secret-key",
        ...     token="your-token",
        ... )
    """
    import tempfile
    from .client import HubClient

    # Parse repo_id
    parts = repo_id.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid repo_id format: {repo_id}. Expected 'organization/repo_name'")

    organization, repo_name = parts

    client = HubClient(
        base_url=base_url,
        username=username,
        password=password,
        token=token,
    )
    is_encrypted = bool(encryption_key)
    # 构建 Git URL
    git_url = _build_git_url(
        base_url=base_url,
        organization=organization,
        repo_type=repo_type,
        repo_name=repo_name,
        username=username,
        password=password,
        token=token,
    )
    
    # 该临时目录用来存储克隆的仓库
    if temp_dir is not None:
        # 创建子目录
        import uuid
        temp_dir_path = Path(temp_dir)
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        unique_dir = temp_dir_path / f"upload_{uuid.uuid4().hex[:8]}"
        unique_dir.mkdir(parents=True, exist_ok=True)
        temp_context = None
        working_temp_dir = unique_dir
    else:
        # 使用系统的临时目录
        temp_context = tempfile.TemporaryDirectory()
        working_temp_dir = Path(temp_context.__enter__())
        unique_dir = None

    try:
        repo_path = working_temp_dir / "repo"

        try:
            # 克隆远程仓库到临时目录，depth=1，只克隆最新的提交,减少数据量
            try:
                env_mapping = None
                if skip_lfs:
                    env_mapping={'GIT_LFS_SKIP_SMUDGE': "1"}
                repo = Repo.clone_from(
                    git_url,
                    repo_path,
                    branch=revision,
                    depth=1,
                    env=env_mapping,
                )
            except GitCommandError as e:
                if "Authentication failed" in str(e) or "authentication" in str(e).lower():
                    raise AuthenticationError(f"Authentication failed: {e}")
                raise UploadError(f"Failed to clone repository: {e}")
            
            # Prepare file path in repository
            file_path = repo_path / path_in_repo
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            if isinstance(path_or_fileobj, bytes):
                # Write bytes directly
                file_path.write_bytes(path_or_fileobj)
            else:
                # Copy from source file
                source_path = Path(path_or_fileobj)
                if not source_path.exists():
                    raise FileNotFoundError(f"File not found: {source_path}")
                shutil.copy2(source_path, file_path)

            print(f"Added file: {path_in_repo}")

            # 处理加密元数据文件
            metadata_file = repo_path / ".moha_encryption"
            metadata_updated = False

            # Encrypt file if repository is encrypted
            if is_encrypted:
                # Determine encryption algorithm
                from .encryption import EncryptionAlgorithm, encrypt_file as encrypt_file_func

                if encryption_algorithm is None:
                    algorithm = EncryptionAlgorithm.AES_256_CBC
                else:
                    try:
                        algorithm = EncryptionAlgorithm(encryption_algorithm)
                    except ValueError:
                        raise EncryptionError(
                            f"Invalid encryption algorithm: {encryption_algorithm}. "
                            f"Supported algorithms: {', '.join([a.value for a in EncryptionAlgorithm])}"
                        )

                print(f"Encrypting file: {path_in_repo} using {algorithm.value}")
                encrypt_file_func(file_path, encryption_key, algorithm)
                print(f"File encrypted")

                # 计算加密后的文件信息
                encrypted_size = file_path.stat().st_size
                encrypted_hash = _calculate_file_hash(file_path)

                # 读取或创建加密元数据文件
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        encryption_metadata = json.load(f)
                else:
                    encryption_metadata = {
                        "version": "1.0",
                        "createAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "files": []
                    }

                # 更新或添加文件信息
                file_info = {
                    "path": path_in_repo,
                    "algorithm": algorithm.value,
                    "encryptedSize": encrypted_size,
                    "encryptedHash": encrypted_hash,
                }

                # 检查文件是否已存在，如果存在则更新
                existing_index = None
                for i, f in enumerate(encryption_metadata["files"]):
                    if f["path"] == path_in_repo:
                        existing_index = i
                        break

                if existing_index is not None:
                    encryption_metadata["files"][existing_index] = file_info
                else:
                    encryption_metadata["files"].append(file_info)

                # 写入元数据文件
                _write_encryption_metadata(repo_path, encryption_metadata)
                metadata_updated = True
            else:
                # 如果不是加密上传，从元数据文件中移除该文件（如果存在）
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        encryption_metadata = json.load(f)

                    # 查找并移除该文件
                    original_count = len(encryption_metadata["files"])
                    encryption_metadata["files"] = [
                        f for f in encryption_metadata["files"]
                        if f["path"] != path_in_repo
                    ]

                    if len(encryption_metadata["files"]) < original_count:
                        # 文件被移除了
                        if len(encryption_metadata["files"]) == 0:
                            # 如果没有加密文件了，删除元数据文件
                            metadata_file.unlink()
                            print(f"Removed .moha_encryption file (no encrypted files remaining)")
                        else:
                            # 更新元数据文件
                            _write_encryption_metadata(repo_path, encryption_metadata)
                            print(f"Updated .moha_encryption file (removed {path_in_repo})")
                        metadata_updated = True

            # Add file to git
            repo.git.add(path_in_repo)

            # 如果元数据文件被更新，也添加到 git
            if metadata_updated:
                if metadata_file.exists():
                    repo.git.add(".moha_encryption")
                else:
                    # 如果文件被删除，确保从 git 中移除
                    try:
                        repo.git.rm(".moha_encryption")
                    except GitCommandError:
                        # 文件可能不在 git 中，忽略错误
                        pass
            
            # Check if there are changes
            if not repo.is_dirty() and not repo.untracked_files:
                print("No changes to commit (file already exists with same content)")
                return repo.head.commit.hexsha
            
            # Create commit message
            if commit_message is None:
                commit_message = f"Upload {path_in_repo}"
            
            full_message = commit_message
            if commit_description:
                full_message = f"{commit_message}\n\n{commit_description}"
            
            # Commit changes
            print(f"Committing changes: {commit_message}")
            commit = repo.index.commit(full_message)
            
            # Push to remote
            print(f"Pushing to {revision}...")
            try:
                origin = repo.remote(name='origin')
                origin.push(refspec=f'{revision}:{revision}')
            except GitCommandError as e:
                if "Authentication failed" in str(e) or "authentication" in str(e).lower():
                    raise AuthenticationError(f"Authentication failed during push: {e}")
                raise UploadError(f"Failed to push changes: {e}")
            
            print(f"Successfully uploaded {path_in_repo} to {repo_id}")
            print(f"Commit hash: {commit.hexsha}")
            
            return commit.hexsha

        except (GitCommandError, InvalidGitRepositoryError) as e:
            raise UploadError(f"Git operation failed: {e}")
    finally:
        # Clean up temporary directory
        if temp_context is not None:
            # Clean up system temp directory
            try:
                temp_context.__exit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors
        elif unique_dir is not None:
            # Clean up custom temp directory
            try:
                import shutil as shutil_cleanup
                shutil_cleanup.rmtree(unique_dir, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors



