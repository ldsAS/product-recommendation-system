import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processing.data_loader import DataLoader
from src.data_processing.data_cleaner import DataCleaner
from src.data_processing.feature_engineer import FeatureEngineer

def debug():
    print("Loading data individually...")
    loader = DataLoader()
    
    member_df = loader.load_members(max_rows=10000)
    print(f"Member DF: {member_df.shape}")
    if not member_df.empty:
        print(f"Member columns: {member_df.columns.tolist()}")
        print(f"Member ID sample: {member_df['id'].head().tolist() if 'id' in member_df.columns else 'No id'}")
    
    sales_df = loader.load_sales(max_rows=10000)
    print(f"Sales DF: {sales_df.shape}")
    if not sales_df.empty:
        print(f"Sales columns: {sales_df.columns.tolist()}")
        print(f"Sales Member ID (member col) sample: {sales_df['member'].head().tolist() if 'member' in sales_df.columns else 'No member col'}")
        print(f"Sales ID sample: {sales_df['id'].head().tolist() if 'id' in sales_df.columns else 'No id'}")

    details_df = loader.load_sales_details(max_rows=10000)
    print(f"Details DF: {details_df.shape}")
    if not details_df.empty:
        print(f"Details columns: {details_df.columns.tolist()}")
        print(f"Details Sales ID sample: {details_df['sales_id'].head().tolist() if 'sales_id' in details_df.columns else 'No sales_id'}")

    print("\nAttempting merge...")
    merged_df = loader.merge_data(max_rows=10000)
    print(f"Merged DF: {merged_df.shape}")

if __name__ == "__main__":
    debug()
