import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style='whitegrid', font='DejaVu Sans')
PALETTE = ['#006FCF', '#00175A', '#ED7D31', '#70AD47', '#A5A5A5', '#FFC000']  # AmEx blue-inspired palette

cust = pd.read_csv('data/dim_customer.csv')
spend = pd.read_csv('data/fact_monthly_spend.csv', parse_dates=['date'])
txn = pd.read_csv('data/fact_transactions.csv')

# ---------------- Chart 1: Monthly total spend trend ----------------
monthly = spend.groupby('date')['spend'].sum().reset_index()
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(monthly['date'], monthly['spend']/1e7, color='#006FCF', linewidth=2)
ax.fill_between(monthly['date'], monthly['spend']/1e7, alpha=0.15, color='#006FCF')
ax.set_title('Total Portfolio Spend by Month (Jul 2022 - Jun 2024)', fontsize=14, fontweight='bold', color='#00175A')
ax.set_ylabel('Spend (Rs Crores)')
fig.tight_layout()
fig.savefig('outputs/chart1_monthly_spend_trend.png', dpi=150)
plt.close(fig)

# ---------------- Chart 2: Spend by merchant category ----------------
cat_spend = spend.groupby('category')['spend'].sum().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(cat_spend.index[::-1], cat_spend.values[::-1]/1e7, color=PALETTE[0])
ax.set_title('Total Spend by Merchant Category', fontsize=14, fontweight='bold', color='#00175A')
ax.set_xlabel('Spend (Rs Crores)')
fig.tight_layout()
fig.savefig('outputs/chart2_category_spend.png', dpi=150)
plt.close(fig)

# ---------------- Chart 3: Card type portfolio mix + avg spend ----------------
card_summary = cust.merge(spend.groupby('customer_id')['spend'].sum().reset_index(), on='customer_id')
card_agg = card_summary.groupby('card_type').agg(customers=('customer_id','count'), avg_spend=('spend','mean')).reindex(['Green','Gold','Platinum','Centurion'])
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ax1.bar(card_agg.index, card_agg['customers'], color=PALETTE[1])
ax1.set_title('Number of Customers by Card Type', fontsize=12, fontweight='bold', color='#00175A')
ax2.bar(card_agg.index, card_agg['avg_spend']/1e5, color=PALETTE[2])
ax2.set_title('Avg Lifetime Spend by Card Type (Rs Lakh)', fontsize=12, fontweight='bold', color='#00175A')
fig.tight_layout()
fig.savefig('outputs/chart3_card_type_mix.png', dpi=150)
plt.close(fig)

# ---------------- Chart 4: Fraud rate by merchant category ----------------
fraud_cat = txn.groupby('merchant_category').agg(txns=('is_fraud','count'), frauds=('is_fraud','sum')).reset_index()
fraud_cat['fraud_rate'] = fraud_cat['frauds']/fraud_cat['txns']*100
fraud_cat = fraud_cat.sort_values('fraud_rate', ascending=False)
fig, ax = plt.subplots(figsize=(10, 5.5))
colors = ['#C00000' if v > 1.2 else '#ED7D31' for v in fraud_cat['fraud_rate']]
ax.barh(fraud_cat['merchant_category'][::-1], fraud_cat['fraud_rate'][::-1], color=colors[::-1])
ax.set_title('Fraud Rate % by Merchant Category', fontsize=14, fontweight='bold', color='#00175A')
ax.set_xlabel('Fraud Rate %')
fig.tight_layout()
fig.savefig('outputs/chart4_fraud_rate_by_category.png', dpi=150)
plt.close(fig)

# ---------------- Chart 5: Fraud rate by hour of day ----------------
fraud_hr = txn.groupby('hour_of_day').agg(txns=('is_fraud','count'), frauds=('is_fraud','sum')).reset_index()
fraud_hr['fraud_rate'] = fraud_hr['frauds']/fraud_hr['txns']*100
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(fraud_hr['hour_of_day'], fraud_hr['fraud_rate'], color='#006FCF')
ax.set_title('Fraud Rate % by Hour of Day', fontsize=14, fontweight='bold', color='#00175A')
ax.set_xlabel('Hour of Day (0-23)')
ax.set_ylabel('Fraud Rate %')
ax.set_xticks(range(0,24,2))
fig.tight_layout()
fig.savefig('outputs/chart5_fraud_by_hour.png', dpi=150)
plt.close(fig)

# ---------------- Chart 6: Customer momentum - top 10 declining ----------------
monthly_cust = spend.groupby(['customer_id','date'])['spend'].sum().reset_index()
recent = monthly_cust[monthly_cust['date']>='2024-01-01'].groupby('customer_id')['spend'].mean()
prior = monthly_cust[(monthly_cust['date']>='2023-07-01')&(monthly_cust['date']<'2024-01-01')].groupby('customer_id')['spend'].mean()
momentum = ((recent-prior)/prior*100).sort_values().head(10)
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.barh(momentum.index, momentum.values, color='#C00000')
ax.set_title('Top 10 Customers by Declining Spend Momentum', fontsize=13, fontweight='bold', color='#00175A')
ax.set_xlabel('Momentum % Change (Recent 6mo vs Prior 6mo)')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig('outputs/chart6_customer_momentum.png', dpi=150)
plt.close(fig)

print("6 EDA charts saved to outputs/")
