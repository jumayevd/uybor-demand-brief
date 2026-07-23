# -*- coding: utf-8 -*-
"""
send_telegram.py — rasterize the built figures to PNG and post them to a
Telegram channel via the Bot API.
=======================================================================

Each fig_*.pdf in figures/ is sent to the channel twice, in a fixed order: a
rasterized PNG (inline preview, with a human caption) followed by the original
vector PDF (downloadable document). A leading header message gives the run's
window/listing count from build/metrics.json.

Env:
  TELEGRAM_BOT_TOKEN   bot token from @BotFather (never hardcode / never logged)
  TELEGRAM_CHAT        channel, e.g. "@chart_automation" (default below)

Prereqs (one-time, done by you):
  1. Create a bot with @BotFather -> get the token.
  2. Add that bot to the channel as an ADMIN with "Post messages" permission.

Fail-loud: any HTTP error from Telegram aborts non-zero with the API message.
"""
import json
import os
import sys
import time

import fitz  # PyMuPDF
import requests

TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ENV = "TELEGRAM_CHAT"
DEFAULT_CHAT = "@chart_automation"

HERE = os.path.dirname(__file__)
FIG_DIR = os.path.join(HERE, "figures")
PNG_DIR = os.path.join(HERE, "figures_png")
METRICS = os.path.join(HERE, "build", "metrics.json")

# fixed send order + caption per figure (only those present are sent)
FIGURES = [
    ("fig_evidence_map", "Four listing signals validated as demand proxies"),
    ("fig_concentration_apartments", "Demand velocity: distribution & top-decile share"),
    ("fig_s1_dimensions", "View velocity by rooms / build type / day-of-week"),
    ("fig_funnel_apartments", "Attention funnel: views → clicks → favorites"),
    ("fig_wedge_apartments", "Velocity vs intent by price quintile"),
    ("fig_intent_norm_districts", "Normalized click/favorite incidence by district"),
    ("fig_s2_dimensions", "Intent by rooms / day-of-week"),
    ("fig_exit_apartments", "Exit velocity gap + renewal-wall decomposition"),
    ("fig_exit_dims", "Exit rate by district / rooms"),
    ("fig_tom_dims", "Time-on-market wall + stock age by district / rooms"),
    ("fig_metrics_panel_apartments", "District heatmap of the four demand signals"),
    ("fig_supply_demand_bands", "Supply vs demand by price band"),
    ("fig_demand_map", "District demand bubble map + ranked panel"),
]

API = "https://api.telegram.org/bot{token}/{method}"
RASTER_SCALE = 2.5   # PDF points -> px multiplier
GAP = 3.5            # seconds between messages (channel limit ~20/min)
MAX_TRIES = 6        # retries when Telegram rate-limits (HTTP 429)


def _rasterize(pdf_path, png_path):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(RASTER_SCALE, RASTER_SCALE))
    pix.save(png_path)
    doc.close()


def _api(token, method, data, file_field=None, file_path=None, mime=None):
    """POST to the Bot API, re-opening any file each attempt and honouring
    Telegram's 429 `retry_after` back-off."""
    url = API.format(token=token, method=method)
    for attempt in range(MAX_TRIES):
        fh = files = None
        if file_field:
            fh = open(file_path, "rb")
            name = os.path.basename(file_path)
            files = {file_field: (name, fh, mime) if mime else fh}
        try:
            r = requests.post(url, data=data, files=files, timeout=120)
        finally:
            if fh:
                fh.close()
        body = r.json()
        if body.get("ok"):
            return body["result"]
        if body.get("error_code") == 429:
            wait = int(body.get("parameters", {}).get("retry_after", 5)) + 2
            time.sleep(wait)
            continue
        raise RuntimeError(f"Telegram {method} failed: "
                           f"{body.get('error_code')} {body.get('description')}")
    raise RuntimeError(f"Telegram {method}: still rate-limited after {MAX_TRIES} tries")


def _header():
    if not os.path.exists(METRICS):
        return "Uybor apartments — daily demand figures"
    w = json.load(open(METRICS, encoding="utf-8"))["window"]
    return ("📊 *Uybor apartments — daily demand figures*\n"
            f"{w['date_min']} → {w['date_max']}  ·  "
            f"{w['n_listings']:,} listings  ·  {w['n_days']} snapshots")


def main(argv=None):
    token = os.environ.get(TOKEN_ENV)
    chat = os.environ.get(CHAT_ENV, DEFAULT_CHAT)
    if not token:
        print(f"SEND FAILED: ${TOKEN_ENV} is not set", file=sys.stderr)
        return 1

    present = [(n, cap) for (n, cap) in FIGURES
               if os.path.exists(os.path.join(FIG_DIR, n + ".pdf"))]
    if not present:
        print(f"SEND FAILED: no figures found in {FIG_DIR}", file=sys.stderr)
        return 1

    os.makedirs(PNG_DIR, exist_ok=True)
    try:
        _api(token, "sendMessage",
             {"chat_id": chat, "text": _header(), "parse_mode": "Markdown"})
        time.sleep(GAP)
        for name, caption in present:
            pdf = os.path.join(FIG_DIR, name + ".pdf")
            png = os.path.join(PNG_DIR, name + ".png")
            _rasterize(pdf, png)
            # PNG preview (inline) ...
            _api(token, "sendPhoto", {"chat_id": chat, "caption": caption},
                 file_field="photo", file_path=png)
            time.sleep(GAP)
            # ... then the original vector PDF as a downloadable document
            _api(token, "sendDocument", {"chat_id": chat},
                 file_field="document", file_path=pdf, mime="application/pdf")
            time.sleep(GAP)
    except Exception as exc:
        print(f"SEND FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"[telegram] sent {len(present)} figures (PNG + PDF) to {chat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
