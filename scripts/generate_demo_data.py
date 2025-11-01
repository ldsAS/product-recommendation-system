"""
生成示範資料用於測試和展示
適用於 Google Colab 或本地測試
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_demo_data(
    n_members=100,
    n_products=50,
    n_sales=500,
    output_dir='data/raw'
):
    """
    生成示範資料
    
    Args:
        n_members: 會員數量
        n_products: 產品數量
        n_sales: 訂單數量
        output_dir: 輸出目錄
    """
    print("🎲 開始生成示範資料...")
    print("=" * 60)
    
    # 設定隨機種子以確保可重現性
    np.random.seed(42)
    
    # 確保輸出目錄存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 生成會員資料
    print(f"📝 生成 {n_members} 筆會員資料...")
    members = pd.DataFrame({
        '會員編號': [f'CU{i:06d}' for i in range(1, n_members + 1)],
        '電話': [f'09{np.random.randint(10000000, 99999999)}' for _ in range(n_members)],
        '總消費金額': np.random.randint(1000, 100000, n_members),
        '累積紅利': np.random.randint(0, 5000, n_members),
        '註冊日期': [
            (datetime.now() - timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d')
            for _ in range(n_members)
        ]
    })
    
    # 2. 生成產品列表
    print(f"📦 生成 {n_products} 個產品...")
    products = [f'{i:05d}' for i in range(30000, 30000 + n_products)]
    
    # 3. 生成銷售訂單
    print(f"🛒 生成 {n_sales} 筆銷售訂單...")
    sales = pd.DataFrame({
        '訂單編號': [f'S{i:06d}' for i in range(1, n_sales + 1)],
        '會員編號': np.random.choice(members['會員編號'], n_sales),
        '訂單日期': [
            (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime('%Y-%m-%d')
            for _ in range(n_sales)
        ],
        '訂單金額': np.random.randint(100, 5000, n_sales),
        '門市代碼': np.random.choice(['STORE01', 'STORE02', 'STORE03'], n_sales)
    })
    
    # 4. 生成訂單明細
    print(f"📋 生成訂單明細...")
    salesdetails = []
    for order_id in sales['訂單編號']:
        # 每筆訂單包含 1-5 個產品
        n_items = np.random.randint(1, 6)
        for _ in range(n_items):
            unit_price = np.random.randint(50, 1000)
            quantity = np.random.randint(1, 5)
            salesdetails.append({
                '訂單編號': order_id,
                '產品編號': np.random.choice(products),
                '數量': quantity,
                '單價': unit_price,
                '小計': unit_price * quantity
            })
    
    salesdetails = pd.DataFrame(salesdetails)
    
    # 5. 儲存資料
    print(f"\n💾 儲存資料到 {output_dir}/...")
    members.to_csv(output_path / 'member', index=False)
    sales.to_csv(output_path / 'sales', index=False)
    salesdetails.to_csv(output_path / 'salesdetails', index=False)
    
    # 6. 顯示統計資訊
    print("\n" + "=" * 60)
    print("✅ 示範資料生成完成！")
    print("=" * 60)
    print(f"\n📊 資料統計:")
    print(f"  會員數量: {len(members):,}")
    print(f"  產品數量: {len(products):,}")
    print(f"  訂單數量: {len(sales):,}")
    print(f"  訂單明細: {len(salesdetails):,}")
    
    print(f"\n💰 消費統計:")
    print(f"  平均消費: ${members['總消費金額'].mean():,.0f}")
    print(f"  最高消費: ${members['總消費金額'].max():,}")
    print(f"  最低消費: ${members['總消費金額'].min():,}")
    
    print(f"\n🎁 紅利統計:")
    print(f"  平均紅利: {members['累積紅利'].mean():.0f} 點")
    print(f"  最高紅利: {members['累積紅利'].max()} 點")
    
    print(f"\n📦 訂單統計:")
    print(f"  平均訂單金額: ${sales['訂單金額'].mean():.0f}")
    print(f"  平均每單產品數: {len(salesdetails) / len(sales):.1f}")
    
    print("\n" + "=" * 60)
    print("📁 檔案位置:")
    print(f"  {output_path / 'member'}")
    print(f"  {output_path / 'sales'}")
    print(f"  {output_path / 'salesdetails'}")
    print("=" * 60)
    
    return members, sales, salesdetails


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='生成示範資料')
    parser.add_argument('--members', type=int, default=100, help='會員數量')
    parser.add_argument('--products', type=int, default=50, help='產品數量')
    parser.add_argument('--sales', type=int, default=500, help='訂單數量')
    parser.add_argument('--output', type=str, default='data/raw', help='輸出目錄')
    
    args = parser.parse_args()
    
    generate_demo_data(
        n_members=args.members,
        n_products=args.products,
        n_sales=args.sales,
        output_dir=args.output
    )


if __name__ == '__main__':
    main()
