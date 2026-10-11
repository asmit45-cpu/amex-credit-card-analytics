import pandas as pd
import sqlite3

conn = sqlite3.connect('data/amex_analytics.db')

cust_df = pd.read_csv('data/dim_customer.csv')
spend_df = pd.read_csv('data/fact_monthly_spend.csv')
txn_df = pd.read_csv('data/fact_transactions.csv')
labels_df = pd.read_csv('data/customer_true_labels.csv')

cust_df.to_sql('dim_customer', conn, if_exists='replace', index=False)
spend_df.to_sql('fact_monthly_spend', conn, if_exists='replace', index=False)
txn_df.to_sql('fact_transactions', conn, if_exists='replace', index=False)
labels_df.to_sql('customer_true_labels', conn, if_exists='replace', index=False)

cur = conn.cursor()
cur.execute("CREATE INDEX IF NOT EXISTS idx_spend_cust ON fact_monthly_spend(customer_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_spend_date ON fact_monthly_spend(date)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_txn_cust ON fact_transactions(customer_id)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_txn_fraud ON fact_transactions(is_fraud)")
conn.commit()

print("Tables:", cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
for t in ['dim_customer', 'fact_monthly_spend', 'fact_transactions']:
    print(t, cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone())
conn.close()
