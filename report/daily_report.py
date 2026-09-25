# -*- coding: utf-8 -*-
"""
daily_report.py — one command for the automated run.
=====================================================

    python daily_report.py

Steps (each fails loud and stops the run):
  1. pull_supabase : live uybor_listings_v2 -> data/uybor_listings_v2.csv
  2. pipeline      : merge v1+v2, clean, compute build/metrics.json + pickles
  3. figures       : render the Uzbek figures (figures/)
  4. send_telegram : post the Uzbek set to the channel

This is the UZBEK daily post (06:00 Asia/Tashkent). The English paper figures
are a separate post at 07:00 via daily_report_en.py / report-en.yml.

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
