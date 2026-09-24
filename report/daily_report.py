# -*- coding: utf-8 -*-
"""
daily_report.py — one command for the automated run.
=====================================================

    python daily_report.py

Steps (each fails loud and stops the run):
  1. pull_supabase   : live uybor_listings_v2 -> data/uybor_listings_v2.csv
  2. pipeline        : merge v1+v2, clean, compute build/metrics.json + pickles
  3. figures         : render the Uzbek figures (figures/)
  4. send_telegram   : post the Uzbek set to the channel
  5. figures_en      : render the English figures (figures_en/)
  6. send_telegram_en: post the English set to the channel

Both language sets are sent every run. The Supabase pull and pipeline run once
and feed both. Sending is attempted for both even if one send fails, and the
run exits non-zero if either the build or either send failed.

Run from the report/ directory (paths in config.py are relative to it).
"""
import sys

import pull_supabase
import pipeline
import figures
import figures_en
import send_telegram
import send_telegram_en


def main():
    rc = pull_supabase.main()
    if rc:
        return rc
    pipeline.main()
    figures.main()
    rc_uz = send_telegram.main()
    figures_en.main()
    rc_en = send_telegram_en.main()
    return rc_uz or rc_en


if __name__ == "__main__":
    sys.exit(main())
