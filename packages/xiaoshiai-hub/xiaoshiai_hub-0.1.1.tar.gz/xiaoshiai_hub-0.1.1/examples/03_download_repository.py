#!/usr/bin/env python3
"""
下载整个仓库示例 - XiaoShi AI Hub Python SDK

本示例演示如何下载整个仓库：
- 下载完整仓库
- 下载加密仓库（自动解密）
- 使用过滤器下载部分文件
- 排除特定文件或目录
"""

from xiaoshiai_hub import snapshot_download
from xiaoshiai_hub.encryption import EncryptionAlgorithm
import os


def download_full_repository():
    """下载完整仓库"""
    print("=" * 80)
    print("示例 3.1: 下载完整仓库")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    LOCAL_DIR = "./downloads/full_repository"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    print(f"📥 下载完整仓库:")
    print(f"  仓库: {REPO_ID}")
    print(f"  类型: {REPO_TYPE}")
    print(f"  保存到: {LOCAL_DIR}")
    print()

    try:
        repo_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            username=USERNAME,
            password=PASSWORD,
            verbose=True,  # 显示详细进度
        )
        print()
        print(f"✅ 仓库已下载到: {repo_path}")
        
        # 统计下载的文件
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(repo_path):
            file_count += len(files)
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        print(f"  文件数量: {file_count}")
        print(f"  总大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def download_encrypted_repository():
    """下载加密仓库"""
    print("=" * 80)
    print("示例 3.2: 下载加密仓库")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    LOCAL_DIR = "./downloads/encrypted_repository"

    # 从环境变量读取认证信息和解密密钥
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")
    DECRYPTION_KEY = os.environ.get("DECRYPTION_KEY", "S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB")

    print(f"📥 下载加密仓库:")
    print(f"  仓库: {REPO_ID}")
    print(f"  类型: {REPO_TYPE}")
    print(f"  保存到: {LOCAL_DIR}")
    print(f"  解密算法: AES-256-CBC")
    print()

    try:
        repo_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            username=USERNAME,
            password=PASSWORD,
            decryption_key=DECRYPTION_KEY,
            decryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
            verbose=True,
        )
        print()
        print(f"✅ 仓库已下载并解密到: {repo_path}")
        
        # 统计下载的文件
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(repo_path):
            file_count += len(files)
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        
        print(f"  文件数量: {file_count}")
        print(f"  总大小: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def download_with_filters():
    """使用过滤器下载"""
    print("=" * 80)
    print("示例 3.3: 使用过滤器下载")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    LOCAL_DIR = "./downloads/filtered_repository"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 过滤器配置
    ALLOW_PATTERNS = ["*.yaml", "*.yml", "*.md"]  # 只下载这些类型的文件
    IGNORE_PATTERNS = [".git*", "*.log"]  # 忽略这些文件

    print(f"📥 使用过滤器下载仓库:")
    print(f"  仓库: {REPO_ID}")
    print(f"  类型: {REPO_TYPE}")
    print(f"  保存到: {LOCAL_DIR}")
    print(f"  允许模式: {ALLOW_PATTERNS}")
    print(f"  忽略模式: {IGNORE_PATTERNS}")
    print()

    try:
        repo_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            allow_patterns=ALLOW_PATTERNS,
            ignore_patterns=IGNORE_PATTERNS,
            username=USERNAME,
            password=PASSWORD,
            verbose=True,
        )
        print()
        print(f"✅ 仓库已下载到: {repo_path}")
        
        # 列出下载的文件
        print(f"  下载的文件:")
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                file_size = os.path.getsize(os.path.join(root, file))
                print(f"    📄 {rel_path} ({file_size:,} bytes)")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def download_with_ignore_patterns():
    """使用忽略模式下载"""
    print("=" * 80)
    print("示例 3.4: 排除特定文件下载")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    LOCAL_DIR = "./downloads/ignore_patterns"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 忽略模式
    IGNORE_PATTERNS = ["subdir/*", "*.tmp", ".git*"]

    print(f"📥 排除特定文件下载:")
    print(f"  仓库: {REPO_ID}")
    print(f"  类型: {REPO_TYPE}")
    print(f"  保存到: {LOCAL_DIR}")
    print(f"  忽略模式: {IGNORE_PATTERNS}")
    print()

    try:
        repo_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            ignore_patterns=IGNORE_PATTERNS,
            username=USERNAME,
            password=PASSWORD,
            verbose=True,
        )
        print()
        print(f"✅ 仓库已下载到: {repo_path}")
        
        # 列出下载的文件
        print(f"  下载的文件:")
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                print(f"    📄 {rel_path}")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def main():
    """运行所有仓库下载示例"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 仓库下载示例")
    print()

    # 运行示例
    download_full_repository()
    download_encrypted_repository()
    download_with_filters()
    download_with_ignore_patterns()

    print("=" * 80)
    print("✨ 仓库下载示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用 snapshot_download() 下载整个仓库")
    print("  - 使用 allow_patterns 只下载特定类型的文件")
    print("  - 使用 ignore_patterns 排除不需要的文件")
    print("  - 加密仓库会自动检测并解密加密的文件")
    print("  - 设置 verbose=True 查看详细下载进度")
    print()


if __name__ == "__main__":
    main()

