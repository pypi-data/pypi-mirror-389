# 測試覆蓋率改善計劃

## 當前狀態
- **總覆蓋率**: 28%
- **目標覆蓋率**: >80%
- **主要問題**: server.py 中大量函數未被測試覆蓋

## 優先改善項目

### 高優先級 (應涵蓋)
1. **錯誤處理函數** - 確保異常情況被正確測試
2. **數據驗證函數** - 測試輸入驗證邏輯
3. **API 回應處理** - 測試不同的 API 回應格式
4. **WebSocket 連接管理** - 測試連接/斷線場景

### 中優先級 (建議涵蓋)
1. **邊界條件測試** - 極端值和邊界情況
2. **並發測試** - 多線程操作的測試
3. **性能測試** - 響應時間和資源使用
4. **整合測試** - 端到端功能測試

### 低優先級 (可選)
1. **UI/UX 測試** - 如果有前端界面
2. **負載測試** - 高並發情況下的表現
3. **相容性測試** - 不同 Python 版本和依賴版本

## 具體改善建議

### 1. 增加單元測試
```python
# 範例: 測試錯誤處理
def test_api_error_handling():
    # 測試 API 調用失敗的情況
    pass

def test_invalid_input_validation():
    # 測試無效輸入的處理
    pass
```

### 2. 使用 Mock 技術
```python
# 使用 pytest-mock 模擬外部依賴
def test_fubon_api_with_mock(mocker):
    mock_api = mocker.patch('fubon_neo.api.place_order')
    mock_api.return_value = {'success': True}
    # 測試邏輯
```

### 3. 測試覆蓋率工具
```bash
# 生成詳細覆蓋率報告
pytest --cov=fubon_mcp --cov-report=html --cov-report=term-missing

# 查看哪些行沒有被覆蓋
coverage report --show-missing
```

### 4. CI/CD 整合
- 設定覆蓋率閾值 (目前設定為 25%)
- 自動上傳覆蓋率到 Codecov
- 覆蓋率下降時發出警告

## 里程碑目標

### Phase 1 (1-2 週)
- 目標覆蓋率: 50%
- 完成: 核心 API 函數測試
- 完成: 錯誤處理測試

### Phase 2 (2-4 週)
- 目標覆蓋率: 70%
- 完成: 邊界條件測試
- 完成: 整合測試

### Phase 3 (1-2 個月)
- 目標覆蓋率: 80%+
- 完成: 完整測試套件
- 完成: 持續整合

## 測試策略

1. **單元測試**: 測試個別函數和方法
2. **整合測試**: 測試組件間的互動
3. **端到端測試**: 測試完整用戶流程
4. **回歸測試**: 確保新功能不破壞現有功能

## 工具和框架

- **pytest**: 測試框架
- **pytest-cov**: 覆蓋率插件
- **pytest-mock**: Mock 工具
- **coverage.py**: 覆蓋率分析
- **Codecov**: 覆蓋率報告服務