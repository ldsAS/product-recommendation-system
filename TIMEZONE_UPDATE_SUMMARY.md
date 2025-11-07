# 台灣時區設定更新總結

## 修改內容

### 1. 後端時區設定 (`src/utils/memory_monitor_store.py`)

**修改項目：**
- 導入 `timezone` 模組
- 定義台灣時區常量：`TW_TIMEZONE = timezone(timedelta(hours=8))`
- 修改 `add_record()` 方法：使用 `datetime.now(TW_TIMEZONE)` 記錄時間戳
- 修改 `get_records()` 方法：使用台灣時區計算時間窗口

**效果：**
- 所有監控記錄的時間戳都會包含 `+08:00` 時區信息
- 例如：`2025-11-07T16:54:46.297192+08:00`

### 2. 前端時間顯示 (`src/web/templates/trends.html`)

**修改項目：**
- 品質趨勢圖的 X 軸標題改為：`時間 (台灣時區 UTC+8)`
- 性能趨勢圖的 X 軸標題改為：`時間 (台灣時區 UTC+8)`
- 添加 X 軸 ticks 回調函數，使用 `toLocaleString()` 轉換為台灣時區
- 添加 tooltip title 回調函數，顯示完整的台灣時區時間
- 使用 `timeZone: 'Asia/Taipei'` 確保時間正確顯示

**效果：**
- 圖表 X 軸會顯示台灣時區時間（格式：MM/dd HH:mm）
- 滑鼠懸停時會顯示完整的台灣時區時間（格式：yyyy/MM/dd HH:mm:ss）
- 所有時間都會自動轉換為台灣時區，無論瀏覽器在哪個時區

## 測試驗證

執行測試腳本：
```bash
python test_timezone.py
```

測試結果：
- ✓ 時區常量設定正確 (UTC+08:00)
- ✓ 記錄時間戳包含正確的時區信息 (+08:00)
- ✓ 時間解析和顯示正確

## 如何使用

1. **啟動 Web UI：**
   ```bash
   python src/web/app.py
   ```

2. **訪問趨勢分析頁面：**
   - 打開瀏覽器訪問：http://localhost:8000/trends
   - 或從主頁面點擊「趨勢分析」按鈕

3. **查看時間顯示：**
   - 圖表 X 軸會顯示台灣時區時間
   - 滑鼠懸停在數據點上會顯示完整的台灣時間

## 注意事項

1. **時區一致性：**
   - 所有新記錄都會使用台灣時區
   - 舊記錄（如果有）可能沒有時區信息，系統會自動補充

2. **瀏覽器時區：**
   - Chart.js 會使用瀏覽器的本地時區來顯示時間
   - 由於後端已經使用台灣時區，所以顯示會是正確的台灣時間

3. **重啟服務：**
   - 修改後需要重啟 Web UI 服務才能生效
   - 使用 Ctrl+C 停止服務，然後重新啟動

## 相關文件

- `src/utils/memory_monitor_store.py` - 監控數據存儲（後端時區設定）
- `src/web/templates/trends.html` - 趨勢分析頁面（前端時間顯示）
- `test_timezone.py` - 時區測試腳本

## 技術細節

### ISO 8601 時間格式
```
2025-11-07T16:54:46.297192+08:00
│          │                 └─ 時區偏移 (UTC+8)
│          └─ 時間 (時:分:秒.微秒)
└─ 日期 (年-月-日)
```

### Python datetime 時區處理
```python
from datetime import datetime, timezone, timedelta

# 定義台灣時區
TW_TIMEZONE = timezone(timedelta(hours=8))

# 獲取台灣時間
now_tw = datetime.now(TW_TIMEZONE)

# 輸出 ISO 格式（包含時區）
timestamp = now_tw.isoformat()
```

### Chart.js 時間軸配置
```javascript
scales: {
    x: {
        type: 'time',
        time: {
            unit: 'hour',
            displayFormats: {
                hour: 'MM/dd HH:mm'
            },
            tooltipFormat: 'yyyy/MM/dd HH:mm:ss'
        },
        ticks: {
            callback: function(value, index, ticks) {
                // 將時間轉換為台灣時區顯示
                const date = new Date(value);
                return date.toLocaleString('zh-TW', {
                    timeZone: 'Asia/Taipei',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                });
            }
        },
        title: {
            display: true,
            text: '時間 (台灣時區 UTC+8)'
        }
    }
},
plugins: {
    tooltip: {
        callbacks: {
            title: function(context) {
                // 顯示台灣時區時間
                const date = new Date(context[0].parsed.x);
                return date.toLocaleString('zh-TW', { 
                    timeZone: 'Asia/Taipei',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                });
            }
        }
    }
}
```
