import os
import pandas as pd
import logging
from sqlalchemy import create_engine, text

# ---------------- CONFIG ----------------
DATA_DIR =r"C:/Users/talap/Vendor_Per_Data/data"
SQLITE_DB = "inventory.db"
TABLE_NAME = "vendor_sales_summary"
CHUNK_SIZE = 100000  # adjust for your RAM

REQUIRED_TABLES = {
    "purchases": "purchases.csv",
    "purchase_prices": "purchase_prices.csv",
    "sales": "sales.csv",
    "vendor_invoice": "vendor_invoice.csv"
}

# ---------------- LOGGING ----------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/vendor_summary_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

# ---------------- UTILS ----------------
def table_exists(engine, table_name):
    """Check if a table exists in SQLite."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
            {"t": table_name}
        ).fetchone()
    return result is not None

def ingest_csv_to_sqlite(csv_path, table_name, engine):
    """Read CSV in chunks and ingest into SQLite (replace table)."""
    logging.info(f"Ingesting {csv_path} into table {table_name}...")
    with engine.connect() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
    chunk_iter = pd.read_csv(csv_path, chunksize=CHUNK_SIZE)
    for i, chunk in enumerate(chunk_iter):
        if i == 0:
            chunk.to_sql(table_name, engine, if_exists='replace', index=False)
        else:
            chunk.to_sql(table_name, engine, if_exists='append', index=False)
        logging.info(f"  -> Loaded chunk {i+1} ({len(chunk)} rows)")
    logging.info(f"Completed ingestion for {table_name}.")

# ---------------- CLEANING ----------------
def clean_data(df):
    df['Volume'] = df['Volume'].astype(float)
    df.fillna(0, inplace=True)
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit'] / df['TotalSalesDollars']) * 100
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalesToPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']
    return df

# ---------------- SUMMARY QUERY ----------------
BASE_QUERY = """
WITH FreightSummary AS (
    SELECT VendorNumber, SUM(Freight) AS FreightCost
    FROM vendor_invoice
    GROUP BY VendorNumber
),
PurchaseSummary AS (
    SELECT
        p.VendorNumber, p.VendorName, p.Brand, p.Description,
        p.PurchasePrice, pp.Price AS ActualPrice, pp.Volume,
        SUM(p.Quantity) AS TotalPurchaseQuantity,
        SUM(p.Dollars) AS TotalPurchaseDollars
    FROM purchases p
    JOIN purchase_prices pp ON p.Brand = pp.Brand
    WHERE p.PurchasePrice > 0
    GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description,
             p.PurchasePrice, pp.Price, pp.Volume
),
SalesSummary AS (
    SELECT
        VendorNo, Brand,
        SUM(SalesDollars)  AS TotalSalesDollars,
        SUM(SalesPrice)    AS TotalSalesPrice,
        SUM(SalesQuantity) AS TotalSalesQuantity,
        SUM(ExciseTax)     AS TotalExciseTax
    FROM sales
    GROUP BY VendorNo, Brand
)
SELECT
    ps.VendorNumber, ps.VendorName, ps.Brand, ps.Description,
    ps.PurchasePrice, ps.ActualPrice, ps.Volume,
    ps.TotalPurchaseQuantity, ps.TotalPurchaseDollars,
    ss.TotalSalesQuantity, ss.TotalSalesDollars,
    ss.TotalSalesPrice, ss.TotalExciseTax, fs.FreightCost
FROM PurchaseSummary ps
LEFT JOIN SalesSummary ss
    ON ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
LEFT JOIN FreightSummary fs
    ON ps.VendorNumber = fs.VendorNumber
ORDER BY ps.TotalPurchaseDollars DESC
"""

def create_vendor_summary(engine):
    logging.info("Creating vendor summary...")
    offset = 0
    first_chunk = True
    while True:
        chunk_query = f"{BASE_QUERY} LIMIT {CHUNK_SIZE} OFFSET {offset}"
        chunk_df = pd.read_sql_query(chunk_query, engine)
        if chunk_df.empty:
            break
        chunk_df = clean_data(chunk_df)
        if first_chunk:
            chunk_df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
            first_chunk = False
        else:
            chunk_df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)
        logging.info(f"Inserted {len(chunk_df)} rows (offset {offset})")
        offset += CHUNK_SIZE
    logging.info("Vendor summary creation completed.")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    logging.info("Starting Vendor Summary Pipeline...")
    sqlite_engine = create_engine(f"sqlite:///{SQLITE_DB}")

    # Step 1: Ensure all required tables exist
    for table, csv_file in REQUIRED_TABLES.items():
        if not table_exists(sqlite_engine, table):
            csv_path = os.path.join(DATA_DIR, csv_file)
            if os.path.exists(csv_path):
                ingest_csv_to_sqlite(csv_path, table, sqlite_engine)
            else:
                logging.error(f"Missing CSV for table {table}: {csv_path}")
                raise FileNotFoundError(f"Missing CSV for table {table}: {csv_path}")

    # Step 2: Create vendor summary
    create_vendor_summary(sqlite_engine)

    logging.info("✅ Vendor Summary Pipeline Completed Successfully!")
    print("✅ Vendor Summary Pipeline Completed Successfully!")
    


