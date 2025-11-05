# 監控儀表板使用指南

## 概述

監控儀表板提供推薦系統的即時監控和歷史分析功能，幫助團隊了解系統運行狀態、識別問題並優化性能。

## 訪問儀表板

### 啟動 Web UI

```bash
# Windows
start_web_ui.bat

# Linux/Mac
python -m src.web.app
```

### 訪問地址

- **主儀表板**: http://localhost:8000/dashboard
- **趨勢分析**: http://localhost:8000/trends
- **API 文檔**: http://localhost:8000/docs

---

## 儀表板功能

### 1. 即時監控面板

顯示當前系統運行狀態和關鍵指標。

#### 品質指標卡片

顯示推薦品質的四個維度分數：

| 指標 | 說明 | 目標值 | 狀態指示 |
|------|------|--------|----------|
| 綜合可參考價值 | 四個維度的加權平均 | > 60 | 🟢 正常 / 🟡 警告 / 🔴 嚴重 |
| 相關性分數 | 推薦與會員偏好的匹配度 | > 70 | 🟢 正常 / 🟡 警告 / 🔴 嚴重 |
| 新穎性分數 | 新產品和新類別的比例 | > 30 | 🟢 正常 / 🟡 警告 / 🔴 嚴重 |
| 可解釋性分數 | 推薦理由的清晰度 | > 80 | 🟢 正常 / 🟡 警告 / 🔴 嚴重 |
| 多樣性分數 | 推薦的多樣化程度 | > 60 | 🟢 正常 / 🟡 警告 / 🔴 嚴重 |

**狀態指示說明**:
- 🟢 **正常**: 分數達到或超過目標值
- 🟡 **警告**: 分數低於目標值但高於警告線
- 🔴 **嚴重**: 分數低於嚴重告警線

#### 性能指標卡片

顯示系統反應時間統計：

| 指標 | 說明 | 目標值 |
|------|------|--------|
| P50 反應時間 | 50% 的請求在此時間內完成 | < 200ms |
| P95 反應時間 | 95% 的請求在此時間內完成 | < 500ms |
| P99 反應時間 | 99% 的請求在此時間內完成 | < 1000ms |
| 平均反應時間 | 所有請求的平均耗時 | < 300ms |

#### 系統統計

顯示系統運行統計：

- **總推薦次數**: 時間窗口內的推薦總數
- **唯一會員數**: 接受推薦的唯一會員數
- **降級次數**: 使用降級策略的次數
- **告警數量**: 觸發的告警總數

---

### 2. 告警列表

顯示最近的告警記錄，按時間倒序排列。

#### 告警等級

| 等級 | 圖標 | 說明 | 處理優先級 |
|------|------|------|------------|
| CRITICAL | 🔴 | 嚴重告警 | 立即處理 |
| WARNING | 🟡 | 警告 | 盡快處理 |
| INFO | 🔵 | 資訊 | 關注即可 |

#### 告警範例

```
🔴 CRITICAL - 綜合分數過低: 38.5 < 40.0
   時間: 2025-01-15 10:25:30
   建議: 檢查推薦策略配置，考慮使用降級策略

🟡 WARNING - 多樣性分數低於警告線: 48.5 < 50.0
   時間: 2025-01-15 10:20:15
   建議: 增加推薦產品的類別和品牌多樣性

🟡 WARNING - P95反應時間接近閾值: 520.3ms > 500ms
   時間: 2025-01-15 10:15:45
   建議: 檢查系統負載，優化慢查詢
```

---

### 3. 趨勢分析

訪問 `/trends` 頁面查看歷史趨勢。

#### 可參考價值分數趨勢圖

顯示綜合分數和各維度分數的時間序列變化。

**圖表類型**: 折線圖

**時間範圍選擇**:
- 最近 1 小時
- 最近 6 小時
- 最近 24 小時
- 最近 7 天

**顯示指標**:
- 綜合可參考價值分數（粗線）
- 相關性分數
- 新穎性分數
- 可解釋性分數
- 多樣性分數

**使用方法**:
1. 選擇時間範圍
2. 點擊圖例可隱藏/顯示特定指標
3. 滑鼠懸停查看具體數值
4. 識別分數下降的時間點

#### 反應時間分布圖

顯示反應時間的百分位數變化。

**圖表類型**: 折線圖

**顯示指標**:
- P50 反應時間
- P95 反應時間
- P99 反應時間
- 平均反應時間

**閾值線**:
- P50 目標線: 200ms
- P95 目標線: 500ms
- P99 目標線: 1000ms

#### 各階段耗時佔比圖

顯示推薦流程各階段的平均耗時佔比。

**圖表類型**: 餅圖

**階段**:
- 特徵載入
- 模型推理
- 推薦合併
- 理由生成
- 品質評估

