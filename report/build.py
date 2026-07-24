"""
build.py — bitta buyruq bilan butun hisobotni yangi ma'lumotdan qayta yaratadi.
==============================================================================

    python build.py

Bosqichlar:
  1. pipeline.py : xom CSV (config.CSV_INPUTS) -> build/{L.pkl, P.pkl, metrics.json}
  2. figures.py  : build/* -> figures/fig_*.pdf  (aynan 11 ta figura, paperdagidek)
  3. tekshiruv   : 11 ta figura yaratilganini va asosiy raqamlarni tasdiqlaydi

Determinlashtirilgan: bir xil kirish CSV har doim bir xil raqam va figuralarni beradi.
"""
import os
import json
import pipeline
import figures
import config

# Paperda ishlatiladigan aynan 11 ta figura (boshqasi yaratilmaydi):
EXPECTED_FIGURES = [
    "fig_concentration_apartments.pdf",
    "fig_s1_dimensions.pdf",
    "fig_wedge_apartments.pdf",
    "fig_intent_norm_districts.pdf",
    "fig_s2_dimensions.pdf",
    "fig_exit_apartments.pdf",
    "fig_exit_dims.pdf",
    "fig_tom_dims.pdf",
    "fig_metrics_panel_apartments.pdf",
    "fig_demand_map.pdf",
    "fig_supply_demand_bands.pdf",
]


def verify():
    """Faqat 11 ta kutilgan figura borligini va asosiy raqamlarni tekshiradi."""
    produced = sorted(f for f in os.listdir(config.FIG_DIR) if f.endswith(".pdf"))
    missing = [f for f in EXPECTED_FIGURES if f not in produced]
    extra = [f for f in produced if f not in EXPECTED_FIGURES]
    print("\n[verify] figuralar tekshiruvi:")
    print(f"  kutilgan: {len(EXPECTED_FIGURES)}, yaratilgan: {len(produced)}")
    if missing:
        print(f"  YETISHMAYDI: {missing}")
    if extra:
        print(f"  ORTIQCHA (o'chirilsin): {extra}")
    if not missing and not extra:
        print("  OK: aynan 11 ta figura, ortiqchasiz.")

    R = json.load(open(os.path.join(config.BUILD_DIR, "metrics.json")))
    w = R["window"]
    print("\n[verify] asosiy raqamlar (kunlik sanity-check):")
    print(f"  kvartiralar: {w['n_listings']}  e'lon-kun: {w['n_obs']}  jami ko'rish: {R['tot_views']}")
    print(f"  mediana tezlik: {R['med_vpd']}  top-10 konsentratsiya: {R['top10']}%")
    print(f"  chiqish darajasi: {R['exit_rate']}%  chiqish farqi: {R['exit_gap']}x")
    print(f"  CTR: {R['ctr']}%  bosishlar: {R['tot_clicks']}  saqlashlar: {R['tot_favs']}")
    print(f"  davr: {w['date_min']} -> {w['date_max']} ({w['n_days']} kesim)")
    return not missing and not extra


if __name__ == "__main__":
    pipeline.main()
    figures.main()
    ok = verify()
    print("\n[build] " + ("tayyor — hammasi joyida." if ok
                          else "OGOHLANTIRISH: figuralar ro'yxati mos kelmadi (yuqoriga qarang)."))
