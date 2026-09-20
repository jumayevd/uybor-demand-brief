"""
build_en.py — produce the ENGLISH paper figures from the latest data.
======================================================================
    python build_en.py            # pull v2, build metrics, render EN figures, export JPG
    python build_en.py --no-pull  # skip the Supabase pull (use existing data CSV)

Steps:
  1. pull_supabase : live uybor_listings_v2 -> data/uybor_listings_v2.csv  (unless --no-pull)
  2. pipeline      : merge v1+v2, clean, compute build/metrics.json + L/P pickles
  3. figures_en    : build figures_en/fig_*.pdf  (English, 11 paper figures)
  4. rasterize     : figures_en/fig_*.jpg  (high quality, ~300 DPI)
"""
import glob
import os
import sys

import fitz  # PyMuPDF

import pull_supabase
import pipeline
import figures_en

JPG_SCALE = 4.17   # 72 * 4.17 ≈ 300 DPI
JPG_QUALITY = 95


def rasterize_all(pdf_dir):
    made = []
    for pdf in sorted(glob.glob(os.path.join(pdf_dir, "*.pdf"))):
        jpg = pdf[:-4] + ".jpg"
        doc = fitz.open(pdf)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(JPG_SCALE, JPG_SCALE))
        with open(jpg, "wb") as fh:
            fh.write(pix.tobytes("jpg", jpg_quality=JPG_QUALITY))
        doc.close()
        made.append(os.path.basename(jpg))
    return made


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--no-pull" not in argv:
        rc = pull_supabase.main()
        if rc:
            return rc
    pipeline.main()
    figures_en.main()
    jpgs = rasterize_all(figures_en.FIG_DIR)
    print(f"[build_en] exported {len(jpgs)} JPG(s) alongside the PDFs in {figures_en.FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
