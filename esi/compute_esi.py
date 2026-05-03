# EPISTEMIC SHIFT INDEX (ESI) - Crime Prediction Literature
# Author: Cem Eroglu
# Purpose:
#   1. Compare pre-AI and post-AI keyword structures
#   2. Standardize equivalent terms across periods
#   3. Measure conceptual change between the two periods
#   4. Export ESI tables and figures

import pandas as pd
from pathlib import Path

# Paths
DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

PRE_FILE = DATA_DIR / "pre_ai.xlsx"
POST_FILE = DATA_DIR / "post_ai.xlsx"
OUTPUT_FILE = OUTPUT_DIR / "ESI_results.xlsx"

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

# Calculate ESI
df["diff"] = abs(df["p_post"] - df["p_pre"])
ESI = 0.5 * df["diff"].sum()

print("ESI value:", round(ESI, 3))

# Sort terms by change
df_sorted = df.sort_values("diff", ascending=False)

# Export to Excel
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_sorted.to_excel(writer, sheet_name="ESI_Terms", index=False)
    pd.DataFrame({
        "Metric": ["Epistemic Shift Index"],
        "Value": [round(ESI, 3)]
    }).to_excel(writer, sheet_name="ESI_Summary", index=False)

print(f"Results saved to: {OUTPUT_FILE}")
