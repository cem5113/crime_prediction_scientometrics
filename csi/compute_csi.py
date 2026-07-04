# CONCEPTUAL SHIFT INDEX (CSI) - Crime Prediction Literature
# Author: Cem Eroglu
# Purpose:
#   1. Compare pre-AI and post-AI keyword structures
#   2. Standardize equivalent terms across periods
#   3. Compute the Conceptual Shift Index (CSI) between the two periods
#   4. Export CSI tables and figures

import pandas as pd
from pathlib import Path

# Paths
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

PRE_FILE = DATA_DIR / "pre_ai.xlsx"
POST_FILE = DATA_DIR / "post_ai.xlsx"
OUTPUT_FILE = OUTPUT_DIR / "CSI_results.xlsx"

# Read Excel files
pre = pd.read_excel(PRE_FILE)
post = pd.read_excel(POST_FILE)

# Fix column names
pre.columns = ["term", "freq"]
post.columns = ["term", "freq"]

# Clean terms
pre["term"] = pre["term"].astype(str).str.lower().str.strip()
post["term"] = post["term"].astype(str).str.lower().str.strip()

# Synonym mapping
mapping = {
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "dl": "deep learning"
}

pre["term"] = pre["term"].replace(mapping)
post["term"] = post["term"].replace(mapping)

# Aggregate duplicate terms
pre = pre.groupby("term", as_index=False)["freq"].sum()
post = post.groupby("term", as_index=False)["freq"].sum()

# Combine terms
all_terms = set(pre["term"]).union(set(post["term"]))
df = pd.DataFrame({"term": sorted(all_terms)})

# Merge datasets
df = df.merge(pre, on="term", how="left").rename(columns={"freq": "f_pre"})
df = df.merge(post, on="term", how="left").rename(columns={"freq": "f_post"})
df = df.fillna(0)

# Normalize frequencies
df["p_pre"] = df["f_pre"] / df["f_pre"].sum()
df["p_post"] = df["f_post"] / df["f_post"].sum()

# Calculate CSI
df["diff"] = abs(df["p_post"] - df["p_pre"])
CSI = 0.5 * df["diff"].sum()

print("CSI value:", round(CSI, 3))

# ============================================================
# Sensitivity Analysis
# ============================================================

thresholds = [1, 2, 3, 5]
sensitivity_results = []

for t in thresholds:

    # Apply minimum frequency threshold
    pre_t = pre[pre["freq"] >= t].copy()
    post_t = post[post["freq"] >= t].copy()

    # Combine terms
    all_terms_t = set(pre_t["term"]).union(set(post_t["term"]))
    df_t = pd.DataFrame({"term": sorted(all_terms_t)})

    # Merge
    df_t = df_t.merge(pre_t, on="term", how="left").rename(columns={"freq": "f_pre"})
    df_t = df_t.merge(post_t, on="term", how="left").rename(columns={"freq": "f_post"})
    df_t = df_t.fillna(0)

    # Normalize
    df_t["p_pre"] = df_t["f_pre"] / df_t["f_pre"].sum()
    df_t["p_post"] = df_t["f_post"] / df_t["f_post"].sum()

    # CSI
    df_t["diff"] = abs(df_t["p_post"] - df_t["p_pre"])
    csi_t = 0.5 * df_t["diff"].sum()

    sensitivity_results.append({
        "Minimum keyword frequency":
            "All keywords" if t == 1 else f"≥{t}",
        "CSI": round(csi_t, 3),
        "Retained terms": len(df_t),
        "Pre-AI total frequency": int(pre_t["freq"].sum()),
        "Post-AI total frequency": int(post_t["freq"].sum())
    })

sensitivity_df = pd.DataFrame(sensitivity_results)

print("\nSensitivity Analysis")
print(sensitivity_df)

# Sort terms by change
df_sorted = df.sort_values("diff", ascending=False)

# Export to Excel
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

    df_sorted.to_excel(writer,
                       sheet_name="CSI_Terms",
                       index=False)

    pd.DataFrame({
        "Metric": ["Conceptual Shift Index"],
        "Value": [round(CSI, 3)]
    }).to_excel(writer,
                sheet_name="CSI_Summary",
                index=False)

    sensitivity_df.to_excel(writer,
                            sheet_name="CSI_Sensitivity",
                            index=False)

print(f"Results saved to: {OUTPUT_FILE}")
