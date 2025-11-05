## What's Changed in v1.8.0

### 🚀 新功能 (Features)

#### 動態版本管理
- ✅ 採用 setuptools-scm 從 Git tags 自動生成版本號
- ✅ 不再在程式碼中寫死版本號
- ✅ 支援開發版本自動標記 (e.g., 1.8.1.dev0+g668432028.d20251104)

#### VS Code Extension
- ✅ 完整的 VS Code Extension 結構
- ✅ 一鍵啟動/停止 MCP Server
- ✅ 內建配置管理 (帳號、憑證、數據目錄)
- ✅ 安全密碼輸入 (不儲存在設定中)
- ✅ 即時日誌輸出面板
- ✅ 命令面板支援 (Start/Stop/Restart/Show Logs)

#### 自動化發佈流程
- ✅ PyPI 自動發佈 (從 GitHub Release 觸發)
- ✅ VS Code Marketplace 自動發佈
- ✅ VSIX 檔案自動附加到 GitHub Release

### 🐛 修正 (Bug Fixes)
- 移除 Python 3.14 支援 (尚未正式發布)
- 修正版本號管理問題
- 改善 CI/CD 流程穩定性

### 📚 文檔 (Documentation)
- 新增完整的發佈指南 (.github/RELEASE_GUIDE.md)
- 新增發佈檢查清單 (.github/RELEASE_CHECKLIST.md)
- 新增 VS Code Extension 使用說明
- 新增 MCP 功能驗證腳本 (test_mcp_server.py)

### 🔧 維護 (Maintenance)
- 更新 pyproject.toml 和 setup.py 使用動態版本
- 新增 setuptools-scm 依賴
- 更新 .gitignore 排除 extension 建置產物
- 完善 GitHub Actions workflows

### 📦 VS Code Extension 功能

**Commands:**
- `Fubon MCP: Start` - 啟動 MCP Server
- `Fubon MCP: Stop` - 停止 MCP Server
- `Fubon MCP: Restart` - 重啟 MCP Server
- `Fubon MCP: Show Logs` - 顯示日誌

**Settings:**
- `fubon-mcp.username` - 富邦證券帳號
- `fubon-mcp.pfxPath` - PFX 憑證路徑
- `fubon-mcp.dataDir` - 數據儲存目錄
- `fubon-mcp.autoStart` - 自動啟動選項

### ⚠️ Breaking Changes

**版本管理變更:**
- 版本號現在從 Git tags 動態生成
- 建置時需要 setuptools-scm
- 本地開發版本會包含 commit hash 和日期

**升級指南:**
```bash
# 安裝新版本
pip install --upgrade fubon-api-mcp-server

# 驗證版本
python -c "import fubon_mcp; print(fubon_mcp.__version__)"
```

### 📥 安裝方式

**PyPI (Python Package):**
```bash
pip install fubon-api-mcp-server==1.8.0
```

**VS Code Extension:**
1. 從 Marketplace 搜尋 "Fubon API MCP Server"
2. 或從 Assets 下載 .vsix 檔案手動安裝

### 🔗 相關連結

- **PyPI**: https://pypi.org/project/fubon-api-mcp-server/
- **文檔**: https://github.com/Mofesto/fubon-api-mcp-server#readme
- **問題回報**: https://github.com/Mofesto/fubon-api-mcp-server/issues
- **富邦 API**: https://www.fbs.com.tw/TradeAPI/docs/

### 📊 測試狀態

- ✅ MCP 功能驗證: 5/5 通過
- ✅ CI/CD Pipeline: 全部通過
- ✅ 型別檢查 (mypy): 通過
- ✅ 代碼格式化: 通過
- ✅ 安全掃描: 通過

**Full Changelog**: https://github.com/Mofesto/fubon-api-mcp-server/compare/v1.7.0...v1.8.0
