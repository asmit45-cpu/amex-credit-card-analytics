# Power BI Build Guide — AmEx Credit Card Analytics

This guide lets you build the Power BI report yourself in ~30-45 minutes. Building it yourself (rather than being handed a finished .pbix) is actually better for you: it's real practice on the exact skill your course is teaching, and you can speak to every step in an interview because you did it, not because a file was given to you.

All the data you need is in `data_for_import/` (4 CSV files). Power BI Desktop is required (free download from Microsoft).

---

## Step 1 — Import the data

1. Open Power BI Desktop → **Get Data** → **Text/CSV**
2. Import all 4 files, one at a time:
   - `dim_customer.csv`
   - `fact_monthly_spend.csv`
   - `fact_transactions.csv`
   - `customer_churn_risk_scores.csv`
3. Click **Transform Data** for each so they open in Power Query — check data types:
   - `date` columns → Date
   - `spend`, `amount`, `credit_limit` → Decimal Number
   - `is_fraud`, `is_online`, `is_international` → Whole Number
4. Click **Close & Apply**

## Step 2 — Build the data model (relationships)

Go to the **Model** view (left sidebar) and create these relationships (drag from one field to the other):

| From table | Field | To table | Field |
|---|---|---|---|
| fact_monthly_spend | customer_id | dim_customer | customer_id |
| fact_transactions | customer_id | dim_customer | customer_id |
| customer_churn_risk_scores | customer_id | dim_customer | customer_id |

All should be **Many-to-One**, direction **single** (dim_customer is the "one" side).

### Add a Date table (best practice — do this in every Power BI project)
Go to **Modeling** tab → **New Table**, paste:
```
DateTable = CALENDAR(DATE(2022,7,1), DATE(2024,6,30))
```
Then add columns:
```
Year = YEAR(DateTable[Date])
MonthName = FORMAT(DateTable[Date], "MMM-YYYY")
MonthNum = MONTH(DateTable[Date])
```
Relate `DateTable[Date]` → `fact_monthly_spend[date]` (one-to-many).

## Step 3 — Create these DAX measures

Go to **fact_monthly_spend** table → **New Measure**, add each of these one at a time:

```dax
Total Spend = SUM(fact_monthly_spend[spend])
```

```dax
Total Transactions = SUM(fact_monthly_spend[num_transactions])

```

```dax
Avg Spend per Customer =
DIVIDE([Total Spend], DISTINCTCOUNT(fact_monthly_spend[customer_id]))
```

```dax
YoY Spend Growth % =
VAR CurrentSpend = [Total Spend]
VAR PriorYearSpend = CALCULATE([Total Spend], SAMEPERIODLASTYEAR(DateTable[Date]))
RETURN DIVIDE(CurrentSpend - PriorYearSpend, PriorYearSpend)
```

Now go to **fact_transactions** table → **New Measure**:

```dax
Total Transactions Count = COUNTROWS(fact_transactions)
```

```dax
Fraud Count = SUM(fact_transactions[is_fraud])
```

```dax
Fraud Rate % = DIVIDE([Fraud Count], [Total Transactions Count])
```

```dax
Avg Transaction Amount = AVERAGE(fact_transactions[amount])
```

Now go to **customer_churn_risk_scores** table → **New Measure**:

```dax
High Risk Customers = CALCULATE(COUNTROWS(customer_churn_risk_scores), customer_churn_risk_scores[risk_flag] = "HIGH RISK")
```

```dax
Avg Risk Score = AVERAGE(customer_churn_risk_scores[risk_score])
```

## Step 4 — Build the report pages

### Page 1: Portfolio Overview
- **Card visual** (top strip, 4 cards): Total Spend, Total Transactions, Avg Spend per Customer, YoY Spend Growth %
- **Bar chart**: `dim_customer[card_type]` on axis, `[Avg Spend per Customer]` as value — insight: which tier is most valuable
- **Line chart**: `DateTable[MonthName]` on axis, `[Total Spend]` as value — shows the seasonality trend (use "sort by MonthNum" so months appear in order, not alphabetically)
- **Donut chart**: `fact_monthly_spend[category]` and `[Total Spend]` — spend mix by category
- **Slicer**: `dim_customer[city]` — lets you filter the whole page by city

### Page 2: Fraud Analytics
- **Card visuals**: Fraud Count, Fraud Rate %, Avg Transaction Amount
- **Bar chart**: `fact_transactions[merchant_category]` on axis, `[Fraud Rate %]` as value, sorted descending
- **Line/bar chart**: `fact_transactions[hour_of_day]` on axis, `[Fraud Rate %]` as value — shows the late-night fraud spike
- **Table**: filter `fact_transactions[is_fraud] = 1`, show transaction_id, customer_id, amount, merchant_category, hour_of_day — a working "fraud review list"

### Page 3: Customer Churn Risk
- **Card visuals**: High Risk Customers, Avg Risk Score
- **Table**: `customer_churn_risk_scores` fields (customer_id, card_type, momentum_pct, risk_score, risk_flag), sorted by risk_score descending, filtered to risk_flag = "HIGH RISK" — this is your "retention call list"
- **Scatter chart**: momentum_pct (X-axis) vs risk_score (Y-axis), colour by card_type — visually shows which customers are declining fastest

## Step 5 — Formatting polish (do this last)

- **Theme**: View tab → Themes → pick a blue-toned theme (matches AmEx branding), or set a custom theme with hex `#006FCF` and `#00175A`
- **Page names**: rename pages to "Portfolio Overview", "Fraud Analytics", "Churn Risk" (right-click the page tab)
- **Titles**: add a text box title to each page
- **Tooltips**: leave default page tooltips on for interactivity
- **Save**: File → Save As → `AmEx_Analytics_Report.pbix`

---

## What to say in an interview about this Power BI report

> "I built the data model with proper star-schema relationships between a customer dimension and three fact tables, added a dedicated Date table for time intelligence (which is best practice, not just using the date column directly), and wrote DAX measures rather than calculated columns wherever possible, since measures are more memory-efficient and recalculate dynamically with filters. The three pages map to the three business questions the project answers - portfolio health, fraud risk, and churn risk."

This line alone signals you understand *why* you're doing things a certain way, not just clicking buttons - that's what separates a strong Power BI answer from a weak one in interviews.
