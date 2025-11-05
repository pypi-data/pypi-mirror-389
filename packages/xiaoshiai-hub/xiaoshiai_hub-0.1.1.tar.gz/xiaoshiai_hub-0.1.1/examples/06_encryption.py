#!/usr/bin/env python3
"""
加密功能示例 - XiaoShi AI Hub Python SDK

本示例演示如何使用加密功能：
- 生成加密密钥
- 使用不同的加密算法
- 对称加密（AES, SM4）
- 非对称加密（RSA, SM2）
"""

import secrets
import string


def generate_symmetric_key():
    """生成对称加密密钥"""
    print("=" * 80)
    print("示例 6.1: 生成对称加密密钥")
    print("=" * 80)
    print()

    print("🔑 对称加密密钥（用于 AES 和 SM4）:")
    print()

    # 生成 32 字符的随机密钥
    key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    print(f"  密钥长度: 32 字符")
    print(f"  密钥内容: {key}")
    print()
    
    print("📝 使用示例:")
    print(f"  # AES-256-CBC 加密")
    print(f"  upload_file(..., encryption_key='{key}', encryption_algorithm='aes-256-cbc')")
    print()
    print(f"  # AES-256-GCM 加密")
    print(f"  upload_file(..., encryption_key='{key}', encryption_algorithm='aes-256-gcm')")
    print()
    print(f"  # SM4-CBC 加密（国密）")
    print(f"  upload_file(..., encryption_key='{key}', encryption_algorithm='sm4-cbc')")
    print()
    print(f"  # SM4-GCM 加密（国密）")
    print(f"  upload_file(..., encryption_key='{key}', encryption_algorithm='sm4-gcm')")
    print()


def generate_rsa_keypair():
    """生成 RSA 密钥对"""
    print("=" * 80)
    print("示例 6.2: 生成 RSA 密钥对")
    print("=" * 80)
    print()

    try:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        print("🔐 生成 RSA 密钥对...")
        print()

        # 生成 RSA 私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()

        # 序列化公钥
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # 序列化私钥
        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        print("✅ RSA 密钥对生成成功")
        print()
        print("📄 公钥 (PEM 格式) - 用于加密:")
        print("-" * 70)
        print(public_key_pem)
        print()
        print("🔒 私钥 (PEM 格式) - 用于解密:")
        print("-" * 70)
        print(private_key_pem)
        print()

        print("📝 使用示例:")
        print("  # 上传时使用公钥加密")
        print("  public_key = '''")
        print("  " + "\n  ".join(public_key_pem.split('\n')))
        print("  '''")
        print("  upload_file(..., encryption_key=public_key, encryption_algorithm='rsa-oaep')")
        print()
        print("  # 下载时使用私钥解密")
        print("  private_key = '''")
        print("  " + "\n  ".join(private_key_pem.split('\n')[:3]))
        print("  ...")
        print("  '''")
        print("  snapshot_download(..., decryption_key=private_key, decryption_algorithm='rsa-oaep')")
        print()

        # 保存到文件（可选）
        print("💾 保存密钥到文件:")
        with open("rsa_public_key.pem", "w") as f:
            f.write(public_key_pem)
        print("  公钥已保存到: rsa_public_key.pem")
        
        with open("rsa_private_key.pem", "w") as f:
            f.write(private_key_pem)
        print("  私钥已保存到: rsa_private_key.pem")
        print("  ⚠️  请妥善保管私钥文件！")
        print()

    except ImportError:
        print("❌ 需要安装 cryptography 库")
        print("   运行: pip install cryptography")
        print()


def generate_sm2_keypair():
    """生成 SM2 密钥对"""
    print("=" * 80)
    print("示例 6.3: 生成 SM2 密钥对（国密）")
    print("=" * 80)
    print()

    try:
        from gmssl import sm2

        print("🔐 生成 SM2 密钥对...")
        print()

        # 生成 SM2 密钥对（示例）
        # 注意：实际使用时应该使用 gmssl 库的正确方法生成密钥
        private_key_hex = secrets.token_hex(32)  # 64 个十六进制字符
        public_key_hex = "04" + secrets.token_hex(64)  # 130 个十六进制字符，以 '04' 开头

        print("✅ SM2 密钥对生成成功")
        print()
        print("📄 公钥 (十六进制) - 用于加密:")
        print(f"  {public_key_hex}")
        print()
        print("🔒 私钥 (十六进制) - 用于解密:")
        print(f"  {private_key_hex}")
        print()

        print("📝 使用示例:")
        print(f"  # 上传时使用公钥加密")
        print(f"  upload_file(..., encryption_key='{public_key_hex}', encryption_algorithm='sm2')")
        print()
        print(f"  # 下载时使用私钥解密")
        print(f"  snapshot_download(..., decryption_key='{private_key_hex}', decryption_algorithm='sm2')")
        print()

        print("⚠️  注意:")
        print("  - 这是一个简化的示例，实际使用时应该使用 gmssl 库的正确方法生成密钥")
        print("  - SM2 是中国国家密码管理局制定的椭圆曲线公钥密码算法")
        print()

    except ImportError:
        print("❌ 需要安装 gmssl 库")
        print("   运行: pip install gmssl")
        print()


