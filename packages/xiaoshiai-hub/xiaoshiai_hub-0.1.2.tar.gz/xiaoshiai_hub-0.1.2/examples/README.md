# XiaoShi AI Hub Python SDK - 示例代码

本目录包含 XiaoShi AI Hub Python SDK 的完整示例代码，展示了 SDK 的各种功能和使用场景。

## 📋 目录

- [快速开始](#快速开始)
- [示例列表](#示例列表)
- [环境配置](#环境配置)
- [运行示例](#运行示例)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 安装 SDK

```bash
# 基础安装（仅下载功能）
pip install xiaoshiai-hub

# 完整安装（包含上传功能）
pip install xiaoshiai-hub[upload]
```

### 2. 配置环境变量

```bash
# 必需的环境变量
export MOHA_ENDPOINT="https://your-hub-endpoint.com"
export MOHA_USERNAME="your-username"
export MOHA_PASSWORD="your-password"

# 可选的环境变量（用于加密/解密）
export ENCRYPTION_KEY="your-32-character-encryption-key"
export DECRYPTION_KEY="your-32-character-decryption-key"
```

### 3. 运行示例

```bash
# 运行基础使用示例
python examples/01_basic_usage.py

# 运行完整工作流示例
python examples/07_complete_workflow.py
```

## 📚 示例列表

### 01_basic_usage.py - 基础使用

**功能**: 演示 HubClient API 的基本使用

**内容**:
- 创建客户端
- 获取仓库信息
- 列出分支和标签
- 浏览仓库内容

**运行**:
```bash
python examples/01_basic_usage.py
```

**前置条件**:
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量

---

### 02_download_file.py - 下载文件

**功能**: 演示如何下载单个文件

**内容**:
- 下载普通文件
- 下载加密文件并解密
- 下载到自定义路径

**运行**:
```bash
python examples/02_download_file.py
```

**前置条件**:
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量
- 下载加密文件需要设置 `DECRYPTION_KEY` 环境变量

---

### 03_download_repository.py - 下载仓库

**功能**: 演示如何下载整个仓库

**内容**:
- 下载完整仓库
- 下载加密仓库（自动解密）
- 使用过滤器下载部分文件
- 排除特定文件或目录

**运行**:
```bash
python examples/03_download_repository.py
```

**前置条件**:
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量
- 下载加密仓库需要设置 `DECRYPTION_KEY` 环境变量

---

### 04_upload_file.py - 上传文件

**功能**: 演示如何上传单个文件

**内容**:
- 上传普通文件
- 上传加密文件
- 上传文件对象（BytesIO）
- 自定义提交信息

**运行**:
```bash
python examples/04_upload_file.py
```

**前置条件**:
- 安装上传依赖: `pip install xiaoshiai-hub[upload]`
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量
- 上传加密文件需要设置 `ENCRYPTION_KEY` 环境变量

---

### 05_upload_folder.py - 上传文件夹

**功能**: 演示如何上传整个文件夹

**内容**:
- 上传整个文件夹
- 上传加密文件夹
- 使用忽略模式排除文件
- 部分文件加密上传

**运行**:
```bash
python examples/05_upload_folder.py
```

**前置条件**:
- 安装上传依赖: `pip install xiaoshiai-hub[upload]`
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量
- 上传加密文件夹需要设置 `ENCRYPTION_KEY` 环境变量

---

### 06_encryption.py - 加密功能

**功能**: 演示加密功能和密钥生成

**内容**:
- 生成对称加密密钥（AES, SM4）
- 生成 RSA 密钥对
- 生成 SM2 密钥对（国密）
- 加密算法概览
- 加密最佳实践

**运行**:
```bash
python examples/06_encryption.py
```

**前置条件**:
- 生成 RSA 密钥需要: `pip install cryptography`
- 生成 SM2 密钥需要: `pip install gmssl`

---

### 07_complete_workflow.py - 完整工作流

**功能**: 演示端到端的完整工作流程

**内容**:
1. 设置和配置
2. 生成加密密钥
3. 准备测试数据
4. 上传加密数据
5. 下载并解密数据
6. 验证文件完整性

**运行**:
```bash
python examples/07_complete_workflow.py
```

**前置条件**:
- 安装上传依赖: `pip install xiaoshiai-hub[upload]`
- 设置 `MOHA_USERNAME` 和 `MOHA_PASSWORD` 环境变量

---

## ⚙️ 环境配置

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `MOHA_ENDPOINT` | Hub 服务端点 | `https://hub.example.com` |
| `MOHA_USERNAME` | 用户名 | `your-username` |
| `MOHA_PASSWORD` | 密码 | `your-password` |

### 可选的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ENCRYPTION_KEY` | 上传时使用的加密密钥 | `S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB` |
| `DECRYPTION_KEY` | 下载时使用的解密密钥 | `S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB` |

### 配置方法

#### 方法 1: 使用 `.env` 文件

创建 `.env` 文件：

```bash
MOHA_ENDPOINT=https://hub.example.com
MOHA_USERNAME=your-username
MOHA_PASSWORD=your-password
ENCRYPTION_KEY=S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB
DECRYPTION_KEY=S4v57YbMPMN9JPnEjWd9ZuVRyEDqvJKB
```

然后使用 `python-dotenv` 加载：

```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()
```

#### 方法 2: 直接设置环境变量

**Linux/macOS**:
```bash
export MOHA_USERNAME="your-username"
export MOHA_PASSWORD="your-password"
```

**Windows (PowerShell)**:
```powershell
$env:MOHA_USERNAME="your-username"
$env:MOHA_PASSWORD="your-password"
```

**Windows (CMD)**:
```cmd
set MOHA_USERNAME=your-username
set MOHA_PASSWORD=your-password
```

## 🏃 运行示例

### 运行单个示例

```bash
# 运行基础使用示例
python examples/01_basic_usage.py

# 运行下载文件示例
python examples/02_download_file.py

# 运行完整工作流示例
python examples/07_complete_workflow.py
```

### 运行所有示例

```bash
# 运行所有示例（按顺序）
for script in examples/*.py; do
    echo "Running $script..."
    python "$script"
    echo ""
done
```

## ❓ 常见问题

### Q1: 运行示例时提示 "上传功能不可用"

**A**: 需要安装上传依赖：

```bash
pip install xiaoshiai-hub[upload]
```

### Q2: 运行示例时提示认证失败

**A**: 检查环境变量是否正确设置：

```bash
echo $MOHA_USERNAME
echo $MOHA_PASSWORD
```

### Q3: 下载加密文件失败

**A**: 确保设置了正确的解密密钥和算法：

```bash
export DECRYPTION_KEY="your-decryption-key"
```

### Q4: 如何生成加密密钥？

**A**: 运行加密示例：

```bash
python examples/06_encryption.py
```

### Q5: 示例中的仓库 ID 如何修改？

**A**: 编辑示例文件，修改 `REPO_ID` 变量：

```python
REPO_ID = "your-org/your-repo"
```

## 📖 更多资源

- [SDK 文档](../README.md)
- [API 参考](../docs/api.md)
- [PyPI 发布指南](../info.md)

## 🤝 贡献

欢迎提交问题和改进建议！

## 📄 许可证

本示例代码遵循与主项目相同的许可证。

