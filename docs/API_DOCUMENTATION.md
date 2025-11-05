# API 文檔

## 概述

本文檔描述推薦系統的 REST API 端點，包含增強版推薦 API 的新回應格式、監控查詢 API 和模型資訊 API。

## 基礎資訊

- **基礎 URL**: `http://localhost:8000/api/v1`
- **內容類型**: `application/json`
- **字元編碼**: `UTF-8`

## 認證

目前 API 不需要認證。生產環境部署時建議添加 API Key 或 OAuth 2.0 認證。

---

## 推薦 API

### 獲取產品推薦

根據會員資訊返回個性化產品推薦，包含可參考價值分數和性能指標。

**端點**: `POST /api/v1/recommendations`

**請求參數**:

| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| member_code | string | 是 | 會員編號 |
| phone | string | 否 | 會員電話 |
| total_consumption | float | 否 | 累計消費金額 |
| accumulated_bonus | float | 否 | 累計紅利點數 |
| recent_purchases | list[string] | 否 | 最近購買產品ID列表 |
| top_k | integer | 否 | 推薦數量，預設5 |
| min_confidence | float | 否 | 最低信心分數閾值（0-100） |

**查詢參數**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| use_enhanced | boolean | true | 是否使用增強推薦引擎 |

**請求範例**:

```json
{
  "member_code": "CU000001",
  "phone": "0912345678",
  "total_consumption": 15000.0,
  "accumulated_bonus": 1500.0,
  "recent_purchases": ["30469", "30470"],
  "top_k": 5,
  "min_confidence": 60.0
}
```

**回應格式**:

```json
{
  "recommendations": [
    {
      "product_id": "30469",
      "product_name": "杏輝蓉憶記膠囊",
      "confidence_score": 85.5,
      "explanation": "基於您購買過的蓉憶記系列產品",
      "rank": 1,
      "source": "ml_model",
      "raw_score": 0.855
    }
  ],
  "reference_value_score": {
    "overall_score": 65.2,
    "relevance_score": 72.5,
    "novelty_score": 32.1,
    "explainability_score": 85.3,
    "diversity_score": 58.7,
    "score_breakdown": {
      "relevance": {
        "score": 72.5,
        "weight": 0.4,
        "contribution": 29.0
      },
      "novelty": {
        "score": 32.1,
        "weight": 0.25,
        "contribution": 8.025
      },
      "explainability": {
        "score": 85.3,
        "weight": 0.2,
        "contribution": 17.06
      },
      "diversity": {
        "score": 58.7,
        "weight": 0.15,
        "contribution": 8.805
      }
    }
  },
  "performance_metrics": {
    "request_id": "req_CU000001_1234567890",
    "total_time_ms": 245.5,
    "stage_times": {
      "feature_loading": 45.2,
      "model_inference": 120.3,
      "reason_generation": 35.1,
      "quality_evaluation": 44.9
    },
    "is_slow_query": false
  },
  "response_time_ms": 245.5,
  "model_version": "v1.0.0",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "member_code": "CU000001",
  "timestamp": "2025-01-15T10:30:00",
  "quality_level": "good",
  "is_degraded": false
}
```

**回應欄位說明**:

| 欄位 | 類型 | 說明 |
|------|------|------|
| recommendations | array | 推薦產品列表 |
| recommendations[].product_id | string | 產品ID |
| recommendations[].product_name | string | 產品名稱 |
| recommendations[].confidence_score | float | 信心分數（0-100） |
| recommendations[].explanation | string | 推薦理由 |
| recommendations[].rank | integer | 推薦排名 |
| recommendations[].source | string | 推薦來源（ml_model/rule_based/popular） |
| recommendations[].raw_score | float | 原始模型分數（0-1） |
| reference_value_score | object | **新增** 推薦可參考價值分數 |
| reference_value_score.overall_score | float | 綜合分數（0-100） |
| reference_value_score.relevance_score | float | 相關性分數（0-100） |
| reference_value_score.novelty_score | float | 新穎性分數（0-100） |
| reference_value_score.explainability_score | float | 可解釋性分數（0-100） |
| reference_value_score.diversity_score | float | 多樣性分數（0-100） |
| reference_value_score.score_breakdown | object | 詳細分數拆解 |
| performance_metrics | object | **新增** 性能指標 |
| performance_metrics.request_id | string | 請求追蹤ID |
| performance_metrics.total_time_ms | float | 總反應時間（毫秒） |
| performance_metrics.stage_times | object | 各階段耗時 |
| performance_metrics.is_slow_query | boolean | 是否為慢查詢 |
| quality_level | string | **新增** 品質等級（excellent/good/acceptable/poor） |
| is_degraded | boolean | **新增** 是否使用降級策略 |
| response_time_ms | float | 回應時間（毫秒） |
| model_version | string | 模型版本 |
| request_id | string | 請求ID |
| member_code | string | 會員編號 |
| timestamp | string | 時間戳記（ISO 8601格式） |

