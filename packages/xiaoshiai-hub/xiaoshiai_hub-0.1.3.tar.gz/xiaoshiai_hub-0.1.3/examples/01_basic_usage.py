#!/usr/bin/env python3
"""
基础使用示例 - XiaoShi AI Hub Python SDK

本示例演示如何使用 HubClient API 进行基本操作：
- 创建客户端
- 获取仓库信息
- 列出分支和标签
- 浏览仓库内容
"""

from xiaoshiai_hub import HubClient
import os


def main():
    """基础使用示例"""
    print("=" * 80)
    print("示例 1: 基础使用 - HubClient API")
    print("=" * 80)
    print()

    # 配置信息
    # 可以通过环境变量 MOHA_ENDPOINT 设置 Hub URL
    # 例如: export MOHA_ENDPOINT="https://your-hub-url.com/moha"
    REPO_ID = "system/encryption"
    REPO_TYPE = "models"
    
    # 从环境变量读取认证信息（推荐）
    USERNAME = os.environ.get("MOHA_USERNAME", "your-username")
    PASSWORD = os.environ.get("MOHA_PASSWORD", "your-password")

    # 创建客户端
    print("🔧 创建 HubClient...")
    client = HubClient(
        username=USERNAME,
        password=PASSWORD,
        # base_url 可选，默认从环境变量 MOHA_ENDPOINT 读取
    )
    print("✅ 客户端创建成功")
    print()

    # 解析仓库 ID
    org, repo = REPO_ID.split('/')

    # 1. 获取仓库信息
    print("📦 获取仓库信息...")
    try:
        repo_info = client.get_repository_info(org, REPO_TYPE, repo)
        print(f"  名称: {repo_info.name}")
        print(f"  组织: {repo_info.organization}")
        print(f"  类型: {repo_info.type}")
        if repo_info.description:
            print(f"  描述: {repo_info.description}")
        if repo_info.metadata:
            print(f"  元数据: {repo_info.metadata}")
        print("✅ 仓库信息获取成功")
    except Exception as e:
        print(f"❌ 获取仓库信息失败: {e}")
        return
    print()

    # 2. 列出分支和标签
    print("🌿 列出分支和标签...")
    try:
        refs = client.get_repository_refs(org, REPO_TYPE, repo)
        default_branch = None
        
        print(f"  共找到 {len(refs)} 个引用")
        print()
        print(f"  {'类型':<10} {'名称':<25} {'提交哈希':<12} {'标记'}")
        print("  " + "-" * 60)
        
        for ref in refs[:10]:  # 只显示前10个
            marker = "⭐ 默认" if ref.is_default else ""
            if ref.is_default and ref.type == "branch":
                default_branch = ref.name
            print(f"  {ref.type:<10} {ref.name:<25} {ref.hash[:10]:<12} {marker}")
        
        if len(refs) > 10:
            print(f"  ... 还有 {len(refs) - 10} 个引用")
        
        if default_branch:
            print()
            print(f"  默认分支: {default_branch}")
        
        print("✅ 引用列表获取成功")
    except Exception as e:
        print(f"❌ 获取引用列表失败: {e}")
        return
    print()

    # 3. 列出仓库内容
    print("📁 列出仓库内容...")
    try:
        branch = default_branch or "main"
        content = client.get_repository_content(org, REPO_TYPE, repo, branch, "")
        
        if content.entries:
            print(f"  分支: {branch}")
            print(f"  路径: / (根目录)")
            print(f"  共 {len(content.entries)} 个项目")
            print()
            print(f"  {'类型':<6} {'名称':<45} {'大小'}")
            print("  " + "-" * 70)
            
            for entry in content.entries[:20]:  # 只显示前20个
                icon = "📄" if entry.type == "file" else "📁"
                size = f"{entry.size:,} bytes" if entry.type == "file" else "-"
                print(f"  {icon}    {entry.path:<45} {size}")
            
            if len(content.entries) > 20:
                print(f"  ... 还有 {len(content.entries) - 20} 个项目")
            
            print("✅ 仓库内容获取成功")
        else:
            print("  仓库为空")
    except Exception as e:
        print(f"❌ 获取仓库内容失败: {e}")
        return
    print()

    # 4. 浏览子目录（如果存在）
    print("📂 浏览子目录示例...")
    try:
        # 尝试浏览第一个目录
        first_dir = None
        for entry in content.entries:
            if entry.type == "directory":
                first_dir = entry.path
                break
        
        if first_dir:
            print(f"  浏览目录: {first_dir}")
            subdir_content = client.get_repository_content(
                org, REPO_TYPE, repo, branch, first_dir
            )
            
            if subdir_content.entries:
                print(f"  共 {len(subdir_content.entries)} 个项目")
                for entry in subdir_content.entries[:5]:
                    icon = "📄" if entry.type == "file" else "📁"
                    print(f"    {icon} {entry.path}")
                
                if len(subdir_content.entries) > 5:
                    print(f"    ... 还有 {len(subdir_content.entries) - 5} 个项目")
            
            print("✅ 子目录浏览成功")
        else:
            print("  未找到子目录")
    except Exception as e:
        print(f"⚠️  浏览子目录失败: {e}")
    print()

    print("=" * 80)
    print("✨ 基础使用示例完成！")
    print("=" * 80)
    print()
    print("💡 提示:")
    print("  - 使用环境变量 MOHA_ENDPOINT 设置 Hub URL")
    print("  - 使用环境变量 MOHA_USERNAME 和 MOHA_PASSWORD 设置认证信息")
    print("  - 查看其他示例了解更多功能")
    print()


if __name__ == "__main__":
    main()

