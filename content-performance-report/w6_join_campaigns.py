# w6_join_campaigns.py
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pandas as pd
from w6_pandas_basics import load_content

def normalize_url(s: str) -> str:
    return str(s).strip().rstrip("/").lower()

def load_campaigns(path="content_data/campaigns.csv") -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Missing {path}")
    df = pd.read_csv(p)
    df["url"] = df["url"].astype(str)
    df["url_key"] = df["url"].map(normalize_url)
    # light cleaning
    for c in ["campaign","source","medium","topic"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    return df

def utm_from_url(url: str) -> dict:
    try:
        q = parse_qs(urlparse(str(url)).query)
        pick = lambda k: (q.get(k) or [None])[0]
        return {
            "utm_campaign": pick("utm_campaign"),
            "utm_source":   pick("utm_source"),
            "utm_medium":   pick("utm_medium"),
            "utm_term":     pick("utm_term"),
            "utm_content":  pick("utm_content"),
        }
    except Exception:
        return {"utm_campaign":None,"utm_source":None,"utm_medium":None,"utm_term":None,"utm_content":None}

if __name__ == "__main__":
    # 1) content totals per URL (across months/channels)
    df = load_content("content_data")
    per_url = (
        df.groupby("url", as_index=False)
          .agg(title=("title","first"),
               channels=("channel","nunique"),
               views=("views","sum"),
               clicks=("clicks","sum"),
               impressions=("impressions","sum"),
               first_date=("date","min"),
               last_date=("date","max"))
          .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"]).where(x["impressions"]>0,0)*100)
    )
    per_url["url_key"] = per_url["url"].map(normalize_url)

    # 2) campaigns
    cmap = load_campaigns()

    # 3) left-join: keep all content URLs; add campaign fields if found
    merged = per_url.merge(
        cmap.drop_duplicates("url_key"),
        on="url_key", how="left", suffixes=("","_camp")
    )

    # Attach UTM columns parsed from URL
    utm_df = pd.DataFrame(merged["url"].map(utm_from_url).tolist())
    merged = pd.concat([merged, utm_df], axis=1)

    # Prefer explicit campaign map; fall back to UTM; then 'unknown'
    merged["campaign"] = merged["campaign"].fillna(merged["utm_campaign"]).fillna("unknown")
    merged["source"]   = merged["source"]  .fillna(merged["utm_source"]).fillna("unknown")
    merged["medium"]   = merged["medium"]  .fillna(merged["utm_medium"]).fillna("unknown")
    # topic stays as-is; if missing, keep 'unknown'
    merged["topic"]    = merged["topic"]   .fillna("unknown")


    # 4) quick diagnostics
    missing_campaign = merged[merged["campaign"].isna()]
    extra_campaign = cmap[~cmap["url_key"].isin(per_url["url_key"])]

    print("\n=== Join check ===")
    print({
        "content_urls": len(per_url),
        "campaign_rows": len(cmap),
        "matched": int((~merged["campaign"].isna()).sum()),
        "missing_campaign_for_content": len(missing_campaign),
        "campaign_without_content": len(extra_campaign),
    })

    if not missing_campaign.empty:
        print("\nContent URLs with no campaign:")
        print(missing_campaign[["title","url"]].to_string(index=False))

    if not extra_campaign.empty:
        print("\nCampaign URLs with no content metrics:")
        print(extra_campaign[["url","campaign"]].to_string(index=False))

    # 5) campaign summaries
    merged["campaign"] = merged["campaign"].fillna("unknown")
    merged["source"] = merged["source"].fillna("unknown")
    merged["medium"] = merged["medium"].fillna("unknown")
    merged["topic"] = merged["topic"].fillna("unknown")

    by_campaign = (
        merged.groupby(["campaign"], as_index=False)
              .agg(views=("views","sum"),
                   clicks=("clicks","sum"),
                   impressions=("impressions","sum"),
                   urls=("url","nunique"))
              .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"]).where(x["impressions"]>0,0)*100)
              .sort_values(["views","campaign"], ascending=[False, True])
    )

    by_source = (
        merged.groupby(["source"], as_index=False)
              .agg(views=("views","sum"),
                   clicks=("clicks","sum"),
                   impressions=("impressions","sum"),
                   urls=("url","nunique"))
              .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"])*100)
              .sort_values(["views","source"], ascending=[False, True])
    )

    by_topic = (
        merged.groupby(["topic"], as_index=False)
              .agg(views=("views","sum"),
                   clicks=("clicks","sum"),
                   impressions=("impressions","sum"),
                   urls=("url","nunique"))
              .assign(ctr_pct=lambda x: (x["clicks"]/x["impressions"])*100)
              .sort_values(["views","topic"], ascending=[False, True])
    )

    print("\n=== By campaign ===")
    print(by_campaign[["campaign","urls","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    print("\n=== By source ===")
    print(by_source[["source","urls","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    print("\n=== By topic ===")
    print(by_topic[["topic","urls","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    # 6) Top posts with campaign attached (min impressions)
    MIN_IMPR = 100
    top_posts = (
        merged[merged["impressions"] >= MIN_IMPR]
        .sort_values(["views","title"], ascending=[False, True])
        .head(5)
    )
    print(f"\n=== Top posts (with campaign) — min_impr={MIN_IMPR} ===")
    print(top_posts[["title","campaign","source","medium","views","clicks","impressions","ctr_pct"]]
          .round({"ctr_pct":2}).to_string(index=False))

    # 7) Save exports
    by_campaign.to_csv("pandas_by_campaign.csv", index=False)
    by_source.to_csv("pandas_by_source.csv", index=False)
    by_topic.to_csv("pandas_by_topic.csv", index=False)
    merged.to_csv("pandas_posts_with_campaign.csv", index=False)
    print("\nSaved: pandas_by_campaign.csv, pandas_by_source.csv, pandas_by_topic.csv, pandas_posts_with_campaign.csv")
