# -*- coding: utf-8 -*-
"""
daily_report.py — one command for the automated run.
=====================================================

    python daily_report.py

Steps (each fails loud and stops the run):
  1. pull_supabase : live uybor_listings_v2 -> data/uybor_listings_v2.csv
  2. build         : merge v1+v2, clean, compute metrics, render 13 PDFs
  3. send_telegram : rasterize each figure to PNG and post to the channel

Run from the report/ directory (paths in config.py are relative to it).
"""
import sys

import pull_supabase
import pipeline
import figures
import send_telegram


def main():
    rc = pull_supabase.main()
    if rc:
        return rc
    pipeline.main()
    figures.main()
    return send_telegram.main()


if __name__ == "__main__":
    sys.exit(main())
