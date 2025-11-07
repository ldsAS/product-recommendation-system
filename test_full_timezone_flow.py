"""
完整時區流程測試
測試從後端記錄到前端顯示的完整流程
"""
from datetime import datetime, timezone, timedelta
from src.utils.memory_monitor_store import get_monitor_store, TW_TIMEZONE
import json

print("=" * 70)
print("完整時區流程測試")
print("=" * 70)

# 1. 後端記錄時間
print("\n【步驟 1】後端記錄監控數據")
print("-" * 70)

monitor_store = get_monitor_store()

# 清空舊記錄
monitor_store.records.clear()

# 添加測試記錄
test_records = []
for i in range(3):
    record = {
        'member_code': f'TEST{i:03d}',
        'response_time_ms': 100 + i * 10,
        'reference_value_score': {
            'overall_score': 85.0 + i,
            'relevance_score': 90.0,
            'novelty_score': 80.0,
            'explainability_score': 85.0,
            'diversity_score': 85.0
        }
    }
    monitor_store.add_record(record)
    test_records.append(record)
    print(f"  記錄 {i+1}: {record['timestamp']}")

# 2. 驗證時間戳格式
print("\n【步驟 2】驗證時間戳格式")
print("-" * 70)

records = monitor_store.get_records(time_window_minutes=5)
for i, record in enumerate(records):
    timestamp_str = record['timestamp']
    timestamp = datetime.fromisoformat(timestamp_str)
    
    print(f"\n  記錄 {i+1}:")
    print(f"    原始時間戳: {timestamp_str}")
    print(f"    時區信息: {timestamp.tzinfo}")
    print(f"    UTC 偏移: {timestamp.utcoffset()}")
    
    # 驗證是否為台灣時區
    if '+08:00' in timestamp_str:
        print(f"    ✓ 時區正確 (UTC+8)")
    else:
        print(f"    ✗ 時區錯誤")

# 3. 模擬 API 響應
print("\n【步驟 3】模擬 API 響應")
print("-" * 70)

api_response = {
    'total_records': len(records),
    'records': records
}

print(f"  API 返回記錄數: {api_response['total_records']}")
print(f"  第一條記錄時間戳: {api_response['records'][0]['timestamp']}")

# 4. 模擬前端 JavaScript 處理
print("\n【步驟 4】模擬前端 JavaScript 時間處理")
print("-" * 70)

# Python 模擬 JavaScript 的 new Date() 行為
for i, record in enumerate(records):
    timestamp_str = record['timestamp']
    
    # Python 解析（類似 JavaScript 的 new Date()）
    dt = datetime.fromisoformat(timestamp_str)
    
    # 轉換為 UTC（JavaScript 內部使用 UTC）
    dt_utc = dt.astimezone(timezone.utc)
    
    # 轉換回台灣時區（類似 toLocaleString 的行為）
    dt_tw = dt.astimezone(TW_TIMEZONE)
    
    print(f"\n  記錄 {i+1}:")
    print(f"    原始時間: {timestamp_str}")
    print(f"    UTC 時間: {dt_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"    台灣時間: {dt_tw.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # 驗證時間是否一致
    original_hour = dt.hour
    tw_hour = dt_tw.hour
    
    if original_hour == tw_hour:
        print(f"    ✓ 時間一致 (小時: {original_hour})")
    else:
        print(f"    ✗ 時間不一致 (原始: {original_hour}, 台灣: {tw_hour})")

# 5. 總結
print("\n" + "=" * 70)
print("測試總結")
print("=" * 70)

all_correct = True
for record in records:
    if '+08:00' not in record['timestamp']:
        all_correct = False
        break

if all_correct:
    print("✓ 所有時間戳都包含正確的台灣時區信息 (+08:00)")
    print("✓ 前端使用 toLocaleString('zh-TW', {timeZone: 'Asia/Taipei'}) 可正確顯示")
    print("\n建議：")
    print("  1. 重啟 Web UI 服務")
    print("  2. 訪問 http://localhost:8000/trends")
    print("  3. 檢查圖表上的時間是否顯示為台灣時區")
else:
    print("✗ 時區設定有問題，請檢查代碼")

print("=" * 70)
