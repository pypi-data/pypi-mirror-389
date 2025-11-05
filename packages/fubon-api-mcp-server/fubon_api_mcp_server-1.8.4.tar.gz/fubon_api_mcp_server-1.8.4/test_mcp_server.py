"""
MCP Server 功能驗證腳本

測試 fubon-api-mcp-server 的核心功能是否正常運作
"""
import sys
from fubon_mcp import __version__, mcp, main

def test_version():
    """測試版本資訊"""
    print(f"✓ 版本: {__version__}")
    return True

def test_module_imports():
    """測試模組導入"""
    try:
        from fubon_mcp import (
            callable_place_order,
            callable_get_account_info,
            callable_get_inventory,
            callable_get_bank_balance,
        )
        print("✓ 模組導入成功")
        return True
    except ImportError as e:
        print(f"✗ 模組導入失敗: {e}")
        return False

def test_mcp_server_object():
    """測試 MCP server 物件"""
    try:
        assert mcp is not None
        print(f"✓ MCP server 物件創建成功: {type(mcp).__name__}")
        return True
    except Exception as e:
        print(f"✗ MCP server 物件創建失敗: {e}")
        return False

def test_main_function():
    """測試 main 函數存在"""
    try:
        assert callable(main)
        print("✓ main() 函數可調用")
        return True
    except Exception as e:
        print(f"✗ main() 函數測試失敗: {e}")
        return False

def test_callable_wrappers():
    """測試 callable wrapper 函數"""
    try:
        from fubon_mcp import (
            callable_place_order,
            callable_get_account_info,
            callable_batch_place_order,
            callable_get_realtime_quotes,
        )
        
        wrappers = [
            callable_place_order,
            callable_get_account_info,
            callable_batch_place_order,
            callable_get_realtime_quotes,
        ]
        
        for wrapper in wrappers:
            assert callable(wrapper), f"{wrapper.__name__} 不可調用"
        
        print(f"✓ {len(wrappers)} 個 callable wrapper 函數正常")
        return True
    except Exception as e:
        print(f"✗ Callable wrapper 測試失敗: {e}")
        return False

def main_test():
    """主測試流程"""
    print("=" * 60)
    print("MCP Server 功能驗證測試")
    print("=" * 60)
    print()
    
    tests = [
        ("版本資訊", test_version),
        ("模組導入", test_module_imports),
        ("MCP Server 物件", test_mcp_server_object),
        ("Main 函數", test_main_function),
        ("Callable Wrappers", test_callable_wrappers),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n測試: {name}")
        print("-" * 60)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ 測試異常: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("測試摘要")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{status}: {name}")
    
    print()
    print(f"總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有 MCP 功能驗證測試通過！")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 個測試失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main_test())
