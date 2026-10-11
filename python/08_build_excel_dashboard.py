import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule

ARIAL = 'Arial'
NAVY = '00175A'   # AmEx deep blue
BLUE = '006FCF'   # AmEx signature blue
hdr_font = Font(name=ARIAL, bold=True, color='FFFFFF', size=10)
hdr_fill = PatternFill('solid', fgColor=NAVY)
title_font = Font(name=ARIAL, bold=True, size=18, color='FFFFFF')
sub_font = Font(name=ARIAL, italic=True, size=10, color='555555')
normal_font = Font(name=ARIAL, size=10)
bold_font = Font(name=ARIAL, bold=True, size=10)
thin = Side(style='thin', color='CCCCCC')
border = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()

# ============================================================
# SHEET: Data (raw-ish supporting tables that formulas reference)
# ============================================================
wsd = wb.active
wsd.title = 'Data'
wsd.sheet_view.showGridLines = False
wsd.sheet_properties.tabColor = '808080'
wsd['A1'] = 'Supporting Data (referenced by formulas on other sheets)'
wsd['A1'].font = Font(name=ARIAL, bold=True, size=12, color=NAVY)

cust_summary = pd.read_csv('data/customer_summary.csv')[['customer_id', 'card_type', 'city', 'tenure_months', 'total_spend']]
wsd['A3'] = 'Customer Summary (24-month total spend per customer)'
wsd['A3'].font = bold_font
cs_hdr_row = 4
for j, col in enumerate(cust_summary.columns, start=1):
    c = wsd.cell(row=cs_hdr_row, column=j, value=col)
    c.font = hdr_font; c.fill = hdr_fill
for i, row in cust_summary.iterrows():
    r = cs_hdr_row + 1 + i
    for j, val in enumerate(row, start=1):
        wsd.cell(row=r, column=j, value=val)
cs_last_row = cs_hdr_row + len(cust_summary)

fraud_cat = pd.read_csv('data/fraud_by_category.csv')
fraud_start_col = 8  # column H
wsd.cell(row=3, column=fraud_start_col, value='Fraud by Merchant Category').font = bold_font
fc_hdr_row = 4
for j, col in enumerate(fraud_cat.columns, start=fraud_start_col):
    c = wsd.cell(row=fc_hdr_row, column=j, value=col)
    c.font = hdr_font; c.fill = hdr_fill
for i, row in fraud_cat.iterrows():
    r = fc_hdr_row + 1 + i
    for j, val in enumerate(row, start=fraud_start_col):
        wsd.cell(row=r, column=j, value=val)
fc_last_row = fc_hdr_row + len(fraud_cat)

for col_letter in ['A','B','C','D','E','H','I','J','K']:
    wsd.column_dimensions[col_letter].width = 15

# ============================================================
# SHEET: Executive Summary
# ============================================================
ws = wb.create_sheet('Executive Summary')
wb.move_sheet('Executive Summary', offset=-1)
ws.sheet_view.showGridLines = False
ws.sheet_properties.tabColor = NAVY

for col in range(2, 10):
    for row in (2, 3):
        ws.cell(row=row, column=col).fill = PatternFill('solid', fgColor=NAVY)
ws['B2'] = 'AmEx Credit Card Customer Analytics - Fraud Risk, Churn & Spend Behaviour'
ws['B2'].font = title_font
ws.merge_cells('B2:I2')
ws['B3'] = 'SQL + Python (Machine Learning) + Excel + Power BI | 1,500 customers | 24 months spend history | 60,000 transactions'
ws['B3'].font = Font(name=ARIAL, italic=True, size=10, color='D9E2F3')
ws.merge_cells('B3:I3')
ws.row_dimensions[2].height = 32
ws.row_dimensions[3].height = 20

ws['B5'] = 'Business Problem'
ws['B5'].font = Font(name=ARIAL, bold=True, size=12, color=NAVY)
ws['B6'] = ("A credit-card issuer needs to: (1) understand its portfolio mix and spend behaviour across card tiers "
    "and merchant categories, (2) flag fraudulent transactions in real time without over-blocking genuine customers, "
    "and (3) identify customers at risk of reducing card usage early enough for the retention team to act.")
ws['B6'].font = normal_font
ws['B6'].alignment = Alignment(wrap_text=True, vertical='top')
ws.merge_cells('B6:I6')
ws.row_dimensions[6].height = 45

