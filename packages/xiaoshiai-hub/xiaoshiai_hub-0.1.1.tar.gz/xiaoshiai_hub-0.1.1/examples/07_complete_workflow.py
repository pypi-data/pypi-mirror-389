#!/usr/bin/env python3
"""
完整工作流示例 - XiaoShi AI Hub Python SDK

本示例演示一个完整的工作流程：
1. 创建客户端并获取仓库信息
2. 生成加密密钥
3. 上传加密文件夹
4. 下载并解密文件
5. 验证文件完整性

这是一个端到端的示例，展示了 SDK 的主要功能。
"""

import os
import shutil
import hashlib
import secrets
import string

try:
    from xiaoshiai_hub import HubClient, upload_folder, snapshot_download
    from xiaoshiai_hub.encryption import EncryptionAlgorithm
    UPLOAD_AVAILABLE = True
except ImportError:
    from xiaoshiai_hub import HubClient, snapshot_download
    UPLOAD_AVAILABLE = False
    print("⚠️  上传功能不可用，部分示例将跳过")
    print("   运行: pip install xiaoshiai-hub[upload]")


def calculate_file_hash(file_path):
    """计算文件的 SHA256 哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def step1_setup():
    """步骤 1: 设置和配置"""
    print("=" * 80)
    print("步骤 1: 设置和配置")
    print("=" * 80)
    print()

    # 配置信息
    config = {
        "repo_id": "system/encryption",
        "repo_type": "models",
        "username": os.environ.get("MOHA_USERNAME", "your-username"),
        "password": os.environ.get("MOHA_PASSWORD", "your-password"),
        "encryption_key": None,
    }

    print("📋 配置信息:")
    print(f"  仓库 ID: {config['repo_id']}")
    print(f"  仓库类型: {config['repo_type']}")
    print(f"  用户名: {config['username']}")
    print()

    # 创建客户端
    print("🔧 创建 HubClient...")
    client = HubClient(
        username=config["username"],
        password=config["password"],
    )
    print("✅ 客户端创建成功")
    print()

    # 获取仓库信息
    print("📦 获取仓库信息...")
    org, repo = config["repo_id"].split('/')
    try:
        repo_info = client.get_repository_info(org, config["repo_type"], repo)
        print(f"  名称: {repo_info.name}")
        print(f"  组织: {repo_info.organization}")
        print(f"  类型: {repo_info.type}")
        print("✅ 仓库信息获取成功")
    except Exception as e:
        print(f"❌ 获取仓库信息失败: {e}")
        return None
    print()

    return config


def step2_generate_key():
    """步骤 2: 生成加密密钥"""
    print("=" * 80)
    print("步骤 2: 生成加密密钥")
    print("=" * 80)
    print()

    print("🔑 生成 AES-256 加密密钥...")
    encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    print(f"  密钥: {encryption_key}")
    print(f"  长度: {len(encryption_key)} 字符")
    print("✅ 密钥生成成功")
    print()

    print("💾 保存密钥到环境变量（推荐）:")
    print(f"  export ENCRYPTION_KEY='{encryption_key}'")
    print()

    return encryption_key


def step3_prepare_data():
    """步骤 3: 准备测试数据"""
    print("=" * 80)
    print("步骤 3: 准备测试数据")
    print("=" * 80)
    print()

    folder_path = "./workflow_test_data"
    
    # 清理旧数据
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    os.makedirs(folder_path, exist_ok=True)

    print("📁 创建测试文件...")

    # 创建 README
    readme_path = f"{folder_path}/README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# 工作流测试项目\n\n")
        f.write("这是一个完整工作流的测试项目。\n\n")
        f.write("## 文件说明\n")
        f.write("- config.json: 配置文件（不加密）\n")
        f.write("- data/: 数据目录（加密）\n")

    # 创建配置文件
    config_path = f"{folder_path}/config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write('{\n')
        f.write('  "name": "workflow-test",\n')
        f.write('  "version": "1.0.0",\n')
        f.write('  "encrypted": true\n')
        f.write('}\n')

    # 创建数据目录
    os.makedirs(f"{folder_path}/data", exist_ok=True)
    
    data_path = f"{folder_path}/data/sensitive.txt"
    with open(data_path, "w", encoding="utf-8") as f:
        f.write("这是敏感数据，需要加密保护。\n")
        f.write("包含重要信息。\n")

    print(f"  ✅ README.md")
    print(f"  ✅ config.json")
    print(f"  ✅ data/sensitive.txt")
    print()

    # 计算文件哈希
    hashes = {}
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, folder_path)
            hashes[rel_path] = calculate_file_hash(file_path)

    print("🔍 文件哈希值:")
    for file, hash_value in hashes.items():
        print(f"  {file}: {hash_value[:16]}...")
    print()

    return folder_path, hashes


def step4_upload(config, encryption_key, folder_path):
    """步骤 4: 上传加密数据"""
    if not UPLOAD_AVAILABLE:
        print("=" * 80)
        print("步骤 4: 上传加密数据 (跳过)")
        print("=" * 80)
        print()
        print("⚠️  上传功能不可用，跳过此步骤")
        print()
        return None

    print("=" * 80)
    print("步骤 4: 上传加密数据")
    print("=" * 80)
    print()

    print("📤 上传文件夹（部分加密）...")
    print(f"  本地路径: {folder_path}")
    print(f"  目标仓库: {config['repo_id']}")
    print(f"  加密算法: AES-256-CBC")
    print(f"  加密排除: README.md, *.json")
    print()

    try:
        commit_hash = upload_folder(
            folder_path=folder_path,
            repo_id=config["repo_id"],
            repo_type=config["repo_type"],
            commit_message="Complete workflow test upload",
            commit_description="测试完整工作流：部分文件加密上传",
            username=config["username"],
            password=config["password"],
            encryption_key=encryption_key,
            encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
            encryption_exclude=["README.md", "*.json"],
        )
        print(f"✅ 上传成功!")
        print(f"  提交哈希: {commit_hash}")
        print()
        return commit_hash
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return None


def step5_download(config, encryption_key):
    """步骤 5: 下载并解密数据"""
    print("=" * 80)
    print("步骤 5: 下载并解密数据")
    print("=" * 80)
    print()

    download_path = "./workflow_downloaded_data"
    
    # 清理旧数据
    if os.path.exists(download_path):
        shutil.rmtree(download_path)

    print("📥 下载仓库...")
    print(f"  仓库: {config['repo_id']}")
    print(f"  保存到: {download_path}")
    print(f"  解密算法: AES-256-CBC")
    print()

    try:
        repo_path = snapshot_download(
            repo_id=config["repo_id"],
            repo_type=config["repo_type"],
            local_dir=download_path,
            username=config["username"],
            password=config["password"],
            decryption_key=encryption_key,
            decryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
            verbose=True,
        )
        print()
        print(f"✅ 下载成功!")
        print(f"  路径: {repo_path}")
        print()
        return repo_path
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        return None


def step6_verify(original_hashes, download_path):
    """步骤 6: 验证文件完整性"""
    print("=" * 80)
    print("步骤 6: 验证文件完整性")
    print("=" * 80)
    print()

    if not download_path or not os.path.exists(download_path):
        print("⚠️  下载路径不存在，跳过验证")
        print()
        return

    print("🔍 验证文件哈希值...")
    print()

    all_match = True
    for file, original_hash in original_hashes.items():
        file_path = os.path.join(download_path, file)
        if os.path.exists(file_path):
            current_hash = calculate_file_hash(file_path)
            match = current_hash == original_hash
            status = "✅" if match else "❌"
            print(f"  {status} {file}")
            if not match:
                print(f"     原始: {original_hash[:16]}...")
                print(f"     当前: {current_hash[:16]}...")
                all_match = False
        else:
            print(f"  ❌ {file} (文件不存在)")
            all_match = False

    print()
    if all_match:
        print("✅ 所有文件验证通过！")
    else:
        print("❌ 部分文件验证失败")
    print()


def cleanup():
    """清理临时文件"""
    print("=" * 80)
    print("清理临时文件")
    print("=" * 80)
    print()

    folders = ["./workflow_test_data", "./workflow_downloaded_data"]
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  🗑️  已删除: {folder}")

    print()


def main():
    """运行完整工作流"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 完整工作流示例")
    print()
    print("本示例演示一个端到端的工作流程：")
    print("  1. 设置和配置")
    print("  2. 生成加密密钥")
    print("  3. 准备测试数据")
    print("  4. 上传加密数据")
    print("  5. 下载并解密数据")
    print("  6. 验证文件完整性")
    print()

    try:
        # 步骤 1: 设置
        config = step1_setup()
        if not config:
            return

        # 步骤 2: 生成密钥
        encryption_key = step2_generate_key()
        config["encryption_key"] = encryption_key

        # 步骤 3: 准备数据
        folder_path, original_hashes = step3_prepare_data()

        # 步骤 4: 上传
        commit_hash = step4_upload(config, encryption_key, folder_path)

        # 步骤 5: 下载
        download_path = step5_download(config, encryption_key)

        # 步骤 6: 验证
        step6_verify(original_hashes, download_path)

        # 清理
        cleanup()

        print("=" * 80)
        print("✨ 完整工作流示例完成！")
        print("=" * 80)
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  工作流被用户中断")
        cleanup()
    except Exception as e:
        print(f"\n❌ 工作流失败: {e}")
        import traceback
        traceback.print_exc()
        cleanup()


if __name__ == "__main__":
    main()

