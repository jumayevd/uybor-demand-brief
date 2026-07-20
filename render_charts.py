# -*- coding: utf-8 -*-
"""Render each Chart.js chart in a generated brief to a PNG.

The brief draws its charts client-side onto <canvas> elements, so the only
faithful way to get images is to load the page in a real (headless) browser,
let the charts draw, and export each canvas. Writes <outdir>/<canvasId>.png.

Usage:
    python render_charts.py --html tashkent_demand_brief.html --outdir briefs/2026-07-20

Needs the extra render dependency (kept out of the core pipeline):
    pip install -r requirements-render.txt
    playwright install chromium
"""

import argparse
import base64
import os
import sys

# ordered id -> filename slug, so the PNGs sort sensibly and have readable names
CHART_FILES = {
    "cVelTotal": "01-total-new-views-per-day",
    "cVelPer": "02-per-listing-mean-vs-median",
    "cVpdHist": "03-demand-velocity-distribution",
    "cExit": "04-views-per-day-by-outcome",
    "cDistViews": "05-demand-velocity-by-district",
    "cDistPrice": "06-price-vs-demand-by-district",
    "cRoomsViews": "07-demand-by-room-count",
    "cNew": "08-new-build-vs-secondary",
    "cReno": "09-demand-by-renovation",
    "cTierDemand": "10-demand-by-price-tier",
    "cTierIntent": "11-buyer-intent-by-price-tier",
}


def render(html_path, outdir, scale=2, settle_ms=1200):
    from playwright.sync_api import sync_playwright

    os.makedirs(outdir, exist_ok=True)
    url = "file://" + os.path.abspath(html_path).replace("\\", "/")
    written = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 900},
                                device_scale_factor=scale)
        page.goto(url, wait_until="networkidle")
        page.wait_for_function("typeof Chart !== 'undefined'", timeout=30000)
        # every canvas must have an attached Chart instance before we capture
        page.wait_for_function(
            "[...document.querySelectorAll('canvas')]"
            ".every(c => Chart.getChart(c) !== undefined)", timeout=30000)
        page.wait_for_timeout(settle_ms)  # let the 700ms open-animation finish

        ids = page.evaluate("[...document.querySelectorAll('canvas')].map(c=>c.id)")
        for cid in ids:
            name = CHART_FILES.get(cid, cid)
            data_url = page.evaluate(
                f"document.getElementById({cid!r}).toDataURL('image/png')")
            png = base64.b64decode(data_url.split(",", 1)[1])
            path = os.path.join(outdir, name + ".png")
            with open(path, "wb") as fh:
                fh.write(png)
            written.append(os.path.basename(path))
        browser.close()
    return ids, written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--html", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args(argv)

    if not os.path.exists(args.html):
        print(f"RENDER FAILED: no such file {args.html}", file=sys.stderr)
        return 1
    ids, written = render(args.html, args.outdir, scale=args.scale)
    if not written:
        print("RENDER FAILED: no canvases found in the page", file=sys.stderr)
        return 1
    unknown = [c for c in ids if c not in CHART_FILES]
    if unknown:
        print(f"note: unnamed canvases captured by id: {unknown}")
    print(f"OK: wrote {len(written)} PNG(s) to {args.outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