**錯誤回應**:

```json
{
  "error": "validation_error",
  "message": "請求資料驗證失敗",
  "detail": ["會員編號不能為空"],
  "timestamp": "2025-01-15T10:30:00",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**狀態碼**:

- `200 OK`: 成功返回推薦結果
- `400 Bad Request`: 請求驗證失敗
- `500 Internal Server Error`: 伺服器內部錯誤
- `503 Service Unavailable`: 服務不可用（模型未載入）

---

## 模型資訊 API

### 獲取模型資訊

返回當前模型的版本、類型、訓練時間和效能指標。

**端點**: `GET /api/v1/model/info`

**請求範例**:

```bash
curl -X GET "http://localhost:8000/api/v1/model/info"
```

**回應範例**:

```json
{
  "model_version": "v1.0.0",
  "model_type": "lightgbm",
  "trained_at": "2025-01-15T10:30:00",
  "metrics": {
    "accuracy": 0.75,
    "precision": 0.72,
    "recall": 0.68,
    "f1_score": 0.70,
    "precision_at_5": 0.75,
    "recall_at_5": 0.68,
    "ndcg_at_5": 0.82,
    "map_at_5": 0.78
  },
  "total_products": 150,
  "total_members": 1000,
  "description": "基於 LightGBM 的產品推薦模型"
}
```

**狀態碼**:

- `200 OK`: 成功返回模型資訊
- `500 Internal Server Error`: 伺服器內部錯誤
- `503 Service Unavailable`: 服務不可用（模型未載入）

---

## 監控 API

### 獲取即時監控數據

返回最近一段時間的推薦品質和性能監控數據。

**端點**: `GET /api/v1/monitoring/realtime`

**查詢參數**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| time_window_minutes | integer | 60 | 時間窗口（分鐘） |
| member_code | string | null | 會員編號（可選） |

**請求範例**:

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/realtime?time_window_minutes=60"
```

**回應範例**:

```json
{
  "time_window_minutes": 60,
  "total_records": 150,
  "unique_members": 45,
  "quality_metrics": {
    "overall_score": {
      "avg": 65.2,
      "min": 42.1,
      "max": 88.5,
      "p50": 64.8,
      "p95": 82.3
    },
    "relevance_score": {
      "avg": 72.5,
      "min": 50.2,
      "max": 95.1
    },
    "novelty_score": {
      "avg": 32.1,
      "min": 15.3,
      "max": 65.8
    },
    "explainability_score": {
      "avg": 85.3,
      "min": 70.0,
      "max": 100.0
    },
    "diversity_score": {
      "avg": 58.7,
      "min": 35.2,
      "max": 85.4
    }
  },
  "performance_metrics": {
    "response_time_ms": {
      "avg": 245.5,
      "min": 120.3,
      "max": 850.2,
      "p50": 220.1,
      "p95": 480.5,
      "p99": 720.8
    }
  },
  "degradation_count": 2,
  "timestamp": "2025-01-15T10:30:00"
}
```

**狀態碼**:

- `200 OK`: 成功返回監控數據
- `500 Internal Server Error`: 伺服器內部錯誤

---

### 獲取歷史統計數據

返回指定時間範圍的推薦品質和性能統計數據。

**端點**: `GET /api/v1/monitoring/statistics`

**查詢參數**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| report_type | string | hourly | 報告類型（hourly/daily） |