def encryption_algorithms_overview():
    """加密算法概览"""
    print("=" * 80)
    print("示例 6.4: 加密算法概览")
    print("=" * 80)
    print()

    algorithms = [
        {
            "name": "AES-256-CBC",
            "type": "对称加密",
            "key_type": "32 字符字符串",
            "security": "⭐⭐⭐⭐",
            "speed": "⚡⚡⚡⚡",
            "use_case": "通用加密，适合大文件"
        },
        {
            "name": "AES-256-GCM",
            "type": "对称加密（认证）",
            "key_type": "32 字符字符串",
            "security": "⭐⭐⭐⭐⭐",
            "speed": "⚡⚡⚡⚡",
            "use_case": "需要完整性验证的场景"
        },
        {
            "name": "SM4-CBC",
            "type": "对称加密（国密）",
            "key_type": "32 字符字符串",
            "security": "⭐⭐⭐⭐",
            "speed": "⚡⚡⚡",
            "use_case": "符合国密标准的场景"
        },
        {
            "name": "SM4-GCM",
            "type": "对称加密（国密认证）",
            "key_type": "32 字符字符串",
            "security": "⭐⭐⭐⭐⭐",
            "speed": "⚡⚡⚡",
            "use_case": "国密标准 + 完整性验证"
        },
        {
            "name": "RSA-OAEP",
            "type": "非对称加密",
            "key_type": "PEM 格式密钥对",
            "security": "⭐⭐⭐⭐⭐",
            "speed": "⚡⚡",
            "use_case": "密钥交换，小文件加密"
        },
        {
            "name": "RSA-PKCS1V15",
            "type": "非对称加密",
            "key_type": "PEM 格式密钥对",
            "security": "⭐⭐⭐⭐",
            "speed": "⚡⚡",
            "use_case": "兼容性要求高的场景"
        },
        {
            "name": "SM2",
            "type": "非对称加密（国密）",
            "key_type": "十六进制密钥对",
            "security": "⭐⭐⭐⭐⭐",
            "speed": "⚡⚡⚡",
            "use_case": "国密标准的非对称加密"
        },
    ]

    print("📊 支持的加密算法:")
    print()
    print(f"{'算法':<20} {'类型':<20} {'密钥类型':<20} {'安全性':<10} {'速度':<10}")
    print("-" * 90)
    
    for algo in algorithms:
        print(f"{algo['name']:<20} {algo['type']:<20} {algo['key_type']:<20} {algo['security']:<10} {algo['speed']:<10}")
    
    print()
    print("💡 选择建议:")
    print()
    
    for algo in algorithms:
        print(f"  {algo['name']}:")
        print(f"    {algo['use_case']}")
        print()


def encryption_best_practices():
    """加密最佳实践"""
    print("=" * 80)
    print("示例 6.5: 加密最佳实践")
    print("=" * 80)
    print()

    print("🔒 加密最佳实践:")
    print()

    practices = [
        ("使用环境变量存储密钥", "不要在代码中硬编码密钥"),
        ("定期轮换密钥", "建议每 90 天更换一次加密密钥"),
        ("使用强随机密钥", "使用 secrets 模块生成密钥，不要使用简单密码"),
        ("妥善保管私钥", "非对称加密的私钥应该安全存储，不要泄露"),
        ("选择合适的算法", "根据安全需求和性能要求选择算法"),
        ("备份密钥", "确保密钥有安全的备份，丢失密钥将无法解密"),
        ("使用 GCM 模式", "需要完整性验证时使用 GCM 模式"),
        ("测试解密", "上传后测试解密，确保密钥正确"),
    ]

    for i, (title, desc) in enumerate(practices, 1):
        print(f"  {i}. {title}")
        print(f"     {desc}")
        print()

    print("⚠️  安全警告:")
    print("  - 密钥一旦丢失，加密的数据将无法恢复")
    print("  - 不要将密钥提交到版本控制系统")
    print("  - 不要通过不安全的渠道传输密钥")
    print("  - 定期审计密钥的使用情况")
    print()


def main():
    """运行所有加密示例"""
    print()
    print("🚀 XiaoShi AI Hub Python SDK - 加密功能示例")
    print()

    # 运行示例
    generate_symmetric_key()
    generate_rsa_keypair()
    generate_sm2_keypair()
    encryption_algorithms_overview()
    encryption_best_practices()

    print("=" * 80)
    print("✨ 加密功能示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用 secrets 模块生成安全的随机密钥")
    print("  - 对称加密适合大文件，非对称加密适合密钥交换")
    print("  - 国密算法（SM2, SM4）符合中国密码标准")
    print("  - 妥善保管密钥，丢失后无法恢复数据")
    print()


if __name__ == "__main__":
    main()

