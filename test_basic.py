#!/usr/bin/env python3
"""
基本功能测试脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from src.gradle_downloader.core import RepositoryManager
        print("✓ 核心模块导入成功")
    except ImportError as e:
        print(f"✗ 核心模块导入失败: {e}")
        return False
    
    try:
        from src.gradle_downloader.decompiler import JavaDecompiler
        print("✓ 反编译模块导入成功")
    except ImportError as e:
        print(f"✗ 反编译模块导入失败: {e}")
        return False
    
    try:
        from src.gradle_downloader.utils import validate_dependency_format
        print("✓ 工具模块导入成功")
    except ImportError as e:
        print(f"✗ 工具模块导入失败: {e}")
        return False
    
    try:
        from src.gradle_downloader.cli import cli
        print("✓ CLI 模块导入成功")
    except ImportError as e:
        print(f"✗ CLI 模块导入失败: {e}")
        return False
    
    try:
        from src.gradle_downloader.gui import launch_gui
        print("✓ GUI 模块导入成功")
    except ImportError as e:
        print(f"✗ GUI 模块导入失败: {e}")
        return False
    
    return True

def test_dependency_parsing():
    """测试依赖解析"""
    print("\n测试依赖解析...")
    
    from src.gradle_downloader.core import RepositoryManager
    from src.gradle_downloader.utils import validate_dependency_format
    
    repo_manager = RepositoryManager()
    
    # 测试有效格式
    valid_deps = [
        "com.google.guava:guava:31.1-jre",
        "org.springframework:spring-core:5.3.21",
        "com.google.gson:gson:2.8.9"
    ]
    
    for dep in valid_deps:
        if validate_dependency_format(dep):
            try:
                group, artifact, version = repo_manager.parse_dependency(dep)
                print(f"✓ {dep} -> {group}:{artifact}:{version}")
            except Exception as e:
                print(f"✗ 解析失败 {dep}: {e}")
                return False
        else:
            print(f"✗ 格式验证失败: {dep}")
            return False
    
    # 测试无效格式
    invalid_deps = [
        "invalid",
        "group:artifact",
        "group:artifact:version:extra"
    ]
    
    for dep in invalid_deps:
        if not validate_dependency_format(dep):
            print(f"✓ 正确识别无效格式: {dep}")
        else:
            print(f"✗ 应该识别为无效格式: {dep}")
            return False
    
    return True

def test_repository_connection():
    """测试仓库连接"""
    print("\n测试仓库连接...")
    
    from src.gradle_downloader.core import RepositoryManager
    
    repo_manager = RepositoryManager()
    
    # 测试一个已知存在的构件
    test_url = repo_manager.get_artifact_url(
        "https://repo1.maven.org/maven2/",
        "com.google.gson",
        "gson",
        "2.8.9"
    )
    
    print(f"测试 URL: {test_url}")
    
    if repo_manager.check_artifact_exists(test_url):
        print("✓ 仓库连接正常")
        return True
    else:
        print("✗ 仓库连接失败")
        return False

def test_search_functionality():
    """测试搜索功能"""
    print("\n测试搜索功能...")
    
    from src.gradle_downloader.core import RepositoryManager
    
    repo_manager = RepositoryManager()
    
    try:
        results = repo_manager.search_artifact("gson", 3)
        if results:
            print(f"✓ 搜索成功，找到 {len(results)} 个结果")
            for result in results[:2]:  # 只显示前2个
                print(f"  - {result.get('group', '')}:{result.get('artifact', '')}:{result.get('version', '')}")
            return True
        else:
            print("✗ 搜索返回空结果")
            return False
    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        return False

def test_java_availability():
    """测试 Java 环境"""
    print("\n测试 Java 环境...")
    
    from src.gradle_downloader.decompiler import JavaDecompiler
    
    decompiler = JavaDecompiler()
    
    if decompiler.check_java_available():
        print("✓ Java 环境可用")
        return True
    else:
        print("✗ Java 环境不可用 (反编译功能将不可用)")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("Gradle File Downloader 基本功能测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("依赖解析", test_dependency_parsing),
        ("仓库连接", test_repository_connection),
        ("搜索功能", test_search_functionality),
        ("Java环境", test_java_availability),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} 通过")
            else:
                print(f"✗ {test_name} 失败")
        except Exception as e:
            print(f"✗ {test_name} 异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！工具已准备就绪。")
    elif passed == total - 1 and not test_java_availability():
        print("⚠️  大部分功能正常，但 Java 环境不可用。")
        print("   请安装 Java 以使用反编译功能。")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    
    print(f"{'='*50}")
    
    # 显示使用提示
    if passed >= total - 1:  # Java 可选
        print("\n使用示例:")
        print("  启动 GUI:  uv run gradle-downloader gui")
        print("  CLI 帮助:  uv run gfd --help")
        print("  下载示例:  uv run gfd download com.google.gson:gson:2.8.9")

if __name__ == "__main__":
    main() 