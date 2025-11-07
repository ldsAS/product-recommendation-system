"""
測試台灣時區設定
"""
from datetime import datetime, timezone, timedelta
from src.utils.memory_monitor_store import get_monitor_store, TW_TIMEZONE

# 測試時區常量
print("=" * 60)
print("測試台灣時區設定")
print("=" * 60)

# 1. 測試時區常量
print(f"\n1. 台灣時區 (TW_TIMEZONE): {TW_TIMEZONE}")
print(f"   UTC 偏移: +8 小時")

# 2. 測試當前時間
now_utc = datetime.now(timezone.utc)
now_tw = datetime.now(TW_TIMEZONE)
print(f"\n2. 當前時間:")
print(f"   UTC 時間: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"   台灣時間: {now_tw.strftime('%Y-%m-%d %H:%M:%S %Z')}")

# 3. 測試監控存儲
print(f"\n3. 測試監控記錄時間戳:")
monitor_store = get_monitor_store()

# 添加測試記錄
test_record = {
    'member_code': 'TEST001',
    'response_time_ms': 100,
    'reference_value_score': {
        'overall_score': 85.5,
        'relevance_score': 90.0,
        'novelty_score': 80.0,
        'explainability_score': 85.0,
        'diversity_score': 85.0
    }
}

monitor_store.add_record(test_record)
print(f"   添加測試記錄...")

# 獲取記錄
records = monitor_store.get_records(time_window_minutes=5)
if records:
    latest_record = records[-1]
    timestamp_str = latest_record['timestamp']
    timestamp = datetime.fromisoformat(timestamp_str)
    
    print(f"   記錄時間戳: {timestamp_str}")
    print(f"   解析後時間: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   時區偏移: {timestamp.strftime('%z')}")
    
    # 驗證時區
    if '+08:00' in timestamp_str or timestamp.utcoffset() == timedelta(hours=8):
        print(f"   ✓ 時區設定正確 (UTC+8)")
    else:
        print(f"   ✗ 時區設定錯誤")
else:
    print(f"   ✗ 無法獲取記錄")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