**用途**: 識別性能瓶頸階段

---

## 使用場景

### 場景 1: 日常監控

**目標**: 確保系統正常運行

**操作步驟**:
1. 每天早上查看儀表板
2. 檢查品質指標是否正常（綠色狀態）
3. 檢查性能指標是否達標
4. 查看是否有新告警
5. 如有異常，查看趨勢圖分析原因

**正常狀態標準**:
- ✓ 綜合分數 > 60
- ✓ P95 反應時間 < 500ms
- ✓ 無 CRITICAL 告警
- ✓ WARNING 告警 < 5 個/小時

### 場景 2: 問題排查

**目標**: 快速定位和解決問題

**操作步驟**:

1. **發現問題**
   - 收到告警通知
   - 用戶反饋推薦品質下降
   - 系統反應變慢

2. **查看即時監控**
   - 確認當前指標狀態
   - 查看告警詳情
   - 記錄問題發生時間

3. **分析趨勢**
   - 切換到趨勢分析頁面
   - 選擇包含問題時間點的時間範圍
   - 觀察指標變化趨勢
   - 識別異常開始時間

4. **定位原因**
   - 檢查各階段耗時佔比
   - 查看慢查詢列表
   - 檢查系統資源使用情況
   - 查看應用日誌

5. **採取措施**
   - 根據問題類型採取相應措施
   - 監控指標是否恢復正常
   - 記錄問題和解決方案

### 場景 3: 性能優化

**目標**: 持續優化系統性能

**操作步驟**:

1. **建立基準**
   - 記錄當前性能指標
   - 設定優化目標

2. **識別瓶頸**
   - 查看各階段耗時佔比
   - 找出耗時最長的階段
   - 分析慢查詢原因

3. **實施優化**
   - 針對瓶頸階段進行優化
   - 部署優化後的代碼

4. **驗證效果**
   - 對比優化前後的指標
   - 確認性能提升
   - 記錄優化效果

### 場景 4: A/B 測試分析

**目標**: 比較不同推薦策略的效果

**操作步驟**:

1. **設置 A/B 測試**
   - 配置測試組和對照組
   - 設定測試時長

2. **監控測試過程**
   - 定期查看各組的品質指標
   - 記錄關鍵數據點

3. **分析測試結果**
   - 使用 API 獲取各組統計數據
   - 比較可參考價值分數
   - 比較反應時間
   - 執行統計顯著性檢驗

4. **做出決策**
   - 根據數據選擇最優策略
   - 全量部署獲勝策略

---

## API 整合

### 獲取即時監控數據

```python
import requests

def get_realtime_monitoring(time_window_minutes=60):
    """獲取即時監控數據"""
    url = "http://localhost:8000/api/v1/monitoring/realtime"
    params = {"time_window_minutes": time_window_minutes}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return {
        'quality': data['quality_metrics'],
        'performance': data['performance_metrics'],
        'total_records': data['total_records'],
        'degradation_count': data['degradation_count']
    }

# 使用範例
monitoring_data = get_realtime_monitoring(60)
print(f"平均綜合分數: {monitoring_data['quality']['overall_score']['avg']:.1f}")
print(f"P95反應時間: {monitoring_data['performance']['response_time_ms']['p95']:.1f}ms")
```

### 獲取告警記錄

```python
def get_alerts(time_window_minutes=60, level=None):
    """獲取告警記錄"""
    url = "http://localhost:8000/api/v1/monitoring/alerts"
    params = {
        "time_window_minutes": time_window_minutes,
        "level": level
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    return data['alerts']

# 獲取最近1小時的 CRITICAL 告警
critical_alerts = get_alerts(60, level="critical")
for alert in critical_alerts:
    print(f"[{alert['level']}] {alert['message']}")
    print(f"  時間: {alert['timestamp']}")
```

### 生成自訂報告

```python
def generate_custom_report(start_time, end_time):
    """生成自訂時間範圍的報告"""
    # 獲取監控數據
    monitoring_data = get_realtime_monitoring()
    alerts = get_alerts()
    
    # 生成報告
    report = {
        'period': f"{start_time} - {end_time}",
        'summary': {
            'total_recommendations': monitoring_data['total_records'],
            'avg_quality_score': monitoring_data['quality']['overall_score']['avg'],
            'p95_response_time': monitoring_data['performance']['response_time_ms']['p95'],
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['level'] == 'critical'])
        },
        'quality_breakdown': {
            'relevance': monitoring_data['quality']['relevance_score']['avg'],
            'novelty': monitoring_data['quality']['novelty_score']['avg'],
            'explainability': monitoring_data['quality']['explainability_score']['avg'],
            'diversity': monitoring_data['quality']['diversity_score']['avg']
        }
    }
    
    return report

# 生成報告
report = generate_custom_report("2025-01-15 00:00", "2025-01-15 23:59")
print(f"總推薦次數: {report['summary']['total_recommendations']}")
print(f"平均品質分數: {report['summary']['avg_quality_score']:.1f}")
```

