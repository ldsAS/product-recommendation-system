import json
from collections import Counter

def analyze_json_file(filepath, sample_size=1000):
    """分析 JSON 格式的資料檔案"""
    print(f"\n{'='*60}")
    print(f"分析檔案: {filepath}")
    print(f"{'='*60}")
    
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            try:
                record = json.loads(line.strip())
                records.append(record)
            except Exception as e:
                continue
    
    if not records:
        print("無法讀取資料")
        return None
    
    print(f"\n總樣本數: {len(records)}")
    
    # 取得所有欄位
    all_keys = set()
    for record in records:
        all_keys.update(record.keys())
    
    print(f"\n欄位數量: {len(all_keys)}")
    print(f"\n欄位列表:")
    for key in sorted(all_keys):
        print(f"  - {key}")
    
    # 顯示前 3 筆資料
    print(f"\n前 3 筆資料範例:")
    for i, record in enumerate(records[:3]):
        print(f"\n記錄 {i+1}:")
        for key, value in list(record.items())[:10]:  # 只顯示前 10 個欄位
            print(f"  {key}: {value}")
        if len(record) > 10:
            print(f"  ... (還有 {len(record)-10} 個欄位)")
    
    # 缺失值統計
    print(f"\n缺失值統計:")
    missing_counts = {}
    for key in all_keys:
        missing = sum(1 for r in records if key not in r or r[key] is None or r[key] == '')
        if missing > 0:
            missing_pct = (missing / len(records) * 100)
            missing_counts[key] = (missing, missing_pct)
    
    if missing_counts:
        for key, (count, pct) in sorted(missing_counts.items(), key=lambda x: x[1][0], reverse=True)[:10]:
            print(f"  {key}: {count} ({pct:.2f}%)")
    else:
        print("  無缺失值")
    
    return records

# 分析三個檔案
print("開始分析資料檔案...")

member_records = analyze_json_file('data/raw/member', sample_size=1000)
sales_records = analyze_json_file('data/raw/sales', sample_size=1000)
salesdetails_records = analyze_json_file('data/raw/salesdetails', sample_size=1000)

# 關聯性分析
print(f"\n{'='*60}")
print("資料關聯性分析")
print(f"{'='*60}")

if member_records and sales_records and salesdetails_records:
    print(f"\n會員資料 (member):")
    print(f"  - 樣本數: {len(member_records)}")
    print(f"  - 主鍵: id")
    print(f"  - 關鍵欄位: member_code, member_name, phone, total_consumption")
    
    print(f"\n銷售訂單 (sales):")
    print(f"  - 樣本數: {len(sales_records)}")
    print(f"  - 主鍵: id")
    print(f"  - 外鍵: member (關聯到 member.id)")
    print(f"  - 關鍵欄位: no, date, total, actualTotal, member")
    
    print(f"\n銷售明細 (salesdetails):")
    print(f"  - 樣本數: {len(salesdetails_records)}")
    print(f"  - 主鍵: id")
    print(f"  - 外鍵: sales_id (關聯到 sales.id)")
    print(f"  - 關鍵欄位: stock_id, stock_description, quantity, price")
    
    # 產品統計
    products = [r.get('stock_description') for r in salesdetails_records if r.get('stock_description')]
    if products:
        print(f"\n產品種類統計 (前 10 名):")
        product_counts = Counter(products).most_common(10)
        for product, count in product_counts:
            print(f"  - {product}: {count} 次")
    
    # 統計資訊
    print(f"\n統計摘要:")
    print(f"  - 不重複會員數: {len(set(r['id'] for r in member_records if 'id' in r))}")
    print(f"  - 不重複訂單數: {len(set(r['id'] for r in sales_records if 'id' in r))}")
    print(f"  - 不重複產品數: {len(set(r.get('stock_id') for r in salesdetails_records if r.get('stock_id')))}")

print("\n分析完成！")
