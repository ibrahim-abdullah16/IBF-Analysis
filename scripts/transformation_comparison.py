"""
Transformation comparison for IBF-Analysis.

Evaluates raw, Z-score, Min-Max, log1p, Yeo-Johnson and Box-Cox
transformations on the forecast impact scores and observed DDM damage
variables, and reports skewness, excess kurtosis and Shapiro-Wilk
normality for each.

Produces
    transformation_comparison.xlsx
        Summary      one row per method, averaged across variables
        ByVariable   one row per variable x method
        Lambdas      fitted lambda for Yeo-Johnson and Box-Cox
    skewness_by_method.png       grouped bars, skewness per variable
    normality_summary.png        mean |skew|, |kurtosis|, Shapiro p
    dist_<variable>.png          histogram + Q-Q grid across methods

Usage
    python scripts/transformation_comparison.py --cyclone remal --lead 1dlt
    python scripts/transformation_comparison.py --cyclone remal --lead 1dlt --all-rows
    python scripts/transformation_comparison.py --input merged.csv \
        --columns Norm_Impact_House,No_Total

Notes
    Box-Cox requires strictly positive input. Where zeros are present the
    series is shifted by a constant before fitting and the shift is
    recorded in the Lambdas sheet, so the dependence on that shift stays
    visible rather than being buried.
"""

from pathlib import Path
import argparse
import sys
import warnings

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

warnings.filterwarnings("ignore")

PROJECT_ROOT = Path(__file__).resolve().parents[1]

METHOD_ORDER = ["Raw", "Z-score", "Min-Max", "Log1p", "Yeo-Johnson", "Box-Cox"]

METHOD_COLOR = {
    "Raw":         "#616161",
    "Z-score":     "#90A4AE",
    "Min-Max":     "#B0BEC5",
    "Log1p":       "#1565C0",
    "Yeo-Johnson": "#2E7D32",
    "Box-Cox":     "#C62828",
}


# ------------------------------------------------------------------
# transformations
# ------------------------------------------------------------------

def t_raw(x):
    return np.asarray(x, dtype=float), {}


def t_zscore(x):
    x = np.asarray(x, dtype=float)
    sd = x.std(ddof=1)
    if sd == 0:
        return x - x.mean(), {}
    return (x - x.mean()) / sd, {}


def t_minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = x.min(), x.max()
    if hi == lo:
        return np.zeros_like(x), {}
    return (x - lo) / (hi - lo), {}


def t_log1p(x):
    x = np.asarray(x, dtype=float)
    if (x < 0).any():
        return np.full_like(x, np.nan), {"note": "negative values present"}
    return np.log1p(x), {}


def t_yeojohnson(x):
    x = np.asarray(x, dtype=float)
    try:
        y, lam = stats.yeojohnson(x)
        return y, {"lambda": float(lam)}
    except Exception as exc:
        return np.full_like(x, np.nan), {"note": str(exc)[:60]}


def t_boxcox(x):
    x = np.asarray(x, dtype=float)
    shift = 0.0
    if (x <= 0).any():
        # smallest shift that makes every value strictly positive
        shift = float(-x.min() + 1e-6) if x.min() <= 0 else 0.0
        # a unit shift is the conventional choice and keeps the scale readable
        if shift < 1.0:
            shift = 1.0
    try:
        y, lam = stats.boxcox(x + shift)
        return y, {"lambda": float(lam), "shift": shift}
    except Exception as exc:
        return np.full_like(x, np.nan), {"note": str(exc)[:60], "shift": shift}


TRANSFORMS = {
    "Raw":         t_raw,
    "Z-score":     t_zscore,
    "Min-Max":     t_minmax,
    "Log1p":       t_log1p,
    "Yeo-Johnson": t_yeojohnson,
    "Box-Cox":     t_boxcox,
}


# ------------------------------------------------------------------
# statistics
# ------------------------------------------------------------------

def describe(values):
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]

    out = {
        "n": int(v.size),
        "skewness": np.nan,
        "kurtosis": np.nan,
        "shapiro_W": np.nan,
        "shapiro_p": np.nan,
        "normal_at_05": np.nan,
    }
    if v.size < 3 or np.allclose(v, v[0]):
        return out

    out["skewness"] = float(stats.skew(v))
    out["kurtosis"] = float(stats.kurtosis(v))          # excess, Fisher

    if 3 <= v.size <= 5000:
        w, p = stats.shapiro(v)
        out["shapiro_W"] = float(w)
        out["shapiro_p"] = float(p)
        out["normal_at_05"] = bool(p >= 0.05)
    return out


