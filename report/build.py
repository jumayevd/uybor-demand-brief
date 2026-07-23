"""
build.py — one command to regenerate the entire report from fresh data.
=======================================================================

    python build.py

Steps:
  1. pipeline.py  : raw CSVs (config.CSV_INPUTS) -> build/{L.pkl, P.pkl, metrics.json}
  2. figures.py   : build/*  -> figures/fig_*.pdf  (all 13 figures)

For the daily automation, schedule this file. It is deterministic: same input
CSVs always yield the same numbers and figures. Point config.CSV_INPUTS at the
latest scrape and run.
"""
import pipeline
import figures

if __name__ == "__main__":
    pipeline.main()
    figures.main()
    print("\n[build] complete. Numbers in build/metrics.json, figures in figures/.")
