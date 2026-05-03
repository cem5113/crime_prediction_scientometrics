# ============================================================
# METHOD EVOLUTION NETWORK - Crime Prediction Literature
# Author: Cem Eroglu
# Purpose:
#   1. Detect method terms in bibliometric metadata
#   2. Build method co-occurrence networks by period
#   3. Compute network centrality metrics
#   4. Export edge/node tables and figures
# ============================================================

import pandas as pd
import numpy as np
import re
import itertools
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# 1. SETTINGS
# ============================================================

DATA_DIR = Path("data")
OUT_DIR = Path("outputs/method_evolution_outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = DATA_DIR / "Bibliometrix_(WoS+Scopus).xlsx"

MIN_EDGE_WEIGHT = 2        
MIN_NODE_FREQ = 2         
FIG_DPI = 300

PERIODS = {
    "pre_ai_1980_2016": (1980, 2016),
    "transition_2017_2019": (2017, 2019),
    "post_ai_2020_2025": (2020, 2025),
    "all_1980_2025": (1980, 2025),
}

# ============================================================
# 2. METHOD DICTIONARY
# Left: normalized method name
# Right: possible textual variations to detect
# ============================================================

METHOD_DICT = {
    "hotspot_mapping": ["hotspot mapping", "hot spot mapping", "crime hotspot", "hotspot detection", "hot spot detection", "hotspot analysis"],
    "risk_terrain_modeling": ["risk terrain modeling", "risk terrain modelling", "rtm"],
    "kernel_density_estimation": ["kernel density estimation", "kde"],
    "near_repeat": ["near repeat", "near-repeat"],
    "self_exciting_point_process": ["self-exciting point process", "self exciting point process", "sepp", "etas"],
    "spatial_analysis": ["spatial analysis", "spatial model", "spatial modeling", "spatial modelling", "geospatial analysis", "gis"],
    "time_series": ["time series", "time-series", "time series analysis", "temporal analysis", "spatio-temporal", "spatiotemporal"],
    "arima": ["arima", "sarima", "autoregressive integrated moving average"],
    "regression": ["regression", "regression analysis", "linear regression", "logistic regression", "poisson regression", "negative binomial"],
    "bayesian_model": ["bayesian", "bayesian network", "bayesian model"],
    "decision_tree": ["decision tree", "decision trees", "classification tree", "cart"],
    "random_forest": ["random forest", "random forests"],
    "support_vector_machine": ["support vector machine", "support vector machines", "svm"],
    "knn": ["k-nearest", "k nearest", "knn", "nearest neighbor search"],
    "naive_bayes": ["naive bayes", "naïve bayes"],
    "gradient_boosting": ["gradient boosting", "gbm", "lightgbm", "light gbm", "catboost", "cat boost"],
    "xgboost": ["xgboost", "extreme gradient boosting"],
    "adaptive_boosting": ["adaptive boosting", "adaboost"],
    "ensemble_learning": ["ensemble learning", "ensemble model", "ensemble method", "stacking", "stacked generalization", "bagging", "boosting"],
    "machine_learning": ["machine learning", "machine-learning", "machine learning algorithms", "machine learning techniques", "machine learning models", "ml"],
    "supervised_learning": ["supervised learning"],
    "deep_learning": ["deep learning", "dl", "deep neural network", "deep neural networks", "dnn"],
    "artificial_neural_network": ["artificial neural network", "ann", "neural network", "neural networks", "neural-networks"],
    "cnn": ["convolutional neural network", "convolutional neural networks", "cnn"],
    "rnn": ["recurrent neural network", "rnn"],
    "lstm": ["long short-term memory", "long short term memory", "lstm"],
    "gru": ["gated recurrent unit", "gru"],
    "transformer": ["transformer", "transformer model", "attention model", "self-attention", "self attention"],
    "graph_neural_network": ["graph neural network", "gnn", "graph convolutional network", "gcn"],
    "clustering": ["clustering", "cluster analysis", "k-means", "kmeans", "k-means clustering", "dbscan", "hdbscan"],
    "classification": ["classification", "classification of information"],
    "feature_selection": ["feature selection"],
    "feature_extraction": ["feature extraction"],
    "anomaly_detection": ["anomaly detection"],
    "contrastive_learning": ["contrastive learning"],
    "natural_language_processing": ["natural language processing", "nlp", "text mining", "sentiment analysis"],
    "computer_vision": ["computer vision", "video surveillance", "object detection", "image recognition"],
    "surveillance_analytics": ["video surveillance", "cctv", "surveillance analytics"],
    "explainable_ai": ["explainable ai", "explainable artificial intelligence", "xai", "shap", "lime"],
    "predictive_policing": ["predictive policing", "predictive police", "predictive policing model"],
    "risk_model": ["risk model", "risk modeling", "risk modelling", "risk prediction", "risk assessment", "risk-based model"],
    "victimization_model": ["victimization risk", "victimisation risk", "victim risk", "victim risk modeling", "victim risk modelling"],
    "data_mining": ["data mining", "knowledge discovery"],
    "predictive_analytics": ["predictive analytics"],
    "early_warning_system": ["early warning system", "early warning"],
    "smart_city": ["smart city", "smart cities", "urban computing"],
    "mobility_data": ["mobility data", "mobile phone data", "human mobility", "trajectory data", "gps data"]
}

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def normalize_colnames(df):
    """
    Flexibly standardizes Bibliometrix/WoS/Scopus column names.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def pick_col(df, candidates):
    """
    Returns the first matching column from candidate names.
    """
    for c in candidates:
        if c in df.columns:
            return c
    return None


def clean_text(x):
    """
    Converts text to lowercase and reduces punctuation effects.
    """
    if pd.isna(x):
        return ""
    x = str(x).lower()
    x = x.replace("–", "-").replace("—", "-")
    x = re.sub(r"[^a-z0-9ğüşıöç\s\-]", " ", x)
    x = re.sub(r"\s+", " ", x).strip()
    return x


def compile_patterns(method_dict):
    """
    Compiles regex patterns for each method.
    Uses word boundaries for shorter terms.
    """
    patterns = {}

    for method, variants in method_dict.items():
        escaped = []
        for v in variants:
            v_clean = clean_text(v)
            v_clean = re.escape(v_clean)
            v_clean = v_clean.replace(r"\ ", r"\s+")
            escaped.append(v_clean)

        pattern = r"\b(" + "|".join(escaped) + r")\b"
        patterns[method] = re.compile(pattern, flags=re.IGNORECASE)

    return patterns


def detect_methods(text, patterns):
    """
    Detects methods appearing in a document.
    """
    found = []
    for method, pattern in patterns.items():
        if pattern.search(text):
            found.append(method)
    return sorted(set(found))


def assign_period(year):
    """
    Assigns main analysis period.
    """
    if pd.isna(year):
        return "unknown"
    year = int(year)

    if year <= 2016:
        return "pre_ai_1980_2016"
    elif 2017 <= year <= 2019:
        return "transition_2017_2019"
    elif year >= 2020:
        return "post_ai_2020_2025"
    else:
        return "unknown"


def build_edges(method_lists):
    """
    Builds edge list from co-occurring methods in the same document.
    """
    edge_counter = {}

    for methods in method_lists:
        methods = sorted(set(methods))
        if len(methods) < 2:
            continue

        for a, b in itertools.combinations(methods, 2):
            edge = tuple(sorted([a, b]))
            edge_counter[edge] = edge_counter.get(edge, 0) + 1

    edges = pd.DataFrame(
        [(a, b, w) for (a, b), w in edge_counter.items()],
        columns=["source", "target", "weight"]
    )

    if len(edges) == 0:
        return pd.DataFrame(columns=["source", "target", "weight"])

    return edges.sort_values("weight", ascending=False)


def build_node_table(df_period):
    """
    Generates method frequency table.
    """
    rows = []
    for methods in df_period["methods"]:
        for m in methods:
            rows.append(m)

    if not rows:
        return pd.DataFrame(columns=["method", "freq"])

    node_freq = (
        pd.Series(rows)
        .value_counts()
        .rename_axis("method")
        .reset_index(name="freq")
    )

    return node_freq


def compute_network_metrics(edges, nodes):
    """
    Computes network centrality metrics.
    """
    G = nx.Graph()

    for _, row in nodes.iterrows():
        G.add_node(row["method"], freq=row["freq"])

    for _, row in edges.iterrows():
        G.add_edge(row["source"], row["target"], weight=row["weight"])

    if len(G.nodes) == 0:
        return G, pd.DataFrame()

    degree = dict(G.degree(weight="weight"))
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)

    try:
        eigenvector = nx.eigenvector_centrality_numpy(G, weight="weight")
    except Exception:
        eigenvector = {n: np.nan for n in G.nodes}

    metrics = []
    for n in G.nodes:
        metrics.append({
            "method": n,
            "freq": G.nodes[n].get("freq", 0),
            "weighted_degree": degree.get(n, 0),
            "degree_centrality": degree_centrality.get(n, 0),
            "betweenness_centrality": betweenness.get(n, 0),
            "eigenvector_centrality": eigenvector.get(n, np.nan)
        })

    metrics = pd.DataFrame(metrics).sort_values(
        ["weighted_degree", "freq"],
        ascending=False
    )

    return G, metrics


def plot_network(G, metrics, title, out_path):
    """
    Plots the network.
    """
    if len(G.nodes) == 0:
        print(f"[SKIP] Empty graph: {title}")
        return

    plt.figure(figsize=(12, 9))

    pos = nx.spring_layout(G, seed=42, k=0.7, weight="weight")

    node_freq = dict(zip(metrics["method"], metrics["freq"]))
    node_sizes = [
        300 + 80 * np.sqrt(node_freq.get(n, 1))
        for n in G.nodes()
    ]

    edge_weights = [
        G[u][v].get("weight", 1)
        for u, v in G.edges()
    ]

    max_w = max(edge_weights) if edge_weights else 1
    edge_widths = [
        0.5 + 3 * (w / max_w)
        for w in edge_weights
    ]

    nx.draw_networkx_edges(
        G, pos,
        width=edge_widths,
        alpha=0.35
    )

    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        alpha=0.85
    )

    labels = {n: n.replace("_", " ") for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos,
        labels=labels,
        font_size=8
    )

    plt.title(title, fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=FIG_DPI, bbox_inches="tight")
    plt.close()


# ============================================================
# 4. LOAD DATA
# ============================================================

df = pd.read_excel(INPUT_FILE)
df = normalize_colnames(df)

print("Loaded shape:", df.shape)
print("Columns:", list(df.columns))

year_col = pick_col(df, ["PY", "Year", "year", "Publication Year"])
title_col = pick_col(df, ["TI", "Title", "title", "Article Title"])
abstract_col = pick_col(df, ["AB", "Abstract", "abstract"])
author_kw_col = pick_col(df, ["DE", "Author Keywords", "Author Keywords (DE)", "Keywords"])
kw_plus_col = pick_col(df, ["ID", "Keywords Plus", "Index Keywords"])

if year_col is None:
    raise ValueError("Year column not found. A column such as 'PY' or 'Year' is required.")

text_cols = [c for c in [title_col, abstract_col, author_kw_col, kw_plus_col] if c is not None]

if len(text_cols) == 0:
    raise ValueError("None of the Title/Abstract/Keywords columns were found.")

print("Year column:", year_col)
print("Text columns used:", text_cols)

# ============================================================
# 5. TEXT COMBINATION + METHOD DETECTION
# ============================================================

df["year"] = pd.to_numeric(df[year_col], errors="coerce")

df["combined_text"] = ""
for c in text_cols:
    df["combined_text"] += " " + df[c].fillna("").astype(str)

df["combined_text"] = df["combined_text"].apply(clean_text)

patterns = compile_patterns(METHOD_DICT)

df["methods"] = df["combined_text"].apply(lambda x: detect_methods(x, patterns))
df["n_methods"] = df["methods"].apply(len)
df["period"] = df["year"].apply(assign_period)

# Keep only records with at least one detected method
df_methods = df[df["n_methods"] > 0].copy()

print("\nTotal records:", len(df))
print("Records with at least one detected method:", len(df_methods))
print("Method detection rate:", round(len(df_methods) / len(df) * 100, 2), "%")

# Export detected methods per paper
df_methods_export = df_methods[[year_col, "year", "period", "methods", "n_methods"] + text_cols].copy()
df_methods_export["methods"] = df_methods_export["methods"].apply(lambda x: "; ".join(x))
df_methods_export.to_csv(OUT_DIR / "detected_methods_by_paper.csv", index=False, encoding="utf-8-sig")

# ============================================================
# 6. BUILD NETWORKS BY PERIOD
# ============================================================

all_metrics = []
summary_rows = []

for period_name, (start_year, end_year) in PERIODS.items():

    df_p = df_methods[
        (df_methods["year"] >= start_year) &
        (df_methods["year"] <= end_year)
    ].copy()

    print(f"\n===== {period_name} | {start_year}-{end_year} =====")
    print("Papers with detected methods:", len(df_p))

    nodes = build_node_table(df_p)
    nodes = nodes[nodes["freq"] >= MIN_NODE_FREQ].copy()

    valid_methods = set(nodes["method"])
    df_p["methods_filtered"] = df_p["methods"].apply(
        lambda ms: sorted([m for m in ms if m in valid_methods])
    )

    edges = build_edges(df_p["methods_filtered"])
    edges = edges[edges["weight"] >= MIN_EDGE_WEIGHT].copy()

    # Re-filter the node list after edge filtering
    if len(edges) > 0:
        edge_nodes = set(edges["source"]).union(set(edges["target"]))
        nodes = nodes[nodes["method"].isin(edge_nodes)].copy()

    G, metrics = compute_network_metrics(edges, nodes)

    # Export
    nodes.to_csv(OUT_DIR / f"nodes_{period_name}.csv", index=False, encoding="utf-8-sig")
    edges.to_csv(OUT_DIR / f"edges_{period_name}.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(OUT_DIR / f"metrics_{period_name}.csv", index=False, encoding="utf-8-sig")

    # GraphML export for Gephi / VOSviewer-like network tools
    if len(G.nodes) > 0:
        nx.write_graphml(G, OUT_DIR / f"network_{period_name}.graphml")

    # Figure
    plot_network(
        G,
        metrics,
        title=f"Method Evolution Network: {period_name.replace('_', ' ')}",
        out_path=OUT_DIR / f"network_{period_name}.png"
    )

    # Summary
    if len(metrics) > 0:
        top_degree = metrics.iloc[0]["method"]
        top_betweenness = metrics.sort_values("betweenness_centrality", ascending=False).iloc[0]["method"]
    else:
        top_degree = None
        top_betweenness = None

    summary_rows.append({
        "period": period_name,
        "start_year": start_year,
        "end_year": end_year,
        "papers_with_methods": len(df_p),
        "n_nodes": len(G.nodes),
        "n_edges": len(G.edges),
        "density": nx.density(G) if len(G.nodes) > 1 else 0,
        "top_weighted_degree_method": top_degree,
        "top_betweenness_method": top_betweenness
    })

    if len(metrics) > 0:
        temp = metrics.copy()
        temp["period"] = period_name
        all_metrics.append(temp)

# ============================================================
# 7. SUMMARY EXPORT
# ============================================================

summary = pd.DataFrame(summary_rows)
summary.to_csv(OUT_DIR / "method_evolution_network_summary.csv", index=False, encoding="utf-8-sig")

if all_metrics:
    all_metrics_df = pd.concat(all_metrics, ignore_index=True)
    all_metrics_df.to_csv(OUT_DIR / "all_period_network_metrics.csv", index=False, encoding="utf-8-sig")

print("\nDONE.")
print("Outputs saved to:", OUT_DIR.resolve())
print("\nSummary:")
print(summary)