# ------------------------------------------------------------------
# data loading
# ------------------------------------------------------------------

def clean_admin(x):
    if pd.isna(x):
        return np.nan
    return " ".join(str(x).strip().split())


def load_from_config(cyclone, lead):
    import yaml

    cfg_path = PROJECT_ROOT / "configs" / f"{cyclone}.yaml"
    if not cfg_path.is_file():
        sys.exit(f"Config not found: {cfg_path}")

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    if lead not in cfg["data"]["forecasts"]:
        sys.exit(f"Lead time '{lead}' not defined in {cfg_path.name}")

    fc_path = PROJECT_ROOT / cfg["data"]["forecasts"][lead]
    ddm_path = PROJECT_ROOT / cfg["data"]["observed"]

    f1 = pd.read_excel(fc_path, sheet_name=cfg["sheets"]["forecast"])
    f1.columns = [str(c).strip() for c in f1.columns]
    f1 = (f1.dropna(subset=["District", "Upazila"])
            .drop_duplicates(subset=["District", "Upazila"], keep="first")
            .reset_index(drop=True))

    raw_h = pd.read_excel(ddm_path, sheet_name=cfg["sheets"]["house"], header=None)
    h = raw_h.iloc[2:, :10].copy().reset_index(drop=True)
    h.columns = ["District", "Upazila", "No_Brick", "No_HalfBrick", "No_Raw",
                 "No_Total", "Amt_Brick", "Amt_HalfBrick", "Amt_Raw", "Amt_Total"]
    h["District"] = h["District"].ffill()
    h = h.dropna(subset=["District", "Upazila"])
    for c in h.columns[2:]:
        h[c] = pd.to_numeric(h[c], errors="coerce").fillna(0)

    raw_a = pd.read_excel(ddm_path, sheet_name=cfg["sheets"]["agriculture"], header=None)
    a = raw_a.iloc[2:, :8].copy().reset_index(drop=True)
    a.columns = ["District", "Upazila", "Fully_Land", "Fully_Amt",
                 "Partial_Land", "Partial_Amt", "Total_Loss_Land", "Total_Loss_Amt"]
    a["District"] = a["District"].ffill()
    a = a.dropna(subset=["District", "Upazila"])
    for c in a.columns[2:]:
        a[c] = pd.to_numeric(a[c], errors="coerce").fillna(0)

    for df in (f1, h, a):
        df["District"] = df["District"].apply(clean_admin)
        df["Upazila"] = df["Upazila"].apply(clean_admin)

    m_house = pd.merge(f1, h, on=["District", "Upazila"], how="inner")
    m_agri = pd.merge(f1, a, on=["District", "Upazila"], how="inner")

    print(f"Forecast rows            : {len(f1)}")
    print(f"DDM house rows           : {len(h)}   merged: {len(m_house)}"
          f"   dropped: {len(h) - len(m_house)}")
    print(f"DDM agriculture rows     : {len(a)}   merged: {len(m_agri)}"
          f"   dropped: {len(a) - len(m_agri)}")

    pairs = [
        ("Norm_Impact_House", "No_Total",        m_house, "House: index vs houses damaged"),
        ("Norm_Impact_House", "Amt_Total",       m_house, "House: index vs repair cost"),
        ("Norm_Impact_fAPAR", "Total_Loss_Land", m_agri,  "Agri: index vs land lost"),
        ("Norm_Impact_fAPAR", "Total_Loss_Amt",  m_agri,  "Agri: index vs loss value"),
    ]
    return pairs


def load_from_file(path, columns):
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    cols = [c.strip() for c in columns.split(",")] if columns else \
        df.select_dtypes(include=[np.number]).columns.tolist()

    missing = [c for c in cols if c not in df.columns]
    if missing:
        sys.exit(f"Columns not found in {path.name}: {missing}")

    print(f"Loaded {len(df)} rows from {path.name}")
    print(f"Variables: {', '.join(cols)}")
    return [(c, None, df, c) for c in cols]


# ------------------------------------------------------------------
# variable assembly
# ------------------------------------------------------------------

def build_series(pairs, positive_only):
    """Return {variable_name: 1-D array} after the chosen row filter."""
    series = {}

    for x_col, y_col, df, label in pairs:
        t = df.copy()

        if y_col is None:
            v = pd.to_numeric(t[x_col], errors="coerce").dropna()
            series.setdefault(x_col, v.values)
            continue

        t[x_col] = pd.to_numeric(t[x_col], errors="coerce")
        t[y_col] = pd.to_numeric(t[y_col], errors="coerce")
        t = t.dropna(subset=[x_col, y_col])

        if positive_only:
            t = t[(t[x_col] > 0) & (t[y_col] > 0)]

        tag = "" if not positive_only else ""
        series[f"{x_col} [{y_col} pair]{tag}"] = t[x_col].values
        series[y_col] = t[y_col].values

    return series