ws['B8'] = 'Approach'
ws['B8'].font = Font(name=ARIAL, bold=True, size=12, color=NAVY)
approach_items = [
    'SQL (SQLite): 7 business queries - customer segmentation, Pareto/RFM-style analysis, fraud-rate breakdowns, window functions',
    'Python (pandas): data cleaning, feature engineering, seasonality analysis',
    'Python (scikit-learn): Random Forest fraud-detection classifier (with precision/recall threshold tuning for class imbalance) and Random Forest churn-risk classifier',
    'Excel: this dashboard - summary sheets use live formulas (SUMIF/COUNTIF/AVERAGEIF) against the Data sheet, not hardcoded numbers',
    'Power BI: interactive drill-down report (data model + DAX measures provided - see companion build guide)',
]
r = 9
for item in approach_items:
    ws.cell(row=r, column=2, value='•  ' + item).font = normal_font
    ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True)
    ws.merge_cells(f'B{r}:I{r}')
    ws.row_dimensions[r].height = 18
    r += 1

r += 1
ws.cell(row=r, column=2, value='Key Findings').font = Font(name=ARIAL, bold=True, size=12, color=NAVY)
r += 1
findings = [
    ('Portfolio', 'Centurion cardholders are only ~6% of customers but average several times a Green cardholder in lifetime spend - confirming the top-tier segment as the highest-value group.'),
    ('Spend Mix', 'Travel and Online Shopping together drive over 40% of total portfolio spend - the two categories most worth prioritising for rewards/cashback partnerships.'),
    ('Fraud', 'Healthcare and Jewellery merchant categories show the highest fraud rates; the model catches most fraud value at a tuned threshold with very few false alarms on the test set.'),
    ('Churn Risk', '180 customers (12% of the portfolio) are flagged high-risk by the churn model, representing a significant share of annualised spend at risk.'),
    ('Model Note', 'Both ML models show very clean separation on this synthetic dataset (near-perfect test scores) - a known limitation flagged in the README; production data would need re-validation with noisier, real-world signal.'),
]
for tag, text in findings:
    ws.cell(row=r, column=2, value=tag).font = Font(name=ARIAL, bold=True, size=10, color=BLUE)
    ws.cell(row=r, column=3, value=text).font = normal_font
    ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical='top')
    ws.merge_cells(f'C{r}:I{r}')
    ws.row_dimensions[r].height = 34
    r += 1

r += 1
ws.cell(row=r, column=2, value='Business Recommendation').font = Font(name=ARIAL, bold=True, size=12, color=NAVY)
r += 1
ws.cell(row=r, column=2, value=(
    "Deploy the fraud model at the tuned threshold for real-time transaction scoring on Healthcare and Jewellery "
    "categories first, where fraud rates are highest. Launch a retention program for the flagged churn-risk customers "
    "(priority to Platinum/Centurion tiers given their high lifetime value) - even a partial save-rate protects "
    "meaningful annual interchange/interest revenue from this cohort."
)).font = normal_font
ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True, vertical='top')
ws.merge_cells(f'B{r}:I{r}')
ws.row_dimensions[r].height = 55

ws.column_dimensions['A'].width = 3
ws.column_dimensions['B'].width = 16
for col in ['C','D','E','F','G','H','I']:
    ws.column_dimensions[col].width = 13

# ============================================================
# SHEET: Portfolio Performance (FORMULA-DRIVEN)
# ============================================================
ws2 = wb.create_sheet('Portfolio Performance')
ws2.sheet_view.showGridLines = False
ws2.sheet_properties.tabColor = BLUE
ws2['B2'] = 'Portfolio Performance by Card Type'
ws2['B2'].font = Font(name=ARIAL, bold=True, size=16, color=NAVY)
ws2.merge_cells('B2:F2')
ws2['B3'] = "Live formulas: COUNTIF / SUMIF against the 'Data' sheet's Customer Summary table (1,500 rows)."
ws2['B3'].font = sub_font
ws2.merge_cells('B3:F3')

card_types_list = ['Centurion', 'Platinum', 'Gold', 'Green']
headers = ['Card Type', 'Customers', 'Total Spend (Rs)', 'Avg Lifetime Spend/Customer (Rs)']
hdr_row = 5
for j, h in enumerate(headers, start=2):
    c = ws2.cell(row=hdr_row, column=j, value=h)
    c.font = hdr_font; c.fill = hdr_fill; c.border = border
    c.alignment = Alignment(horizontal='center', wrap_text=True)