---

## 告警配置

### 告警閾值

在 `config/recommendation_config.yaml` 中配置告警閾值：

```yaml
quality_thresholds:
  overall_score:
    critical: 40  # 低於40分觸發 CRITICAL 告警
    warning: 50   # 低於50分觸發 WARNING 告警
    target: 60    # 目標值
  
  relevance_score:
    critical: 50
    warning: 60
    target: 70
  
  novelty_score:
    critical: 15
    warning: 20
    target: 30
  
  explainability_score:
    critical: 60
    warning: 70
    target: 80
  
  diversity_score:
    critical: 40
    warning: 50
    target: 60

performance_thresholds:
  total_time_ms:
    p50: 200
    p95: 500
    p99: 1000
  
  feature_loading_ms:
    max: 100
  
  model_inference_ms:
    max: 200
```

### 告警通道

配置告警通知方式：

```yaml
monitoring:
  enable_real_time: true
  enable_hourly_report: true
  enable_daily_report: true
  
  alert_channels:
    - email
    - slack
    - webhook
  
  email_config:
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    from_email: "alerts@example.com"
    to_emails:
      - "team@example.com"
  
  slack_config:
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    channel: "#recommendations-alerts"
  
  webhook_config:
    url: "https://your-webhook-endpoint.com/alerts"
    method: "POST"
```

---

## 最佳實踐

### 1. 定期檢查

- **每日**: 查看儀表板，確認系統正常
- **每週**: 查看趨勢報告，識別長期趨勢
- **每月**: 生成月度報告，評估系統改進

### 2. 告警處理

- **CRITICAL 告警**: 立即處理，15分鐘內響應
- **WARNING 告警**: 1小時內處理
- **INFO 告警**: 記錄並定期回顧

### 3. 性能基準

建立性能基準並定期更新：

```python
PERFORMANCE_BASELINE = {
    'overall_score': 65.0,
    'p95_response_time': 450.0,
    'degradation_rate': 0.01  # 1%
}

# 定期對比當前指標與基準
def compare_with_baseline(current_metrics):
    score_diff = current_metrics['overall_score'] - PERFORMANCE_BASELINE['overall_score']
    time_diff = current_metrics['p95_response_time'] - PERFORMANCE_BASELINE['p95_response_time']
    
    print(f"品質分數變化: {score_diff:+.1f}")
    print(f"P95反應時間變化: {time_diff:+.1f}ms")
```

### 4. 數據保留

- **即時數據**: 保留 7 天
- **小時統計**: 保留 30 天
- **日統計**: 保留 1 年
- **告警記錄**: 保留 90 天

---

## 故障排除

### 問題 1: 儀表板無法訪問

**症狀**: 無法打開 http://localhost:8000/dashboard

**解決方案**:
1. 檢查 Web 服務是否啟動
   ```bash
   # 查看進程
   ps aux | grep "python.*web.app"
   ```

2. 檢查端口是否被佔用
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

3. 查看應用日誌
   ```bash
   tail -f logs/web_app.log
   ```

### 問題 2: 數據不更新

**症狀**: 儀表板顯示的數據不是最新的

**解決方案**:
1. 檢查監控記錄是否正常寫入
   ```python
   from src.utils.quality_monitor import QualityMonitor
   
   monitor = QualityMonitor()
   count = monitor.get_record_count()
   print(f"記錄數量: {count}")
   ```

2. 檢查時間窗口設置
   - 確認選擇的時間範圍包含最新數據

3. 清除瀏覽器快取
   - 按 Ctrl+F5 強制刷新頁面

### 問題 3: 圖表顯示異常

**症狀**: 趨勢圖無法正常顯示

**解決方案**:
1. 檢查瀏覽器控制台錯誤
   - 按 F12 打開開發者工具
   - 查看 Console 標籤

2. 確認數據格式正確
   ```python
   # 測試 API 回應
   import requests
   response = requests.get("http://localhost:8000/api/v1/monitoring/realtime")
   print(response.json())
   ```

3. 更新前端依賴
   ```bash
   pip install --upgrade plotly dash
   ```

---

## 參考資料

- [API 文檔](API_DOCUMENTATION.md)
- [推薦可參考價值評估文檔](REFERENCE_VALUE_EVALUATION.md)
- [性能追蹤使用指南](PERFORMANCE_TRACKING_GUIDE.md)
- [監控儀表板實施報告](../MONITORING_DASHBOARD_IMPLEMENTATION.md)
