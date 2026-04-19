# Vendor Performance Analysis Pipeline

This repository contains an end-to-end Data Engineering and Exploratory Data Analysis (EDA) pipeline designed to analyze supply-chain profitability and vendor health.

## 🚀 Project Overview
The objective of this project is to merge and analyze disparate operational datasets (Purchases, Sales, Freight Invoices, and Inventory) to calculate essential business KPIs such as:
- **Gross Profit & Profit Margins**
- **Stock Turnover Ratios**
- **Sales-to-Purchase Ratios**

### 🧠 Technical Architecture & Highlights
- **ETL Optimization:** Overcame out-of-memory errors caused by massive 1.5GB+ flat files by implementing iterative chunk-loading (`chunksize=100000`).
- **SQL Aggregation:** Utilizes advanced SQLite Common Table Expressions (CTEs) to join and aggregate millions of rows efficiently outside of system RAM.
- **Automated Pipeline:** `Complete_Injetion_Cleaning_Script.py` autonomously handles database table creation, CSV appending, data scrubbing, and the final KPI calculations.
- **Power BI Connectivity:** The resulting `vendor_sales_summary` is visualized dynamically using an interactive Power BI dashboard.

---

## 🛠️ Project Setup & Execution Instructions

### 1. Environment Setup
It is highly recommended to use a Python Virtual Environment to manage dependencies.
```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/Scripts/activate  # On Windows

# Install required packages
pip install pandas sqlalchemy numpy matplotlib seaborn
```

### 2. Data Placement
To avoid GitHub file-size limits, the raw datasets are not included in this repository. 
Please create a `data/` directory in the root of the project and place the following raw files inside:
- `purchases.csv`
- `sales.csv`
- `vendor_invoice.csv`
- `purchase_prices.csv`

### 3. Running the ETL Pipeline
Execute the main ingestion and cleaning script. This script will read the raw CSVs in safe chunks, generate an `inventory.db` SQLite database, execute the CTEs, and create the final `vendor_sales_summary` table.
```bash
python Complete_Injetion_Cleaning_Script.py
```
*(Note: Check the `logs/` directory if you wish to monitor the ingestion progress.)*

### 4. Jupyter & EDA Analysis
Run the provided Jupyter Notebooks for in-depth exploratory data analysis and visualization.
```bash
jupyter notebook EDA.ipynb
jupyter notebook Vendor_Performance_Analysis.ipynb
```

### 5. Viewing the Dashboard
Open the `Vendor_Performance_Analysis.pbix` file using **Microsoft Power BI Desktop** to interact with the visualizations and top-vendor matrices.

---

## 📂 File Structure

- `Complete_Injetion_Cleaning_Script.py`: Main ETL, Data Formatting, and SQL Pipeline script.
- `sql_script.py`: Contains foundational SQLite connection workflows.
- `Main_Script.ipynb`: Demonstrates the chunking logic used to bypass Pandas MemoryErrors.
- `EDA.ipynb` & `Vendor_Performance_Analysis.ipynb`: Statistical analysis, distribution plotting, and metric explorations.
- `Vendor_Performance_Analysis.pbix`: The final Power BI Dashboard.
- `README.md`: Project documentation.
