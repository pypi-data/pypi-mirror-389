#!/usr/bin/env python3
"""
下载单个文件示例 - XiaoShi AI Hub Python SDK

本示例演示如何下载单个文件：
- 下载普通文件
- 下载加密文件（需要解密密钥）
- 指定本地保存路径
"""

from xiaoshiai_hub import moha_hub_download
from xiaoshiai_hub.encryption import EncryptionAlgorithm
import os


def download_normal_file():
    """下载普通文件"""
    print("=" * 80)
    print("示例 2.1: 下载普通文件")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FILENAME = "config.yaml"
    LOCAL_DIR = "./downloads/normal_file"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    print(f"📥 下载文件:")
    print(f"  仓库: {REPO_ID}")
    print(f"  文件: {FILENAME}")
    print(f"  保存到: {LOCAL_DIR}")
    print()

    try:
        file_path = moha_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件已下载到: {file_path}")
        
        # 显示文件信息
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  文件大小: {file_size:,} bytes")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def download_encrypted_file():
    """下载加密文件"""
    print("=" * 80)
    print("示例 2.2: 下载加密文件")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FILENAME = "data.txt"
    LOCAL_DIR = "./downloads/encrypted_file"

    # 从环境变量读取认证信息和解密密钥
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")
    DECRYPTION_KEY = os.environ.get("DECRYPTION_KEY", "S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB")

    print(f"📥 下载加密文件:")
    print(f"  仓库: {REPO_ID}")
    print(f"  文件: {FILENAME}")
    print(f"  保存到: {LOCAL_DIR}")
    print(f"  解密算法: AES-256-CBC")
    print()

    try:
        file_path = moha_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            username=USERNAME,
            password=PASSWORD,
            decryption_key=DECRYPTION_KEY,
            decryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
        )
        print(f"✅ 文件已下载并解密到: {file_path}")
        
        # 显示文件信息
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  文件大小: {file_size:,} bytes")
            
            # 显示文件内容（如果是文本文件）
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(200)  # 只读取前200个字符
                    print(f"  文件内容预览:")
                    for line in content.split('\n')[:5]:
                        print(f"    {line}")
                    if len(content) >= 200:
                        print("    ...")
            except:
                pass
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def download_with_custom_path():
    """下载文件到自定义路径"""
    print("=" * 80)
    print("示例 2.3: 下载到自定义路径")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FILENAME = "README.md"
    LOCAL_DIR = "./downloads/custom_path"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    print(f"📥 下载文件到自定义路径:")
    print(f"  仓库: {REPO_ID}")
    print(f"  文件: {FILENAME}")
    print(f"  保存到: {LOCAL_DIR}")
    print()

    try:
        # 确保目录存在
        os.makedirs(LOCAL_DIR, exist_ok=True)
        
        file_path = moha_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            repo_type=REPO_TYPE,
            local_dir=LOCAL_DIR,
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件已下载到: {file_path}")
        
        # 显示文件信息
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"  文件大小: {file_size:,} bytes")
            print(f"  绝对路径: {os.path.abspath(file_path)}")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def main():
    """运行所有下载示例"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 文件下载示例")
    print()

    # 运行示例
    download_normal_file()
    download_encrypted_file()
    download_with_custom_path()

    print("=" * 80)
    print("✨ 文件下载示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用 moha_hub_download() 下载单个文件")
    print("  - 加密文件需要提供 decryption_key 和 decryption_algorithm")
    print("  - 支持的加密算法: AES-256-CBC, AES-256-GCM, SM4-CBC, SM4-GCM, RSA-OAEP, RSA-PKCS1V15, SM2")
    print("  - 使用环境变量 DECRYPTION_KEY 设置解密密钥")
    print()


if __name__ == "__main__":
    main()

