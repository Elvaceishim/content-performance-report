# w6_pandas_basics.py
from pathlib import Path
import pandas as pd

def load_content(path="content_data"):
    files = sorted(Path(path).glob("*.csv"))
    if not files:
        raise SystemExit("No CSVs found in content_data/")
    dfs = []
    for p in files:
        df = pd.read_csv(p)
        dfs.append(df)
    out = pd.concat(dfs, ignore_index=True)

    # clean
    out["title"] = out["title"].astype(str).str.strip()
    out["channel"] = out["channel"].astype(str).str.title().str.strip()
    out["url"] = out["url"].astype(str).str.strip()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    # numeric
    for col in ["views", "clicks", "impressions"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)

    # metrics
    out["ctr_pct"] = (out["clicks"] / out["impressions"]).where(out["impressions"] > 0, 0) * 100

    return out.dropna(subset=["date"])

if __name__ == "__main__":
    df = load_content()

    print("\n=== Raw shape ===")
    print(df.shape)  # (rows, cols)

    # Overall
    totals = df[["views","clicks","impressions"]].sum()
    overall_ctr = (totals["clicks"]/totals["impressions"]*100) if totals["impressions"]>0 else 0

    overall = {
        "posts": df["url"].nunique(),
        "rows": len(df),
        "views": int(totals["views"]),
        "clicks": int(totals["clicks"]),
        "impressions": int(totals["impressions"]),
        "ctr_pct": round(float(overall_ctr), 2),
    }

    print("\n=== Overall ===")
    print(overall)


    # Channel summary
    ch = (
        df.groupby("channel", as_index=False)
          .agg(views=("views","sum"),
               clicks=("clicks","sum"),
               impressions=("impressions","sum"),
               posts=("url","nunique"))
    )
    ch["ctr_pct"] = (ch["clicks"]/ch["impressions"]).where(ch["impressions"]>0, 0)*100
    ch = ch.sort_values(["views","channel"], ascending=[False, True])

    print("\n=== Channel summary ===")
    print(ch.to_string(index=False))

    # Top by views (min impressions)
    MIN_IMPR = 100
    top_by_views = (
        df[df["impressions"] >= MIN_IMPR]
        .groupby(["url","title","channel"], as_index=False)
        .agg(views=("views","sum"),
             clicks=("clicks","sum"),
             impressions=("impressions","sum"))
        .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"])*100)
        .sort_values(["views","title"], ascending=[False, True])
        .head(5)
    )
    print(f"\n=== Top 5 by views (min_impr={MIN_IMPR}) ===")
    print(top_by_views[["title","channel","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    # Top by CTR (min impressions)
    top_by_ctr = (
        df[df["impressions"] >= MIN_IMPR]
        .groupby(["url","title","channel"], as_index=False)
        .agg(views=("views","sum"),
             clicks=("clicks","sum"),
             impressions=("impressions","sum"))
        .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"])*100)
        .sort_values(["ctr_pct","impressions","title"], ascending=[False, False, True])
        .head(5)
    )
    print(f"\n=== Top 5 by CTR% (min_impr={MIN_IMPR}) ===")
    print(top_by_ctr[["title","channel","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    # Monthly rollup (pivot)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    monthly = (
        df.groupby("month", as_index=False)
          .agg(views=("views","sum"),
               clicks=("clicks","sum"),
               impressions=("impressions","sum"),
               posts=("url","nunique"))
          .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"]*100).where(x["impressions"]>0,0))
          .sort_values("month")
    )
    print("\n=== Monthly summary ===")
    print(monthly.to_string(index=False))

    # Best day of week
    df["dow"] = df["date"].dt.day_name()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = (
        df.groupby("dow", as_index=False)
        .agg(views=("views","sum"),
            clicks=("clicks","sum"),
            impressions=("impressions","sum"),
            posts=("url","nunique"))
        .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"]*100).where(x["impressions"]>0,0))
    )
    dow["dow"] = pd.Categorical(dow["dow"], categories=order, ordered=True)
    dow = dow.sort_values("dow")

    print("\n=== Day-of-week summary ===")
    print(dow.to_string(index=False))

    # Monthly x Channel pivot (views)
    df["month"] = df["date"].dt.to_period("M").astype(str)  # already present, safe to reassign
    mx = pd.pivot_table(df, index="month", columns="channel", values="views", aggfunc="sum", fill_value=0)
    print("\n=== Monthly x Channel (views) ===")
    print(mx.to_string())

    # Save exports
    ch.to_csv("pandas_channel_summary.csv", index=False)
    top_by_views.to_csv("pandas_top_by_views.csv", index=False)
    top_by_ctr.to_csv("pandas_top_by_ctr.csv", index=False)
    monthly.to_csv("pandas_monthly_summary.csv", index=False)
    print("\nSaved: pandas_channel_summary.csv, pandas_top_by_views.csv, pandas_top_by_ctr.csv, pandas_monthly_summary.csv")
