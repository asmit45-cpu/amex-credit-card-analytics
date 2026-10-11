"""
Credit Card Fraud Detection Model
-----------------------------------
Business problem: flag likely-fraudulent transactions in real time so they
can be held for verification, without blocking too many genuine transactions
(which hurts customer experience).

Key challenge: severe class imbalance (~1.2% fraud) - accuracy is a
meaningless metric here (a model that predicts "never fraud" would already
be 98.8% "accurate"). We evaluate using Precision, Recall, F1, and ROC-AUC/
PR-AUC instead, and use class_weight='balanced' to counter the imbalance.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score,
                              precision_recall_curve, average_precision_score, roc_curve)
from sklearn.preprocessing import LabelEncoder
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

txn = pd.read_csv('data/fact_transactions.csv')

# ---------------- Feature engineering ----------------
le_mcc = LabelEncoder()
le_card = LabelEncoder()
txn['merchant_category_enc'] = le_mcc.fit_transform(txn['merchant_category'])
txn['card_type_enc'] = le_card.fit_transform(txn['card_type'])

# is the transaction at an unusual hour (proxy flag, common fraud-analytics feature)
txn['is_odd_hour'] = txn['hour_of_day'].isin([0,1,2,3,4,23]).astype(int)

feature_cols = ['amount', 'hour_of_day', 'is_online', 'is_international',
                 'distance_from_home_km', 'merchant_category_enc', 'card_type_enc', 'is_odd_hour']
X = txn[feature_cols]
y = txn['is_fraud']

print(f"Dataset: {len(txn)} transactions, {y.sum()} fraud ({y.mean()*100:.2f}%)")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

clf = RandomForestClassifier(n_estimators=400, max_depth=10, min_samples_leaf=3,
                              random_state=42, class_weight='balanced', n_jobs=-1)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)
y_proba = clf.predict_proba(X_test)[:, 1]

print("\n--- Classification Report (default 0.5 threshold) ---")
print(classification_report(y_test, y_pred, target_names=['genuine', 'fraud'], digits=3))
print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_proba):.3f}")
print(f"PR-AUC (Average Precision): {average_precision_score(y_test, y_proba):.3f}")

# ---------------- Threshold tuning: business trade-off ----------------
# Lower threshold = catch more fraud (higher recall) but more false alarms (lower precision)
precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
# find threshold that gives recall >= 0.75 with best precision at that recall
target_recall = 0.75
idx = np.argmin(np.abs(recalls - target_recall))
chosen_threshold = thresholds[min(idx, len(thresholds)-1)]
print(f"\nBusiness-tuned threshold for ~{target_recall*100:.0f}% recall: {chosen_threshold:.3f}")
y_pred_tuned = (y_proba >= chosen_threshold).astype(int)
print("Tuned-threshold Classification Report:")
print(classification_report(y_test, y_pred_tuned, target_names=['genuine', 'fraud'], digits=3))

# ---------------- Feature importance ----------------
importances = pd.Series(clf.feature_importances_, index=feature_cols).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(importances.index, importances.values, color='#006FCF')
ax.set_title('Fraud Detection Model - Feature Importance', fontsize=13, fontweight='bold', color='#00175A')
fig.tight_layout()
fig.savefig('outputs/chart7_fraud_feature_importance.png', dpi=150)
plt.close(fig)

# ---------------- ROC curve ----------------
fpr, tpr, _ = roc_curve(y_test, y_proba)
fig, ax = plt.subplots(figsize=(7, 6))
ax.plot(fpr, tpr, color='#006FCF', linewidth=2, label=f'Model (AUC={roc_auc_score(y_test, y_proba):.3f})')
ax.plot([0,1],[0,1], color='grey', linestyle='--', label='Random guess')
ax.set_xlabel('False Positive Rate')
ax.set_ylabel('True Positive Rate')
ax.set_title('Fraud Detection - ROC Curve', fontsize=13, fontweight='bold', color='#00175A')
ax.legend()
fig.tight_layout()
fig.savefig('outputs/chart8_fraud_roc_curve.png', dpi=150)
plt.close(fig)

# ---------------- Business impact estimate ----------------
tn, fp, fn, tp = confusion_matrix(y_test, y_pred_tuned).ravel()
avg_fraud_amt = txn[txn['is_fraud']==1]['amount'].mean()
fraud_caught_value = tp * avg_fraud_amt
fraud_missed_value = fn * avg_fraud_amt
print(f"\nBusiness impact (test set, tuned threshold):")
print(f"  Fraud transactions caught: {tp} (~Rs {fraud_caught_value:,.0f} in prevented losses)")
print(f"  Fraud transactions missed: {fn} (~Rs {fraud_missed_value:,.0f} still at risk)")
print(f"  Genuine transactions incorrectly flagged: {fp} (customer friction to manage)")

txn[['transaction_id']].copy()
result_export = X_test.copy()
result_export['transaction_id'] = txn.loc[X_test.index, 'transaction_id'].values
result_export['actual_fraud'] = y_test.values
result_export['predicted_fraud_proba'] = y_proba
result_export['predicted_fraud_tuned'] = y_pred_tuned
result_export.to_csv('outputs/fraud_model_predictions.csv', index=False)
print("\nPredictions saved to outputs/fraud_model_predictions.csv")
