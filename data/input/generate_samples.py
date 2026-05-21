# ============================================================
# data/input/generate_samples.py — Create sample datasets
# ============================================================
# Run this once to generate realistic sample CSV files
# for testing and for Fiverr/GitHub portfolio demos.
#   python data/input/generate_samples.py
# ============================================================

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent

random.seed(42)   # Fixed seed → same data every run (reproducible)

# ── Helper ───────────────────────────────────────────────────
def random_date(start_year=2023, end_year=2024):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


# ── Dataset 1: Sales Data ─────────────────────────────────────
print("Generating sales_data.csv ...")
regions    = ["North", "South", "East", "West", "Central"]
products   = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Service Pack"]
salesreps  = ["Alice Johnson", "Bob Smith", "Carol White", "David Brown", "Eva Martinez"]

sales_rows = []
for i in range(1, 301):
    sales_rows.append({
        "sale_id":      f"SL{i:04d}",
        "date":         random_date(),
        "region":       random.choice(regions),
        "product":      random.choice(products),
        "sales_rep":    random.choice(salesreps),
        "quantity":     random.randint(1, 50),
        "unit_price":   round(random.uniform(10.0, 500.0), 2),
        "discount_pct": random.choice([0, 5, 10, 15, 20]),
        "total_amount": None,   # Will calculate below
        "status":       random.choice(["Completed", "Completed", "Completed", "Pending", "Refunded"]),
    })

df_sales = pd.DataFrame(sales_rows)
df_sales["total_amount"] = (
    df_sales["quantity"] * df_sales["unit_price"] *
    (1 - df_sales["discount_pct"] / 100)
).round(2)

# Introduce some intentional messiness (to demo cleaning)
for idx in random.sample(range(300), 10):
    df_sales.loc[idx, "region"] = None          # Missing region
for idx in random.sample(range(300), 5):
    df_sales.loc[idx, "total_amount"] = None    # Missing total
# Add 3 duplicate rows
df_sales = pd.concat([df_sales, df_sales.iloc[[0, 1, 2]]], ignore_index=True)

df_sales.to_csv(OUTPUT_DIR / "sales_data.csv", index=False)
print(f"  → {len(df_sales)} rows saved to sales_data.csv")


# ── Dataset 2: Employee Records ───────────────────────────────
print("Generating employees.csv ...")
departments = ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations"]
titles      = {
    "Engineering": ["Junior Dev", "Senior Dev", "Lead Engineer", "Engineering Manager"],
    "Marketing":   ["Analyst", "Specialist", "Manager", "Director"],
    "Sales":       ["Sales Rep", "Account Manager", "Sales Lead", "VP Sales"],
    "HR":          ["HR Coordinator", "HR Specialist", "HR Manager"],
    "Finance":     ["Accountant", "Financial Analyst", "Finance Manager"],
    "Operations":  ["Operations Analyst", "Ops Manager", "COO"],
}

emp_rows = []
for i in range(1, 151):
    dept  = random.choice(departments)
    title = random.choice(titles[dept])
    base  = random.randint(35000, 120000)
    emp_rows.append({
        "employee_id":   f"EMP{i:04d}",
        "first_name":    random.choice(["James","Mary","John","Patricia","Robert","Jennifer",
                                        "Michael","Linda","William","Barbara","David","Susan"]),
        "last_name":     random.choice(["Smith","Johnson","Williams","Brown","Jones","Garcia",
                                        "Miller","Davis","Rodriguez","Martinez","Hernandez"]),
        "department":    dept,
        "job_title":     title,
        "salary":        base,
        "hire_date":     random_date(2018, 2023),
        "email":         None,   # Will fill below
        "performance":   random.choice(["Excellent", "Good", "Good", "Average", "Needs Improvement"]),
        "is_active":     random.choice([True, True, True, False]),
    })

df_emp = pd.DataFrame(emp_rows)
df_emp["email"] = (
    df_emp["first_name"].str.lower() + "." +
    df_emp["last_name"].str.lower() + "@company.com"
)

# Intentional messiness: some missing salaries and extra whitespace in names
for idx in random.sample(range(150), 8):
    df_emp.loc[idx, "salary"] = None
df_emp.loc[0, "first_name"] = "  James  "   # Extra whitespace

df_emp.to_csv(OUTPUT_DIR / "employees.csv", index=False)
print(f"  → {len(df_emp)} rows saved to employees.csv")


# ── Dataset 3: Monthly sales (for merge demo) ─────────────────
print("Generating monthly CSVs for merge demo ...")
months_dir = OUTPUT_DIR / "monthly_sales"
months_dir.mkdir(exist_ok=True)

for month_num in range(1, 4):   # Jan, Feb, Mar
    month_name = ["january", "february", "march"][month_num - 1]
    rows = []
    for i in range(1, 51):
        rows.append({
            "order_id":   f"ORD-{month_num:02d}-{i:03d}",
            "product":    random.choice(products),
            "region":     random.choice(regions),
            "quantity":   random.randint(1, 20),
            "revenue":    round(random.uniform(50, 2000), 2),
            "month":      month_name.title(),
        })
    pd.DataFrame(rows).to_csv(months_dir / f"sales_{month_name}.csv", index=False)
    print(f"  → 50 rows → monthly_sales/sales_{month_name}.csv")


# ── Dataset 4: Inventory ──────────────────────────────────────
print("Generating inventory.xlsx ...")
categories = ["Electronics", "Furniture", "Office Supplies", "Clothing", "Food & Beverage"]
inv_rows   = []
for i in range(1, 101):
    cat      = random.choice(categories)
    cost     = round(random.uniform(5, 500), 2)
    markup   = random.uniform(1.2, 2.5)
    inv_rows.append({
        "item_id":       f"INV{i:04d}",
        "item_name":     f"{cat} Item {i}",
        "category":      cat,
        "sku":           f"SKU-{random.randint(10000,99999)}",
        "stock_qty":     random.randint(0, 500),
        "reorder_point": random.randint(10, 50),
        "unit_cost":     cost,
        "unit_price":    round(cost * markup, 2),
        "supplier":      f"Supplier {random.randint(1, 10)}",
        "last_restocked": random_date(2024, 2024),
    })

pd.DataFrame(inv_rows).to_excel(OUTPUT_DIR / "inventory.xlsx", index=False)
print(f"  → 100 rows saved to inventory.xlsx")


print("\n✓ All sample datasets generated successfully!")
print(f"  Location: {OUTPUT_DIR.resolve()}")