**請求範例**:

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/statistics?report_type=hourly"
```

**回應範例**:

```json
{
  "report_type": "hourly",
  "start_time": "2025-01-15T09:00:00",
  "end_time": "2025-01-15T10:00:00",
  "recommendation_stats": {
    "total_recommendations": 150,
    "unique_members": 45,
    "avg_recommendations_per_member": 3.33
  },
  "quality_stats": {
    "avg_overall_score": 65.2,
    "avg_relevance_score": 72.5,
    "avg_novelty_score": 32.1,
    "avg_explainability_score": 85.3,
    "avg_diversity_score": 58.7
  },
  "performance_stats": {
    "avg_response_time_ms": 245.5,
    "p50_response_time_ms": 220.1,
    "p95_response_time_ms": 480.5,
    "p99_response_time_ms": 720.8
  },
  "alert_stats": {
    "total_alerts": 5,
    "critical_alerts": 1,
    "warning_alerts": 4,
    "degradation_count": 2
  },
  "trends": {
    "score_trend": "stable",
    "performance_trend": "improving"
  },
  "recommendations_for_improvement": [
    "新穎性分數(32.1)偏低，建議增加新產品和新類別的推薦比例"
  ],
  "timestamp": "2025-01-15T10:00:00"
}
```

**狀態碼**:

- `200 OK`: 成功返回統計數據
- `400 Bad Request`: 無效的報告類型
- `500 Internal Server Error`: 伺服器內部錯誤

---

### 獲取告警記錄

返回指定時間範圍和等級的告警記錄。

**端點**: `GET /api/v1/monitoring/alerts`

**查詢參數**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| time_window_minutes | integer | 60 | 時間窗口（分鐘） |
| level | string | null | 告警等級（info/warning/critical） |

**請求範例**:

```bash
curl -X GET "http://localhost:8000/api/v1/monitoring/alerts?time_window_minutes=60&level=warning"
```

**回應範例**:

```json
{
  "time_window_minutes": 60,
  "filter_level": "warning",
  "total_alerts": 4,
  "alert_counts": {
    "info": 0,
    "warning": 4,
    "critical": 0
  },
  "alerts": [
    {
      "level": "warning",
      "metric_name": "diversity_score",
      "current_value": 48.5,
      "threshold_value": 50.0,
      "message": "多樣性分數低於警告線: 48.5 < 50.0",
      "timestamp": "2025-01-15T10:25:00"
    }
  ],
  "timestamp": "2025-01-15T10:30:00"
}
```

**狀態碼**:

- `200 OK`: 成功返回告警記錄
- `400 Bad Request`: 無效的告警等級
- `500 Internal Server Error`: 伺服器內部錯誤

---

## 健康檢查 API

### 推薦服務健康檢查

檢查推薦服務是否正常運行。

**端點**: `GET /api/v1/recommendations/health`

**請求範例**:

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/health"
```

**回應範例**:

```json
{
  "status": "healthy",
  "service": "recommendations",
  "details": {
    "model_loaded": true,
    "model_version": "v1.0.0",
    "total_products": 150
  }
}
```

**狀態碼**:

- `200 OK`: 服務正常

---

## 使用範例

### Python 範例

```python
import requests

# 獲取推薦
def get_recommendations(member_code, top_k=5):
    url = "http://localhost:8000/api/v1/recommendations"
    payload = {
        "member_code": member_code,
        "top_k": top_k
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"推薦數量: {len(data['recommendations'])}")
        print(f"綜合可參考價值分數: {data['reference_value_score']['overall_score']:.1f}")
        print(f"反應時間: {data['performance_metrics']['total_time_ms']:.1f}ms")
        print(f"品質等級: {data['quality_level']}")
        
        for rec in data['recommendations']:
            print(f"  - {rec['product_name']} (信心分數: {rec['confidence_score']:.1f})")
            print(f"    理由: {rec['explanation']}")
    else:
        print(f"錯誤: {response.status_code}")
        print(response.json())

# 獲取即時監控數據
def get_monitoring_data():
    url = "http://localhost:8000/api/v1/monitoring/realtime"
    params = {"time_window_minutes": 60}
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"監控記錄數: {data['total_records']}")
        print(f"平均綜合分數: {data['quality_metrics']['overall_score']['avg']:.1f}")
        print(f"P95反應時間: {data['performance_metrics']['response_time_ms']['p95']:.1f}ms")
    else:
        print(f"錯誤: {response.status_code}")

# 使用範例
get_recommendations("CU000001", top_k=5)
get_monitoring_data()
```

### cURL 範例

```bash
# 獲取推薦
curl -X POST "http://localhost:8000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "member_code": "CU000001",
    "top_k": 5
  }'

# 獲取模型資訊
curl -X GET "http://localhost:8000/api/v1/model/info"

# 獲取即時監控數據
curl -X GET "http://localhost:8000/api/v1/monitoring/realtime?time_window_minutes=60"

# 獲取告警記錄
curl -X GET "http://localhost:8000/api/v1/monitoring/alerts?level=warning"
```

---

## 版本歷史

### v1.0.0 (2025-01-15)

- 新增增強推薦 API，包含可參考價值分數和性能指標
- 新增監控查詢 API（即時監控、歷史統計、告警記錄）
- 新增品質等級和降級狀態標記
- 保持向後兼容性

---

## 注意事項

1. **向後兼容性**: 新版 API 保持與舊版的向後兼容，原有欄位保持不變
2. **性能考量**: 建議設置合理的 `top_k` 值（建議 5-10），避免過大影響性能
3. **監控頻率**: 建議每分鐘查詢一次即時監控數據，避免過於頻繁
4. **告警處理**: 收到 CRITICAL 等級告警時應立即檢查系統狀態
5. **降級策略**: 當 `is_degraded=true` 時，表示系統使用了降級策略，推薦品質可能較低

---

## 支援

如有問題或建議，請聯繫開發團隊。
