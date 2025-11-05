#!/usr/bin/env python3
"""
上传文件示例 - XiaoShi AI Hub Python SDK

本示例演示如何上传文件：
- 上传普通文件
- 上传加密文件
- 上传文件对象
- 自定义提交信息

注意: 需要安装上传功能依赖
pip install xiaoshiai-hub[upload]
"""

import os
import tempfile
from io import BytesIO

try:
    from xiaoshiai_hub import upload_file
    from xiaoshiai_hub.encryption import EncryptionAlgorithm
except ImportError:
    print("❌ 上传功能不可用")
    print("请安装上传依赖: pip install xiaoshiai-hub[upload]")
    exit(1)


def upload_normal_file():
    """上传普通文件"""
    print("=" * 80)
    print("示例 4.1: 上传普通文件")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 创建测试文件
    test_file = "./temp_uploads/test_file.txt"
    os.makedirs("./temp_uploads", exist_ok=True)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 测试文件\n\n")
        f.write("这是一个由示例代码创建的测试文件。\n")
        f.write(f"创建时间: {os.popen('date').read().strip()}\n")
        f.write("\n")
        f.write("## 内容\n")
        f.write("这是一些测试内容。\n")

    print(f"📤 上传文件:")
    print(f"  本地文件: {test_file}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  目标路径: examples/test_file.txt")
    print()

    try:
        commit_hash = upload_file(
            path_or_fileobj=test_file,
            path_in_repo="examples/test_file.txt",
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload test file from example",
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件上传成功!")
        print(f"  提交哈希: {commit_hash}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)
    print()


def upload_encrypted_file():
    """上传加密文件"""
    print("=" * 80)
    print("示例 4.2: 上传加密文件")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"

    # 从环境变量读取认证信息和加密密钥
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB")

    # 创建测试文件
    test_file = "./temp_uploads/encrypted_file.txt"
    os.makedirs("./temp_uploads", exist_ok=True)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# 加密测试文件\n\n")
        f.write("这是一个将被加密上传的文件。\n")
        f.write("包含敏感信息，需要加密保护。\n")
        f.write(f"创建时间: {os.popen('date').read().strip()}\n")

    print(f"📤 上传加密文件:")
    print(f"  本地文件: {test_file}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  目标路径: examples/encrypted_file.txt")
    print(f"  加密算法: AES-256-CBC")
    print()

    try:
        commit_hash = upload_file(
            path_or_fileobj=test_file,
            path_in_repo="examples/encrypted_file.txt",
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload encrypted test file from example",
            username=USERNAME,
            password=PASSWORD,
            encryption_key=ENCRYPTION_KEY,
            encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
        )
        print(f"✅ 文件已加密并上传成功!")
        print(f"  提交哈希: {commit_hash}")
        print(f"  💡 使用相同的密钥和算法才能解密下载")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)
    print()


def upload_file_object():
    """上传文件对象"""
    print("=" * 80)
    print("示例 4.3: 上传文件对象")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 创建文件对象
    file_content = b"""# File Object Upload Test

This file was uploaded from a BytesIO object.
No temporary file was created on disk.

## Benefits
- Memory efficient for small files
- No disk I/O overhead
- Useful for dynamically generated content
"""

    file_obj = BytesIO(file_content)

    print(f"📤 上传文件对象:")
    print(f"  内容大小: {len(file_content)} bytes")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  目标路径: examples/file_object.md")
    print()

    try:
        commit_hash = upload_file(
            path_or_fileobj=file_obj,
            path_in_repo="examples/file_object.md",
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload file from BytesIO object",
            commit_description="Demonstrates uploading from memory without disk I/O",
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件对象上传成功!")
        print(f"  提交哈希: {commit_hash}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    print()


def upload_with_custom_commit():
    """使用自定义提交信息上传"""
    print("=" * 80)
    print("示例 4.4: 自定义提交信息")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 创建测试文件
    test_file = "./temp_uploads/custom_commit.txt"
    os.makedirs("./temp_uploads", exist_ok=True)

    with open(test_file, "w", encoding="utf-8") as f:
        f.write("# Custom Commit Message Example\n\n")
        f.write("This file demonstrates custom commit messages.\n")

    print(f"📤 上传文件（自定义提交信息）:")
    print(f"  本地文件: {test_file}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  目标路径: examples/custom_commit.txt")
    print()

    try:
        commit_hash = upload_file(
            path_or_fileobj=test_file,
            path_in_repo="examples/custom_commit.txt",
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="feat: Add custom commit example",
            commit_description="""
This commit demonstrates how to use custom commit messages.

Features:
- Custom commit message
- Detailed commit description
- Follows conventional commits format

Related: #123
            """.strip(),
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件上传成功!")
        print(f"  提交哈希: {commit_hash}")
        print(f"  提交信息: feat: Add custom commit example")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)
    print()


def main():
    """运行所有上传示例"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 文件上传示例")
    print()

    # 运行示例
    upload_normal_file()
    upload_encrypted_file()
    upload_file_object()
    upload_with_custom_commit()

    print("=" * 80)
    print("✨ 文件上传示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用 upload_file() 上传单个文件")
    print("  - 支持上传文件路径或文件对象（BytesIO）")
    print("  - 使用 encryption_key 和 encryption_algorithm 加密上传")
    print("  - 支持自定义提交信息和描述")
    print("  - 使用环境变量 ENCRYPTION_KEY 设置加密密钥")
    print()


if __name__ == "__main__":
    main()

