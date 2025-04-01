import os
import pandas as pd
import matplotlib.pyplot as plt

###############################################################################
# 0. Configuration: List of environments (URL + human-readable label)
###############################################################################
websites = [
    ("http://34.55.148.209",  "baseline"),
    ("http://34.122.196.51",  "replica"),
    ("http://34.133.176.226", "CPU/memory"),
    ("http://34.29.21.137",   "HPA"),
    ("http://34.16.90.199",   "istio"),
]


###############################################################################
# 1. Read each environment's results_{ip}_stats.csv for aggregated metrics
###############################################################################
summary_data = []

for url, label in websites:
    # Convert URL to a file-friendly string
    ip_str = url.split("//")[-1].rstrip("/")
    ip_str = ip_str.replace(".", "_")

    stats_filename = os.path.join('data', f"results_{ip_str}_stats.csv")
    
    if not os.path.exists(stats_filename):
        print(f"[Warning] File {stats_filename} not found. Skipping.")
        continue

    df_stats = pd.read_csv(stats_filename)

    # Filter the row corresponding to the aggregated metrics
    df_agg = df_stats[df_stats['Type'].isnull() & (df_stats['Name'] == 'Aggregated')]
    
    if df_agg.empty:
        print(f"[Warning] Aggregated row not found in {stats_filename}. Skipping.")
        continue

    # Extract the desired columns
    median_resp_time = df_agg['Median Response Time'].values[0]
    avg_resp_time    = df_agg['Average Response Time'].values[0]
    rps              = df_agg['Requests/s'].values[0]

    # Append to our summary array
    summary_data.append({
        'Label': label,
        'MedianResponseTime': median_resp_time,
        'AverageResponseTime': avg_resp_time,
        'RequestsPerSecond': rps
    })

# Convert summary data to a DataFrame
summary_df = pd.DataFrame(summary_data)
print("Summary DataFrame:\n", summary_df)

if summary_df.empty:
    print("[Error] No aggregated summary data was loaded. Exiting.")
    exit(0)

###############################################################################
# 2. Plot bar charts comparing aggregated metrics across environments
###############################################################################

# Bar chart: Median Response Time
plt.figure()
plt.bar(summary_df['Label'], summary_df['MedianResponseTime'], color='skyblue')
plt.title("Comparison of Median Response Time by Environment")
plt.xlabel("Environment")
plt.ylabel("Median Response Time (ms)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("median_response_time_comparison.png")
# plt.show()

# Bar chart: Average Response Time
plt.figure()
plt.bar(summary_df['Label'], summary_df['AverageResponseTime'], color='orange')
plt.title("Comparison of Average Response Time by Environment")
plt.xlabel("Environment")
plt.ylabel("Average Response Time (ms)")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("average_response_time_comparison.png")
# plt.show()

# Bar chart: Requests/s
plt.figure()
plt.bar(summary_df['Label'], summary_df['RequestsPerSecond'], color='green')
plt.title("Comparison of Requests/s by Environment")
plt.xlabel("Environment")
plt.ylabel("Requests/s")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig("requests_per_second_comparison.png")
# plt.show()


###############################################################################
# 3. Read each environment's results_{ip}_stats_history.csv, 
#    normalize timestamps, and store them for time-series plots
###############################################################################

all_histories = []
max_offset = 0.0  # Track the largest offset across all environments

for url, label in websites:
    ip_str = url.split("//")[-1].rstrip("/")
    ip_str = ip_str.replace(".", "_")

    history_filename = os.path.join('data', f"results_{ip_str}_stats_history.csv")

    if not os.path.exists(history_filename):
        print(f"[Warning] File {history_filename} not found. Skipping.")
        continue

    df_hist = pd.read_csv(history_filename)
    
    # Keep only the aggregated rows
    df_hist_agg = df_hist[(df_hist['Type'].isnull()) & (df_hist['Name'] == 'Aggregated')]
    if df_hist_agg.empty:
        print(f"[Warning] No aggregated rows found in {history_filename}. Skipping.")
        continue

    # Convert Timestamp (epoch) to datetime
    df_hist_agg['Timestamp'] = pd.to_datetime(df_hist_agg['Timestamp'], unit='s', errors='coerce')
    df_hist_agg.sort_values(by='Timestamp', inplace=True)

    # Normalize so the first row starts at 0s
    start_time = df_hist_agg['Timestamp'].iloc[0]
    df_hist_agg['TimeOffset'] = (df_hist_agg['Timestamp'] - start_time).dt.total_seconds()

    # Update global max_offset
    current_max = df_hist_agg['TimeOffset'].max()
    if current_max > max_offset:
        max_offset = current_max

    all_histories.append((label, df_hist_agg))

if not all_histories:
    print("[Warning] No time-series (history) data. Exiting.")
    exit(0)

###############################################################################
# 4. Example: Plot multiple metrics (Requests/s, Failures/s, Avg Response Time)
#    vs TimeOffset in separate figures
###############################################################################

# We can define the metrics we want to plot:
metrics_to_plot = {
    "Requests/s": {
        "title":  "Requests/s Over Time (Each Env from 0s)",
        "ylabel": "Requests/s",
        "filename": "requests_over_time.png"
    },
    "Failures/s": {
        "title":  "Failures/s Over Time (Each Env from 0s)",
        "ylabel": "Failures/s",
        "filename": "failures_over_time.png"
    },
    # For average response time, the column often is "Total Average Response Time" in stats_history.
    # If your CSV uses a different column for real-time average response time, modify accordingly.
    "Total Average Response Time": {
        "title":  "Average Response Time Over Time",
        "ylabel": "Response Time (ms)",
        "filename": "avg_resp_time_over_time.png"
    }
}

for metric_column, info in metrics_to_plot.items():
    plt.figure()
    for label, df_h in all_histories:
        if metric_column not in df_h.columns:
            # If the column doesn't exist, skip plotting for this environment
            print(f"[Warning] Column '{metric_column}' not in {label}'s data, skipping line.")
            continue

        plt.plot(df_h['TimeOffset'], df_h[metric_column], label=label)

    # If you know each test runs about 60s, you could do: plt.xlim([0,60])
    plt.xlim([0, max_offset])
    plt.title(info["title"])
    plt.xlabel("Time Since Start (seconds)")
    plt.ylabel(info["ylabel"])
    plt.legend()
    plt.tight_layout()
    plt.savefig(info["filename"])
    # plt.show()

print("[Info] Plots generated and saved successfully.")