# ------------------------------------------------------------------
# main comparison
# ------------------------------------------------------------------

def compare(series):
    rows, lam_rows = [], []

    for var, values in series.items():
        v = np.asarray(values, dtype=float)
        v = v[np.isfinite(v)]
        if v.size < 3:
            print(f"  skipping {var}: only {v.size} finite values")
            continue

        for method in METHOD_ORDER:
            transformed, meta = TRANSFORMS[method](v)
            stat = describe(transformed)
            rows.append({"variable": var, "method": method, **stat})

            if "lambda" in meta or "shift" in meta or "note" in meta:
                lam_rows.append({
                    "variable": var,
                    "method": method,
                    "lambda": meta.get("lambda", np.nan),
                    "shift": meta.get("shift", np.nan),
                    "note": meta.get("note", ""),
                })

    by_var = pd.DataFrame(rows)
    by_var["method"] = pd.Categorical(by_var["method"], METHOD_ORDER, ordered=True)
    by_var = by_var.sort_values(["variable", "method"]).reset_index(drop=True)

    summary = (by_var
               .groupby("method", observed=True)
               .agg(mean_skewness=("skewness", "mean"),
                    mean_abs_skewness=("skewness", lambda s: s.abs().mean()),
                    mean_kurtosis=("kurtosis", "mean"),
                    mean_abs_kurtosis=("kurtosis", lambda s: s.abs().mean()),
                    mean_shapiro_p=("shapiro_p", "mean"),
                    median_shapiro_p=("shapiro_p", "median"),
                    n_normal_at_05=("normal_at_05", "sum"),
                    n_variables=("variable", "count"))
               .reindex(METHOD_ORDER)
               .reset_index())

    return by_var, summary, pd.DataFrame(lam_rows)


# ------------------------------------------------------------------
# plots
# ------------------------------------------------------------------