ws2.row_dimensions[hdr_row].height = 30

data_range_card = f"Data!$B${cs_hdr_row+1}:$B${cs_last_row}"
data_range_spend = f"Data!$E${cs_hdr_row+1}:$E${cs_last_row}"
for i, card in enumerate(card_types_list):
    row = hdr_row + 1 + i
    ws2.cell(row=row, column=2, value=card).font = normal_font
    ws2.cell(row=row, column=3, value=f"=COUNTIF({data_range_card},B{row})").font = normal_font
    ws2.cell(row=row, column=4, value=f"=SUMIF({data_range_card},B{row},{data_range_spend})")
    ws2.cell(row=row, column=4).number_format = '#,##0'
    ws2.cell(row=row, column=5, value=f"=D{row}/C{row}")
    ws2.cell(row=row, column=5).number_format = '#,##0'
    for cc in range(2, 6):
        ws2.cell(row=row, column=cc).font = normal_font
        ws2.cell(row=row, column=cc).border = border
card_last_row = hdr_row + len(card_types_list)

tot_row = card_last_row + 1
ws2.cell(row=tot_row, column=2, value='Total').font = bold_font
ws2.cell(row=tot_row, column=3, value=f"=SUM(C{hdr_row+1}:C{card_last_row})").font = bold_font
ws2.cell(row=tot_row, column=4, value=f"=SUM(D{hdr_row+1}:D{card_last_row})").font = bold_font
ws2.cell(row=tot_row, column=4).number_format = '#,##0'
for cc in (2,3,4):
    ws2.cell(row=tot_row, column=cc).border = border

chart = BarChart()
chart.title = 'Avg Lifetime Spend per Customer by Card Type (Rs)'
data = Reference(ws2, min_col=5, min_row=hdr_row, max_row=card_last_row)
cats = Reference(ws2, min_col=2, min_row=hdr_row+1, max_row=card_last_row)
chart.add_data(data, titles_from_data=True)
chart.set_categories(cats)
chart.width = 18; chart.height = 10
ws2.add_chart(chart, 'B13')

ws2.column_dimensions['A'].width = 3
ws2.column_dimensions['B'].width = 14
for col in ['C','D','E']:
    ws2.column_dimensions[col].width = 22

# ============================================================
# SHEET: Fraud Risk Summary (FORMULA-DRIVEN)
# ============================================================
ws3 = wb.create_sheet('Fraud Risk Summary')
ws3.sheet_view.showGridLines = False
ws3.sheet_properties.tabColor = 'C00000'
ws3['B2'] = 'Fraud Rate by Merchant Category'
ws3['B2'].font = Font(name=ARIAL, bold=True, size=16, color=NAVY)
ws3.merge_cells('B2:E2')
ws3['B3'] = "Live formulas referencing the 'Data' sheet's Fraud-by-Category table."
ws3['B3'].font = sub_font
ws3.merge_cells('B3:E3')

fcat_col = get_column_letter(fraud_start_col)
ftot_col = get_column_letter(fraud_start_col+1)
ffraud_col = get_column_letter(fraud_start_col+2)

headers3 = ['Merchant Category', 'Total Txns', 'Fraud Txns', 'Fraud Rate %']
hdr_row3 = 5
for j, h in enumerate(headers3, start=2):
    c = ws3.cell(row=hdr_row3, column=j, value=h)
    c.font = hdr_font; c.fill = hdr_fill; c.border = border
    c.alignment = Alignment(horizontal='center')
for i in range(len(fraud_cat)):
    row = hdr_row3 + 1 + i
    src_row = fc_hdr_row + 1 + i
    ws3.cell(row=row, column=2, value=f"=Data!{fcat_col}{src_row}").font = normal_font
    ws3.cell(row=row, column=3, value=f"=Data!{ftot_col}{src_row}").font = normal_font
    ws3.cell(row=row, column=4, value=f"=Data!{ffraud_col}{src_row}").font = normal_font
    ws3.cell(row=row, column=5, value=f"=D{row}/C{row}*100")
    ws3.cell(row=row, column=5).number_format = '0.00"%"'
    for cc in range(2, 6):
        ws3.cell(row=row, column=cc).border = border
