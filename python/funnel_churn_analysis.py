"""
Project 2: Customer Booking Funnel & Churn Analysis
File: funnel_churn_analysis.py

What this script does:
  1. Generates a realistic 5-stage booking funnel dataset
  2. Performs end-to-end funnel analysis (drop-off rates per stage)
  3. Conducts cohort-based churn analysis (30/60/90-day retention)
  4. Exports all results to Google Sheets-ready CSVs
  5. Produces Matplotlib/Seaborn charts (saved as PNG)

Outputs (in ../data/ and ../sheets/):
  - funnel_events.csv        — raw event-level data
  - funnel_summary.csv       — stage-by-stage drop-off
  - cohort_retention.csv     — cohort retention matrix
  - churn_summary.csv        — 30/60/90-day retention rates
  - charts/funnel_chart.png
  - charts/retention_heatmap.png
  - charts/monthly_trend.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import datetime, timedelta
import random
import os

np.random.seed(7)
random.seed(7)

os.makedirs('../data',          exist_ok=True)
os.makedirs('../sheets',        exist_ok=True)
os.makedirs('../sheets/charts', exist_ok=True)

# ── 1. Generate funnel events dataset ────────────────────────────────────────
"""
5-stage pipeline: Search → Inquiry → Quote → Payment → Confirmation
Realistic drop-offs embedded — highest at Quote→Payment (the 38% story)
"""

STAGES = ['Search', 'Inquiry', 'Quote', 'Payment', 'Confirmation']

# Stage-to-stage conversion rates (realistic travel booking funnel)
STAGE_CONV = {
    'Search':       1.00,   # everyone starts here
    'Inquiry':      0.62,   # 38% drop after search
    'Quote':        0.71,   # of those who inquired
    'Payment':      0.62,   # highest drop — price shock (38% abandonment)
    'Confirmation': 0.88,   # of those who paid
}

n_users = 8000
start   = datetime(2023, 1, 1)
end     = datetime(2024, 12, 31)

def rand_date(s, e):
    return s + timedelta(days=random.randint(0, (e - s).days))

channels   = ['Organic Search', 'Paid Ad', 'Referral', 'Social Media', 'Direct']
chan_wts    = [0.35, 0.25, 0.15, 0.15, 0.10]
packages   = ['Beach Getaway', 'Hill Station', 'Heritage Tour', 'Adventure Trek',
              'Luxury Resort', 'Budget Backpacker', 'Honeymoon Special', 'Family Vacation']

records = []
for uid in range(1, n_users + 1):
    first_touch = rand_date(start, end)
    channel     = random.choices(channels, weights=chan_wts)[0]
    package     = random.choice(packages)
    user_id     = f'USR{uid:05d}'

    prev_conv = 1.0
    reached_stages = []
    for stage in STAGES:
        if stage == 'Search':
            reached_stages.append(stage)
        else:
            conv = STAGE_CONV[stage]
            # Seasonal effect: lower conversion Jul-Sep
            if first_touch.month in [7, 8, 9]:
                conv *= 0.88
            if random.random() < conv:
                reached_stages.append(stage)
            else:
                break  # dropped out

    last_stage   = reached_stages[-1]
    converted    = last_stage == 'Confirmation'
    event_ts     = first_touch + timedelta(hours=random.randint(0, 72))

    records.append({
        'user_id':         user_id,
        'first_touch_date': first_touch.strftime('%Y-%m-%d'),
        'event_date':       event_ts.strftime('%Y-%m-%d'),
        'channel':          channel,
        'package':          package,
        'last_stage':       last_stage,
        'converted':        int(converted),
        'acq_month':        first_touch.strftime('%Y-%m'),
        'acq_quarter':      'Q' + str((first_touch.month-1)//3+1) + '-' + str(first_touch.year),
    })

events_df = pd.DataFrame(records)
events_df.to_csv('../data/funnel_events.csv', index=False)
print(f"Funnel events: {len(events_df)} users")


# ── 2. Funnel drop-off analysis ───────────────────────────────────────────────
stage_counts = {}
for stage in STAGES:
    # Count users who reached at least this stage
    reached = events_df[events_df['last_stage'].isin(
        STAGES[STAGES.index(stage):]
    ) | (events_df['last_stage'] == stage)].shape[0]
    # Actually: count users whose last_stage index >= this stage
    idx = STAGES.index(stage)
    count = events_df[events_df['last_stage'].apply(
        lambda s: STAGES.index(s) >= idx
    )].shape[0]
    stage_counts[stage] = count

funnel_df = pd.DataFrame({
    'Stage':       STAGES,
    'Users':       [stage_counts[s] for s in STAGES],
})
funnel_df['Drop_Off']     = funnel_df['Users'].shift(1) - funnel_df['Users']
funnel_df['Drop_Off_Pct'] = (funnel_df['Drop_Off'] / funnel_df['Users'].shift(1) * 100).round(2)
funnel_df['Conv_From_Top']= (funnel_df['Users'] / funnel_df['Users'].iloc[0] * 100).round(2)
funnel_df.to_csv('../data/funnel_summary.csv', index=False)

print("\n── Funnel Summary ──")
print(funnel_df.to_string(index=False))
worst_stage = funnel_df.dropna().sort_values('Drop_Off_Pct', ascending=False).iloc[0]
print(f"\nHighest drop-off: {worst_stage['Stage']} — {worst_stage['Drop_Off_Pct']:.1f}% abandonment")


# ── 3. Cohort-based churn / retention analysis ────────────────────────────────
"""
For each acquisition cohort (month), track what % of users
came back / completed booking within 30, 60, 90 days.
We simulate 'activity' events post-first-touch.
"""

# Simulate return activity for converted users
activity_records = []
converted_users = events_df[events_df['converted'] == 1].copy()

for _, row in converted_users.iterrows():
    first = datetime.strptime(row['first_touch_date'], '%Y-%m-%d')
    # Simulate 1-3 follow-up interactions within 90 days
    n_interactions = random.randint(1, 3)
    for _ in range(n_interactions):
        days_later = random.choices(
            [random.randint(1,30), random.randint(31,60), random.randint(61,90)],
            weights=[0.5, 0.3, 0.2]
        )[0]
        activity_date = first + timedelta(days=days_later)
        if activity_date <= end:
            activity_records.append({
                'user_id':   row['user_id'],
                'acq_month': row['acq_month'],
                'acq_date':  row['first_touch_date'],
                'activity_date': activity_date.strftime('%Y-%m-%d'),
            })

activity_df = pd.DataFrame(activity_records)

# Calculate days since acquisition for each activity
activity_df['acq_date_dt']      = pd.to_datetime(activity_df['acq_date'])
activity_df['activity_date_dt'] = pd.to_datetime(activity_df['activity_date'])
activity_df['days_since_acq']   = (
    activity_df['activity_date_dt'] - activity_df['acq_date_dt']
).dt.days

# Cohort size per acquisition month
cohort_size = events_df.groupby('acq_month')['user_id'].count().reset_index()
cohort_size.columns = ['acq_month', 'cohort_size']

# Retention: % active within 30 / 60 / 90 days
def retention_rate(cohort, days):
    active = activity_df[
        (activity_df['acq_month'] == cohort) &
        (activity_df['days_since_acq'] <= days)
    ]['user_id'].nunique()
    size = cohort_size[cohort_size['acq_month'] == cohort]['cohort_size'].values
    if len(size) == 0 or size[0] == 0:
        return 0
    return round(active / size[0] * 100, 1)

cohorts = sorted(cohort_size['acq_month'].unique())
retention_rows = []
for c in cohorts:
    size = cohort_size[cohort_size['acq_month'] == c]['cohort_size'].values[0]
    retention_rows.append({
        'acq_month':    c,
        'cohort_size':  size,
        'ret_30d':      retention_rate(c, 30),
        'ret_60d':      retention_rate(c, 60),
        'ret_90d':      retention_rate(c, 90),
    })

retention_df = pd.DataFrame(retention_rows)
retention_df.to_csv('../data/cohort_retention.csv', index=False)

# Churn summary (overall)
churn_summary = pd.DataFrame({
    'Window':          ['30-day retention', '60-day retention', '90-day retention'],
    'Avg_Retention_Pct': [
        retention_df['ret_30d'].mean().round(1),
        retention_df['ret_60d'].mean().round(1),
        retention_df['ret_90d'].mean().round(1),
    ]
})
churn_summary['Avg_Churn_Pct'] = (100 - churn_summary['Avg_Retention_Pct']).round(1)
churn_summary.to_csv('../data/churn_summary.csv', index=False)

print("\n── Cohort Retention Summary ──")
print(churn_summary.to_string(index=False))

# High-risk cohorts (bottom 25% by 30-day retention)
high_risk = retention_df.nsmallest(int(len(retention_df)*0.25), 'ret_30d')
print(f"\nHigh-risk cohorts (lowest 30d retention): {list(high_risk['acq_month'])}")


# ── 4. Charts ─────────────────────────────────────────────────────────────────

sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})

# Chart 1 — Funnel waterfall
fig, ax = plt.subplots(figsize=(10, 5))
colors = ['#4361EE', '#4895EF', '#4CC9F0', '#F72585', '#B5179E']
bars = ax.barh(funnel_df['Stage'][::-1], funnel_df['Users'][::-1],
               color=colors[::-1], edgecolor='white', linewidth=1.2)
for bar, val in zip(bars, funnel_df['Users'][::-1]):
    ax.text(bar.get_width() + 40, bar.get_y() + bar.get_height()/2,
            f'{val:,}', va='center', fontsize=10, color='#333')
ax.set_xlabel('Users', fontsize=11)
ax.set_title('Booking Funnel — Stage Drop-off Analysis', fontsize=13, fontweight='bold', pad=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.spines[['top','right']].set_visible(False)

# Annotate worst drop-off
worst_idx = funnel_df.dropna()['Drop_Off_Pct'].idxmax()
worst     = funnel_df.loc[worst_idx]
stage_ypos = len(STAGES) - 1 - STAGES.index(worst['Stage'])
ax.annotate(
    f"⚠ {worst['Drop_Off_Pct']:.0f}% drop-off",
    xy=(funnel_df[funnel_df['Stage']==worst['Stage']]['Users'].values[0], stage_ypos),
    xytext=(funnel_df[funnel_df['Stage']==worst['Stage']]['Users'].values[0] + 300, stage_ypos + 0.35),
    fontsize=9, color='#F72585', fontweight='bold',
    arrowprops=dict(arrowstyle='->', color='#F72585', lw=1.2)
)
plt.tight_layout()
plt.savefig('../sheets/charts/funnel_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: funnel_chart.png")

# Chart 2 — Retention heatmap (cohort × window)
pivot = retention_df.set_index('acq_month')[['ret_30d', 'ret_60d', 'ret_90d']].tail(12)
pivot.columns = ['30-day', '60-day', '90-day']

fig, ax = plt.subplots(figsize=(8, 7))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd_r',
            linewidths=0.5, linecolor='white',
            cbar_kws={'label': 'Retention %'}, ax=ax, vmin=0, vmax=100)
ax.set_title('Cohort Retention Heatmap (last 12 months)', fontsize=13, fontweight='bold', pad=14)
ax.set_xlabel('Retention Window', fontsize=11)
ax.set_ylabel('Acquisition Month',  fontsize=11)
plt.tight_layout()
plt.savefig('../sheets/charts/retention_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: retention_heatmap.png")

# Chart 3 — Monthly conversion trend
monthly_conv = events_df.groupby('acq_month').agg(
    total=('user_id', 'count'),
    converted=('converted', 'sum')
).reset_index()
monthly_conv['conv_rate'] = (monthly_conv['converted'] / monthly_conv['total'] * 100).round(1)

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()
ax1.bar(monthly_conv['acq_month'], monthly_conv['total'],
        color='#ADB5BD', alpha=0.6, label='Total users')
ax2.plot(monthly_conv['acq_month'], monthly_conv['conv_rate'],
         color='#4361EE', marker='o', linewidth=2, markersize=5, label='Conversion %')

# Shade Q3 months
for i, m in enumerate(monthly_conv['acq_month']):
    if m[5:7] in ['07','08','09']:
        ax1.axvspan(i - 0.5, i + 0.5, color='#F72585', alpha=0.08)

ax1.set_xlabel('Acquisition Month', fontsize=11)
ax1.set_ylabel('Total Users', fontsize=11, color='#555')
ax2.set_ylabel('Conversion Rate (%)', fontsize=11, color='#4361EE')
ax2.tick_params(axis='y', labelcolor='#4361EE')
ax1.set_xticks(range(len(monthly_conv)))
ax1.set_xticklabels(monthly_conv['acq_month'], rotation=45, ha='right', fontsize=8)
ax1.set_title('Monthly User Volume & Conversion Rate (pink = Q3)', fontsize=13, fontweight='bold', pad=14)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9)
ax1.spines[['top']].set_visible(False)
ax2.spines[['top']].set_visible(False)
plt.tight_layout()
plt.savefig('../sheets/charts/monthly_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: monthly_trend.png")


# ── 5. Export Google Sheets-ready CSVs ────────────────────────────────────────
funnel_df.to_csv('../sheets/funnel_summary.csv',      index=False)
retention_df.to_csv('../sheets/cohort_retention.csv', index=False)
churn_summary.to_csv('../sheets/churn_summary.csv',   index=False)
monthly_conv.to_csv('../sheets/monthly_conversion.csv', index=False)

# Channel funnel performance
channel_perf = events_df.groupby('channel').agg(
    total=('user_id','count'),
    converted=('converted','sum')
).reset_index()
channel_perf['conv_rate'] = (channel_perf['converted']/channel_perf['total']*100).round(2)
channel_perf.sort_values('conv_rate', ascending=False).to_csv(
    '../sheets/channel_performance.csv', index=False)

print("\n── Google Sheets CSVs exported to ../sheets/ ──")
print("  funnel_summary.csv | cohort_retention.csv | churn_summary.csv")
print("  monthly_conversion.csv | channel_performance.csv")

# ── 6. Business recommendations ───────────────────────────────────────────────
print("\n" + "="*55)
print("  BUSINESS RECOMMENDATIONS")
print("="*55)
print(f"\n  1. PRICING TRANSPARENCY")
print(f"     Payment stage has the highest drop-off ({worst['Drop_Off_Pct']:.0f}%).")
print(f"     Show full cost breakdown earlier (at Quote stage)")
print(f"     to reduce price-shock abandonment at checkout.")
print(f"\n  2. FOLLOW-UP AUTOMATION")
avg_30 = retention_df['ret_30d'].mean()
print(f"     Avg 30-day retention is {avg_30:.1f}%.")
print(f"     Trigger automated follow-up emails at day 3, 7, 14")
print(f"     for users who reached Inquiry/Quote but didn't convert.")
print(f"\n  3. PACKAGE BUNDLING FOR Q3")
print(f"     Q3 conversion drops significantly (seasonal).")
print(f"     Introduce monsoon-specific bundles and limited-time")
print(f"     discounts in June to pull bookings earlier in the year.")
print("="*55)