def plot_skewness(by_var, out_path, title_suffix=""):
    variables = list(dict.fromkeys(by_var["variable"]))
    n_var = len(variables)
    x = np.arange(n_var)
    width = 0.8 / len(METHOD_ORDER)

    fig, ax = plt.subplots(figsize=(max(10, 2.0 * n_var), 6))

    for i, method in enumerate(METHOD_ORDER):
        sub = by_var[by_var["method"] == method].set_index("variable")
        vals = [sub["skewness"].get(v, np.nan) for v in variables]
        ax.bar(x + i * width - 0.4 + width / 2, vals, width,
               label=method, color=METHOD_COLOR[method], edgecolor="white",
               linewidth=0.6)

    ax.axhline(0, color="black", lw=1)
    ax.axhspan(-0.5, 0.5, color="#43A047", alpha=0.10,
               label="|skew| < 0.5 (approx. symmetric)")
    ax.set_xticks(x)
    ax.set_xticklabels([v.replace(" [", "\n[") for v in variables],
                       fontsize=8, rotation=0)
    ax.set_ylabel("Skewness", fontsize=11)
    ax.set_title(f"Skewness by transformation{title_suffix}",
                 fontsize=12, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8, ncol=4, loc="upper center",
              bbox_to_anchor=(0.5, -0.10), frameon=False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_summary(summary, out_path, title_suffix=""):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    colors = [METHOD_COLOR[m] for m in summary["method"]]

    panels = [
        ("mean_abs_skewness", "Mean |skewness|", None),
        ("mean_abs_kurtosis", "Mean |excess kurtosis|", None),
        ("mean_shapiro_p", "Mean Shapiro-Wilk p", 0.05),
    ]

    for ax, (col, label, ref) in zip(axes, panels):
        ax.bar(summary["method"], summary[col], color=colors,
               edgecolor="white", linewidth=0.6)
        if ref is not None:
            ax.axhline(ref, color="black", ls="--", lw=1.2)
            ax.text(len(summary) - 0.4, ref, "  p = 0.05",
                    va="bottom", ha="right", fontsize=8)
        for i, v in enumerate(summary[col]):
            if np.isfinite(v):
                ax.text(i, v, f"{v:.3g}", ha="center", va="bottom", fontsize=8)
        ax.set_title(label, fontsize=10, fontweight="bold")
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle(f"Normality diagnostics by transformation{title_suffix}",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


def plot_distributions(var, values, out_path):
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]

    fig, axes = plt.subplots(2, len(METHOD_ORDER),
                             figsize=(3.0 * len(METHOD_ORDER), 6.4))

    for j, method in enumerate(METHOD_ORDER):
        t, meta = TRANSFORMS[method](v)
        t = np.asarray(t, dtype=float)
        t = t[np.isfinite(t)]

        ax_h, ax_q = axes[0, j], axes[1, j]

        if t.size < 3:
            for ax in (ax_h, ax_q):
                ax.text(0.5, 0.5, "n/a", ha="center", va="center",
                        transform=ax.transAxes, fontsize=9)
                ax.set_xticks([]); ax.set_yticks([])
            ax_h.set_title(method, fontsize=9, fontweight="bold")
            continue

        ax_h.hist(t, bins=min(30, max(8, t.size // 5)),
                  color=METHOD_COLOR[method], alpha=0.85, edgecolor="white")
        sk = stats.skew(t)
        lam = meta.get("lambda")
        head = method if lam is None else f"{method}  (λ={lam:.3f})"
        ax_h.set_title(head, fontsize=9, fontweight="bold")
        ax_h.text(0.97, 0.94, f"skew {sk:+.3f}", transform=ax_h.transAxes,
                  ha="right", va="top", fontsize=8,
                  bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                            edgecolor="grey", alpha=0.85))
        ax_h.tick_params(labelsize=7)

        stats.probplot(t, dist="norm", plot=ax_q)
        ax_q.get_lines()[0].set_markersize(3)
        ax_q.get_lines()[0].set_color(METHOD_COLOR[method])
        ax_q.get_lines()[1].set_color("black")
        ax_q.set_title("")
        ax_q.set_xlabel("Theoretical quantiles", fontsize=8)
        ax_q.set_ylabel("Ordered values" if j == 0 else "", fontsize=8)
        ax_q.tick_params(labelsize=7)

    fig.suptitle(f"{var}   (n = {v.size})", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out_path}")


# ------------------------------------------------------------------
# entry point
# ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Compare distribution transformations on IBF variables.")
    ap.add_argument("--cyclone", default="remal",
                    choices=["remal", "sitrang", "midhili"])
    ap.add_argument("--lead", default="1dlt",
                    choices=["1dlt", "2dlt", "3dlt"])
    ap.add_argument("--input", default=None,
                    help="CSV or Excel file to use instead of the config.")
    ap.add_argument("--columns", default=None,
                    help="Comma-separated columns when --input is used.")
    ap.add_argument("--all-rows", action="store_true",
                    help="Skip the X>0 and Y>0 filter (default applies it).")
    ap.add_argument("--outdir", default=None,
                    help="Output directory. Defaults under outputs/.")
    args = ap.parse_args()

    positive_only = not args.all_rows

    if args.input:
        pairs = load_from_file(args.input, args.columns)
        default_out = PROJECT_ROOT / "outputs" / "Transformation_Comparison"
        suffix = f" — {Path(args.input).stem}"
    else:
        pairs = load_from_config(args.cyclone, args.lead)
        default_out = (PROJECT_ROOT / "outputs" / args.cyclone / args.lead
                       / "Transformation_Comparison")
        suffix = (f" — {args.cyclone.capitalize()} {args.lead}"
                  f"{'' if positive_only else ', all rows'}")

    out_dir = Path(args.outdir) if args.outdir else default_out
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nRow filter: {'X > 0 and Y > 0' if positive_only else 'none'}")
    series = build_series(pairs, positive_only)
    print(f"Variables to test: {len(series)}\n")

    by_var, summary, lambdas = compare(series)

    xlsx = out_dir / "transformation_comparison.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        summary.to_excel(xw, sheet_name="Summary", index=False)
        by_var.to_excel(xw, sheet_name="ByVariable", index=False)
        if not lambdas.empty:
            lambdas.to_excel(xw, sheet_name="Lambdas", index=False)
    print(f"Saved: {xlsx}")

    plot_skewness(by_var, out_dir / "skewness_by_method.png", suffix)
    plot_summary(summary, out_dir / "normality_summary.png", suffix)

    for var, values in series.items():
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in var)
        plot_distributions(var, values, out_dir / f"dist_{safe}.png")

    print("\n" + "=" * 78)
    print("SUMMARY  (averaged across variables)")
    print("=" * 78)
    show = summary[["method", "mean_skewness", "mean_kurtosis",
                    "mean_shapiro_p", "n_normal_at_05", "n_variables"]]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"\nAll output written to: {out_dir}")


if __name__ == "__main__":
    main()