last_r3 = hdr_row3 + len(fraud_cat)

rule = ColorScaleRule(start_type='min', start_color='63BE7B', mid_type='percentile', mid_value=50, mid_color='FFEB84', end_type='max', end_color='F8696B')
ws3.conditional_formatting.add(f'E{hdr_row3+1}:E{last_r3}', rule)

maxrow3 = last_r3 + 2
ws3.cell(row=maxrow3, column=2, value='Highest-risk category:').font = bold_font
ws3.cell(row=maxrow3, column=3, value=f"=INDEX(B{hdr_row3+1}:B{last_r3},MATCH(MAX(E{hdr_row3+1}:E{last_r3}),E{hdr_row3+1}:E{last_r3},0))").font = bold_font

chart3 = BarChart()
chart3.type = 'bar'
chart3.title = 'Fraud Rate % by Merchant Category'
data3 = Reference(ws3, min_col=5, min_row=hdr_row3, max_row=last_r3)
cats3 = Reference(ws3, min_col=2, min_row=hdr_row3+1, max_row=last_r3)
chart3.add_data(data3, titles_from_data=True)
chart3.set_categories(cats3)
chart3.width = 20; chart3.height = 12
ws3.add_chart(chart3, f'B{maxrow3+2}')

ws3.column_dimensions['A'].width = 3
ws3.column_dimensions['B'].width = 20
for col in ['C','D','E']:
    ws3.column_dimensions[col].width = 14

# ============================================================
# SHEET: Churn Risk Register
# ============================================================
ws4 = wb.create_sheet('Churn Risk Register')
ws4.sheet_view.showGridLines = False
ws4.sheet_properties.tabColor = 'ED7D31'
ws4['B2'] = 'Customer Churn-Risk Register (Model Output, Top 30)'
ws4['B2'].font = Font(name=ARIAL, bold=True, size=16, color=NAVY)
ws4.merge_cells('B2:G2')
ws4['B3'] = 'Source: Random Forest classifier scored on all 1,500 customers; risk_score >= 0.5 flagged HIGH RISK.'
ws4['B3'].font = sub_font
ws4.merge_cells('B3:G3')

risk_df = pd.read_csv('outputs/customer_churn_risk_scores.csv').head(30)
headers4 = ['Customer ID', 'Card Type', 'Momentum %', 'Dormant Months', 'Risk Score', 'Flag']
hdr_row4 = 5
for j, h in enumerate(headers4, start=2):
    c = ws4.cell(row=hdr_row4, column=j, value=h)
    c.font = hdr_font; c.fill = hdr_fill; c.border = border
    c.alignment = Alignment(horizontal='center', wrap_text=True)
ws4.row_dimensions[hdr_row4].height = 26
for i, row in risk_df.iterrows():
    r = hdr_row4 + 1 + i
    ws4.cell(row=r, column=2, value=row['customer_id']).font = normal_font
    ws4.cell(row=r, column=3, value=row['card_type']).font = normal_font
    ws4.cell(row=r, column=4, value=round(row['momentum_pct'], 1)).font = normal_font
    ws4.cell(row=r, column=5, value=int(row['dormant_months'])).font = normal_font
    ws4.cell(row=r, column=6, value=round(row['risk_score'], 3)).font = normal_font
    flag_cell = ws4.cell(row=r, column=7, value=row['risk_flag'])
    flag_cell.font = Font(name=ARIAL, bold=True, size=10, color='C00000' if row['risk_flag']=='HIGH RISK' else '548225')
    for cc in range(2, 8):
        ws4.cell(row=r, column=cc).border = border
last_r4 = hdr_row4 + len(risk_df)

countrow = last_r4 + 2
ws4.cell(row=countrow, column=2, value='Total flagged HIGH RISK (this list):').font = bold_font
ws4.cell(row=countrow, column=3, value=f'=COUNTIF(G{hdr_row4+1}:G{last_r4},"HIGH RISK")').font = bold_font

ws4.column_dimensions['A'].width = 3
ws4.column_dimensions['B'].width = 14
ws4.column_dimensions['C'].width = 12
for col in ['D','E','F','G']:
    ws4.column_dimensions[col].width = 15

wb.save('outputs/AmEx_Analytics_Dashboard.xlsx')
print("Excel dashboard saved with live formulas.")
