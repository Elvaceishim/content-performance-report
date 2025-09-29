import content_report as cr
from datetime import date

def test_parse_date():
    assert cr.parse_date("2025-02-01") == date(2025, 2, 1)
    assert cr.parse_date("02/01/2025")  # US
    assert cr.parse_date("01/02/2025")  # EU
    assert cr.parse_date("bad") is None

def test_rollup_and_metrics():
    rows = [
        {"title":"A","date":"2025-01-01","channel":"LinkedIn","views":"100","clicks":"10","impressions":"400","url":"u1"},
        {"title":"A","date":"2025-01-15","channel":"LinkedIn","views":"50","clicks":"5","impressions":"200","url":"u1"},
        {"title":"B","date":"2025-01-02","channel":"Medium","views":"80","clicks":"4","impressions":"300","url":"u2"},
    ]
    clean = [cr.normalize_row(r) for r in rows]
    clean = [r for r in clean if r]
    posts = cr.rollup_by_url(clean)
    m = cr.overall_metrics(posts)
    assert m["posts"] == 2
    assert m["views"] == 230
    assert m["clicks"] == 19
    assert m["impressions"] == 900
    assert m["ctr_pct"] == round((19/900)*100, 2)
