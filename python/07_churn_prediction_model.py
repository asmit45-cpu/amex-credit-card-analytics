"""
Customer Churn-Risk Prediction Model
--------------------------------------
Business problem: identify credit-card customers likely to reduce usage /
churn, early enough for the retention team to intervene (targeted offers,
fee waivers, relationship-manager outreach) before the customer is lost.

Approach: engineer momentum/trend features from each customer's spend
history, then train a classifier to flag "churn_risk" customers.
Validated against the known ground-truth labels baked into the synthetic
data generation.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

spend = pd.read_csv('data/fact_monthly_spend.csv', parse_dates=['date'])
cust = pd.read_csv('data/dim_customer.csv')
true_labels = pd.read_csv('data/customer_true_labels.csv')

monthly = spend.groupby(['customer_id', 'date'])['spend'].sum().reset_index()

# ---------------- Feature engineering (last 12 months of history) ----------------
features = []
for cid, grp in monthly.groupby('customer_id'):
    grp = grp.sort_values('date')
    g12 = grp[grp['date'] >= '2023-07-01'].reset_index(drop=True)  # last 12 months
    if len(g12) < 12:
        continue

    h1 = g12.iloc[0:6]['spend'].mean()
    h2 = g12.iloc[6:12]['spend'].mean()
    momentum_pct = (h2 - h1) / h1 * 100 if h1 > 0 else 0

    x = np.arange(12)
    y_vals = g12['spend'].values
    slope = np.polyfit(x, y_vals, 1)[0] / (y_vals.mean() + 1) * 100

    volatility = g12['spend'].std() / (g12['spend'].mean() + 1) * 100

    recent_vs_avg = (g12.iloc[9:12]['spend'].mean() / (g12['spend'].mean() + 1) - 1) * 100

    # number of "near-zero spend" months in the last 3 (dormancy signal)
    dormant_months = (g12.iloc[9:12]['spend'] < g12['spend'].mean() * 0.15).sum()

    features.append({
        'customer_id': cid,
        'momentum_pct': momentum_pct,
        'trend_slope_pct': slope,
        'volatility_pct': volatility,
        'recent_vs_avg_pct': recent_vs_avg,
        'dormant_months': dormant_months,
    })

feat_df = pd.DataFrame(features)
feat_df = feat_df.merge(true_labels, on='customer_id')
feat_df = feat_df.merge(cust[['customer_id', 'card_type', 'tenure_months', 'credit_limit']], on='customer_id')
feat_df['is_churn_risk'] = (feat_df['true_label'] == 'churn_risk').astype(int)

feature_cols = ['momentum_pct', 'trend_slope_pct', 'volatility_pct', 'recent_vs_avg_pct',
                 'dormant_months', 'tenure_months', 'credit_limit']
X = feat_df[feature_cols]
y = feat_df['is_churn_risk']

print(f"Dataset: {len(feat_df)} customers, {y.sum()} churn-risk ({y.mean()*100:.1f}%)")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

clf = RandomForestClassifier(n_estimators=400, max_depth=5, min_samples_leaf=3,
                              random_state=42, class_weight='balanced')
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:, 1]

print("\n--- Classification Report (test set) ---")
print(classification_report(y_test, y_pred, target_names=['stable/growth', 'churn_risk'], digits=3))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")

# ---------------- Score ALL customers ----------------
feat_df['risk_score'] = clf.predict_proba(X)[:, 1]
feat_df['risk_flag'] = np.where(feat_df['risk_score'] >= 0.5, 'HIGH RISK', 'OK')
result = feat_df[['customer_id', 'card_type', 'momentum_pct', 'dormant_months',
                   'risk_score', 'risk_flag', 'true_label']].sort_values('risk_score', ascending=False)
result.to_csv('outputs/customer_churn_risk_scores.csv', index=False)
print("\nTop 8 highest-risk customers (model output):")
print(result.head(8).to_string(index=False))

# ---------------- Feature importance ----------------
importances = pd.Series(clf.feature_importances_, index=feature_cols).sort_values()
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(importances.index, importances.values, color='#006FCF')
ax.set_title('Churn Risk Model - Feature Importance', fontsize=13, fontweight='bold', color='#00175A')
fig.tight_layout()
fig.savefig('outputs/chart9_churn_feature_importance.png', dpi=150)
plt.close(fig)

# ---------------- Business impact ----------------
at_risk_ids = result[result['risk_flag'] == 'HIGH RISK']['customer_id']
annual_spend_at_risk = spend[spend['customer_id'].isin(at_risk_ids) & (spend['year'] == 2024)]['spend'].sum() * 2  # annualize from H1
print(f"\nBusiness impact: {len(at_risk_ids)} customers flagged HIGH RISK, "
      f"representing an estimated Rs {annual_spend_at_risk:,.0f} of annualized spend at risk.")
print(f"AmEx earns interchange/interest revenue on this spend - retaining even 30% of at-risk "
      f"customers protects an estimated Rs {annual_spend_at_risk*0.3*0.02:,.0f} in annual revenue (illustrative, ~2% take rate).")
