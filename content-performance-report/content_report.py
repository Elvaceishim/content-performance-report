# content_report.py
from __future__ import annotations
import csv, json, argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional

# ---------- parsing & cleaning ----------

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y")

def parse_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def to_int(s: str) -> int:
    try:
        return int(float(str(s).strip()))
    except (ValueError, TypeError):
        return 0

def normalize_row(r: dict) -> Optional[dict]:
    d = {
        "title": (r.get("title") or "").strip(),
        "date": parse_date(r.get("date", "")),
        "channel": (r.get("channel") or "").strip().title(),
        "views": to_int(r.get("views")),
        "clicks": to_int(r.get("clicks")),
        "impressions": to_int(r.get("impressions")),
        "url": (r.get("url") or "").strip(),
    }
    if not d["title"] or not d["date"]:
        return None
    return d

# ---------- IO ----------

def read_folder_csv(path: Path | str) -> List[dict]:
    path_obj = Path(path)
    if not path_obj.exists():
        print(f"Data folder not found: {path_obj}")
        return []

    rows: List[dict] = []
    for p in sorted(path_obj.glob("*.csv")):
        with p.open("rt", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                clean = normalize_row(row)
                if clean:
                    rows.append(clean)
    return rows

# ---------- filters & rollups ----------

def filter_rows(rows: List[dict], start: Optional[date], end: Optional[date],
                channel: Optional[str]) -> List[dict]:
    out = []
    chan = channel.title().strip() if channel else None
    for r in rows:
        if start and r["date"] < start: 
            continue
        if end and r["date"] > end:
            continue
        if chan and r["channel"] != chan:
            continue
        out.append(r)
    return out

def rollup_by_url(rows: List[dict]) -> List[dict]:
    """Combine duplicate posts (same URL) across files/dates."""
    bucket: Dict[str, dict] = {}
    for r in rows:
        key = r["url"] or f"{r['title']}|{r['channel']}"
        b = bucket.get(key)
        if not b:
            bucket[key] = {
                "url": r["url"],
                "title": r["title"],
                "channel": r["channel"],
                "views": 0,
                "clicks": 0,
                "impressions": 0,
                "first_date": r["date"],
                "last_date": r["date"],
            }
            b = bucket[key]
        b["views"] += r["views"]
        b["clicks"] += r["clicks"]
        b["impressions"] += r["impressions"]
        b["first_date"] = min(b["first_date"], r["date"])
        b["last_date"]  = max(b["last_date"],  r["date"])
    return list(bucket.values())

# ---------- metrics ----------

def overall_metrics(posts: List[dict]) -> dict:
    total_views = sum(p["views"] for p in posts)
    total_clicks = sum(p["clicks"] for p in posts)
    total_impr = sum(p["impressions"] for p in posts)
    ctr = round((total_clicks / total_impr) * 100, 2) if total_impr > 0 else 0.0
    return {
        "posts": len(posts),
        "views": total_views,
        "clicks": total_clicks,
        "impressions": total_impr,
        "ctr_pct": ctr,
    }

def channel_summary(posts: List[dict]) -> List[dict]:
    agg: Dict[str, Dict[str, int]] = defaultdict(lambda: {"views":0,"clicks":0,"impressions":0,"posts":0})
    for p in posts:
        c = agg[p["channel"]]
        c["views"] += p["views"]
        c["clicks"] += p["clicks"]
        c["impressions"] += p["impressions"]
        c["posts"] += 1
    out = []
    for ch, m in agg.items():
        ctr = round((m["clicks"]/m["impressions"])*100, 2) if m["impressions"]>0 else 0.0
        out.append({"channel": ch, **m, "ctr_pct": ctr})
    out.sort(key=lambda x: (-x["views"], x["channel"]))
    return out

def add_post_ctr(posts: List[dict]) -> None:
    for p in posts:
        p["ctr_pct"] = round((p["clicks"]/p["impressions"])*100, 2) if p["impressions"]>0 else 0.0

def top_posts(posts: List[dict], n: int, sort_by: str, min_impr: int) -> List[dict]:
    add_post_ctr(posts)
    filt = [p for p in posts if p["impressions"] >= min_impr]
    key = (lambda p: (-p["views"], p["title"])) if sort_by=="views" else (lambda p: (-p["ctr_pct"], -p["impressions"], p["title"]))
    return sorted(filt, key=key)[:n]

# ---------- output ----------

def save_csv(path: str, rows: List[dict], columns: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in columns})

def save_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)

def print_table(rows: List[dict], columns: List[str], title: str) -> None:
    print(f"\n{title}")
    for r in rows:
        line = " | ".join(str(r.get(k, "")) for k in columns)
        print(line)

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Content performance report")
    ap.add_argument("--path", default=None, help="Folder with CSV files (defaults to the script's content_data)")
    ap.add_argument("--start", default="", help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end",   default="", help="End date (YYYY-MM-DD)")
    ap.add_argument("--channel", default="", help="Filter to one channel (e.g., LinkedIn)")
    ap.add_argument("--top", type=int, default=5, help="How many top posts to show")
    ap.add_argument("--min-impr", type=int, default=100, help="Min impressions for top-post lists")
    ap.add_argument("--save", action="store_true", help="Save CSV and JSON outputs")
    args = ap.parse_args()

    script_dir = Path(__file__).resolve().parent
    data_path = Path(args.path).expanduser() if args.path else script_dir / "content_data"

    start = parse_date(args.start) if args.start else None
    end   = parse_date(args.end)   if args.end   else None
    rows = read_folder_csv(data_path)
    if not rows:
        print("No rows found.")
        return

    rows = filter_rows(rows, start, end, args.channel or None)
    posts = rollup_by_url(rows)

    metrics = overall_metrics(posts)
    chans = channel_summary(posts)
    top_by_views = top_posts(posts, n=args.top, sort_by="views", min_impr=args.min_impr)
    top_by_ctr   = top_posts(posts, n=args.top, sort_by="ctr",   min_impr=args.min_impr)

    print("\n=== Overall ===")
    print(metrics)

    print_table(chans, ["channel","posts","views","clicks","impressions","ctr_pct"], "Channel summary")
    print_table(top_by_views, ["title","channel","views","clicks","impressions","ctr_pct"], f"Top {args.top} posts by views (min_impr={args.min_impr})")
    print_table(top_by_ctr,   ["title","channel","views","clicks","impressions","ctr_pct"], f"Top {args.top} posts by CTR% (min_impr={args.min_impr})")

    if args.save:
        save_csv("report_channel_summary.csv", chans, ["channel","posts","views","clicks","impressions","ctr_pct"])
        save_csv("report_top_by_views.csv", top_by_views, ["title","channel","views","clicks","impressions","ctr_pct","url","first_date","last_date"])
        save_csv("report_top_by_ctr.csv",   top_by_ctr,   ["title","channel","views","clicks","impressions","ctr_pct","url","first_date","last_date"])
        save_json("report_overall.json", metrics)
        print("\nSaved: report_channel_summary.csv, report_top_by_views.csv, report_top_by_ctr.csv, report_overall.json")

if __name__ == "__main__":
    main()
