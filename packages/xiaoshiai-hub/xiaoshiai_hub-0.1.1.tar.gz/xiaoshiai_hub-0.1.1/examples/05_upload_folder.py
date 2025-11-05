#!/usr/bin/env python3
"""
上传文件夹示例 - XiaoShi AI Hub Python SDK

本示例演示如何上传文件夹：
- 上传整个文件夹
- 上传加密文件夹
- 使用忽略模式排除文件
- 部分文件加密上传

注意: 需要安装上传功能依赖
pip install xiaoshiai-hub[upload]
"""

import os
import shutil

try:
    from xiaoshiai_hub import upload_folder
    from xiaoshiai_hub.encryption import EncryptionAlgorithm
except ImportError:
    print("❌ 上传功能不可用")
    print("请安装上传依赖: pip install xiaoshiai-hub[upload]")
    exit(1)


def create_test_folder(folder_path):
    """创建测试文件夹"""
    # 清理旧文件夹
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    os.makedirs(folder_path, exist_ok=True)

    # 创建 README
    with open(f"{folder_path}/README.md", "w", encoding="utf-8") as f:
        f.write("# 测试项目\n\n")
        f.write("这是一个由示例代码创建的测试项目。\n\n")
        f.write("## 结构\n")
        f.write("- config.yaml: 配置文件\n")
        f.write("- data/: 数据目录\n")
        f.write("- scripts/: 脚本目录\n")

    # 创建配置文件
    with open(f"{folder_path}/config.yaml", "w", encoding="utf-8") as f:
        f.write("# 项目配置\n")
        f.write("name: test-project\n")
        f.write("version: 1.0.0\n")
        f.write("author: Example User\n")

    # 创建数据目录
    os.makedirs(f"{folder_path}/data", exist_ok=True)
    with open(f"{folder_path}/data/sample.txt", "w", encoding="utf-8") as f:
        f.write("这是一些示例数据\n")
        f.write("包含多行内容\n")

    with open(f"{folder_path}/data/numbers.csv", "w", encoding="utf-8") as f:
        f.write("id,value\n")
        f.write("1,100\n")
        f.write("2,200\n")
        f.write("3,300\n")

    # 创建脚本目录
    os.makedirs(f"{folder_path}/scripts", exist_ok=True)
    with open(f"{folder_path}/scripts/process.py", "w", encoding="utf-8") as f:
        f.write("#!/usr/bin/env python3\n")
        f.write('"""数据处理脚本"""\n\n')
        f.write("def process_data():\n")
        f.write('    print("Processing data...")\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write("    process_data()\n")

    # 创建临时文件（将被忽略）
    with open(f"{folder_path}/temp.log", "w", encoding="utf-8") as f:
        f.write("这是一个临时日志文件\n")

    print(f"✅ 测试文件夹已创建: {folder_path}")


def upload_normal_folder():
    """上传普通文件夹"""
    print("=" * 80)
    print("示例 5.1: 上传普通文件夹")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FOLDER_PATH = "./temp_uploads/normal_folder"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 创建测试文件夹
    create_test_folder(FOLDER_PATH)
    print()

    print(f"📤 上传文件夹:")
    print(f"  本地路径: {FOLDER_PATH}")
    print(f"  目标仓库: {REPO_ID}")
    print()

    try:
        commit_hash = upload_folder(
            folder_path=FOLDER_PATH,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload test folder from example",
            commit_description="包含示例配置、数据和脚本",
            username=USERNAME,
            password=PASSWORD,
        )
        print(f"✅ 文件夹上传成功!")
        print(f"  提交哈希: {commit_hash}")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件夹
        if os.path.exists(FOLDER_PATH):
            shutil.rmtree(FOLDER_PATH)
    print()


def upload_encrypted_folder():
    """上传加密文件夹"""
    print("=" * 80)
    print("示例 5.2: 上传加密文件夹")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FOLDER_PATH = "./temp_uploads/encrypted_folder"

    # 从环境变量读取认证信息和加密密钥
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB")

    # 创建测试文件夹
    create_test_folder(FOLDER_PATH)
    print()

    print(f"📤 上传加密文件夹:")
    print(f"  本地路径: {FOLDER_PATH}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  加密算法: AES-256-CBC")
    print()

    try:
        commit_hash = upload_folder(
            folder_path=FOLDER_PATH,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload encrypted folder from example",
            commit_description="所有文件都已加密",
            username=USERNAME,
            password=PASSWORD,
            encryption_key=ENCRYPTION_KEY,
            encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
        )
        print(f"✅ 文件夹已加密并上传成功!")
        print(f"  提交哈希: {commit_hash}")
        print(f"  💡 使用相同的密钥和算法才能解密下载")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件夹
        if os.path.exists(FOLDER_PATH):
            shutil.rmtree(FOLDER_PATH)
    print()


def upload_with_ignore_patterns():
    """使用忽略模式上传"""
    print("=" * 80)
    print("示例 5.3: 使用忽略模式上传")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FOLDER_PATH = "./temp_uploads/ignore_patterns_folder"

    # 从环境变量读取认证信息
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 忽略模式
    IGNORE_PATTERNS = [
        "*.log",      # 忽略日志文件
        "temp.*",     # 忽略临时文件
        "scripts/*",  # 忽略脚本目录
    ]

    # 创建测试文件夹
    create_test_folder(FOLDER_PATH)
    print()

    print(f"📤 上传文件夹（使用忽略模式）:")
    print(f"  本地路径: {FOLDER_PATH}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  忽略模式: {IGNORE_PATTERNS}")
    print()

    try:
        commit_hash = upload_folder(
            folder_path=FOLDER_PATH,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload folder with ignore patterns",
            commit_description="排除了日志文件、临时文件和脚本目录",
            username=USERNAME,
            password=PASSWORD,
            ignore_patterns=IGNORE_PATTERNS,
        )
        print(f"✅ 文件夹上传成功（已排除匹配的文件）!")
        print(f"  提交哈希: {commit_hash}")
        print(f"  💡 被忽略的文件不会上传")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件夹
        if os.path.exists(FOLDER_PATH):
            shutil.rmtree(FOLDER_PATH)
    print()


def upload_with_partial_encryption():
    """部分文件加密上传"""
    print("=" * 80)
    print("示例 5.4: 部分文件加密上传")
    print("=" * 80)
    print()

    # 配置信息
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    FOLDER_PATH = "./temp_uploads/partial_encryption_folder"

    # 从环境变量读取认证信息和加密密钥
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB")

    # 加密排除模式（这些文件不加密）
    ENCRYPTION_EXCLUDE = [
        "README.md",   # README 不加密
        "*.yaml",      # 配置文件不加密
    ]

    # 创建测试文件夹
    create_test_folder(FOLDER_PATH)
    print()

    print(f"📤 上传文件夹（部分加密）:")
    print(f"  本地路径: {FOLDER_PATH}")
    print(f"  目标仓库: {REPO_ID}")
    print(f"  加密算法: AES-256-CBC")
    print(f"  加密排除: {ENCRYPTION_EXCLUDE}")
    print()

    try:
        commit_hash = upload_folder(
            folder_path=FOLDER_PATH,
            repo_id=REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Upload folder with partial encryption",
            commit_description="数据文件加密，配置文件和 README 不加密",
            username=USERNAME,
            password=PASSWORD,
            encryption_key=ENCRYPTION_KEY,
            encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
            encryption_exclude=ENCRYPTION_EXCLUDE,
        )
        print(f"✅ 文件夹上传成功（部分文件已加密）!")
        print(f"  提交哈希: {commit_hash}")
        print(f"  💡 README 和配置文件未加密，可直接查看")
        print(f"  💡 数据文件已加密，需要密钥才能访问")
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理临时文件夹
        if os.path.exists(FOLDER_PATH):
            shutil.rmtree(FOLDER_PATH)
    print()


def main():
    """运行所有文件夹上传示例"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 文件夹上传示例")
    print()

    # 运行示例
    upload_normal_folder()
    upload_encrypted_folder()
    upload_with_ignore_patterns()
    upload_with_partial_encryption()

    print("=" * 80)
    print("✨ 文件夹上传示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用 upload_folder() 上传整个文件夹")
    print("  - 使用 ignore_patterns 排除不需要上传的文件")
    print("  - 使用 encryption_key 和 encryption_algorithm 加密上传")
    print("  - 使用 encryption_exclude 指定不加密的文件")
    print("  - 支持嵌套目录结构")
    print()


if __name__ == "__main__":
    main()

