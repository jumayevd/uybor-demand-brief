# Uybor.uz Housing-Demand Report — Automation Package

Turns a daily Uybor.uz listing scrape into the exact numbers and figures used in
the working paper *"Measuring Housing Demand from Online Listings: Evidence from
Tashkent."* Deterministic: the same input CSVs always produce the same output.

## Quick start

```bash
pip install pandas numpy matplotlib scipy
# put your scrape CSV(s) in ./data/ and edit config.CSV_INPUTS to point at them
python build.py
```

Outputs:
- `build/metrics.json` — every number in the report (headline, per-district, per-dimension)
- `build/L.pkl` — one row per listing (listing-level signals)
- `build/P.pkl` — the full cleaned daily panel (listing-day rows)
- `figures/fig_*.pdf` — all 13 figures

## Files

| File | Role | Edit it? |
|------|------|----------|
| `config.py` | Input CSVs, output paths, segment definition, bounds | **Yes — daily** |
| `pipeline.py` | Raw CSVs → clean panel → `metrics.json` | Only to change a definition |
| `figures.py` | `metrics.json` → 13 PDF figures | Only to restyle a figure |
| `build.py` | Runs pipeline then figures | No |

## Daily automation

The whole job is `python build.py`. For a cron/CI schedule:

1. Scraper appends today's rows to a rolling CSV that carries a `snapshot_date`
   column for every day.
2. Set `config.CSV_INPUTS = [("data/uybor_panel.csv", None)]`.
3. Run `python build.py`. Fresh `figures/*.pdf` and `build/metrics.json` appear.
4. (Optional) recompile the LaTeX paper, which reads only those figures.

The window is inferred from the data — earliest snapshot to latest — so as the
panel grows, every metric and figure updates automatically.

---

## Input CSV schema (columns the pipeline reads)

`listing_id, snapshot_date, category, city, district, price_usd, area_m2, rooms,
floor, is_new_building, renovation, building_material, latitude, longitude,
posted_at, views, clicks, favorites, is_vip, is_premium, is_urgently`

- `views, clicks, favorites` are **cumulative counters** (monotone non-decreasing
  per listing), so flows are computed as `last − first`.
- `snapshot_date` = the scrape date. If a CSV lacks it, stamp it in `config.CSV_INPUTS`.
- Apartments only: `category == "Квартира"`, `city == "Ташкент"`.

## Cleaning (config.BOUNDS)

Keep listings with price \$3k–5M, area 15–500 m², 1–8 rooms, \$/m² \$200–6000.
District labels are frozen to each listing's **first-observed** district (portal
geocoding flickers across snapshots), so every listing is counted once.

---

## The four demand signals

The framework rests on four listing signals, each validated in prior research as
a housing-demand proxy. Two are *attention-side*, two are *outcome-side*.

### Signal 1 — Views & view velocity
- **Definition.** Cumulative `views` = breadth of attention. **Demand velocity**
  `VPD = (views_last − views_first) / days_observed` = current intensity.
- **Why.** Buyer attention is the digital form of the buyer visits that
  search-and-matching theory treats as demand's observable face; portal click
  flows Granger-cause prices and liquidity (van Dijk & Francke 2018); views-per-
  property is the demand pillar of Realtor.com's Market Hotness index.
- **Reported as** median (attention is heavy-tailed).

### Signal 2 — Clicks & saves (normalized intent)
- **Definition.** New `clicks` (contact-form) and new `favorites` (saves) over the
  window. Reported **normalized**: rate per view, share of listings earning any,
  or per 1,000 listing-days.
- **Why.** A click or save is a costly, deliberate action. Low interest predicts
  longer time-on-market and price cuts (Pangallo & Loberto 2018); top-favorited
  homes sell faster and above list (Zillow 2018).

### Signal 3 — Exit rate
- **Definition (cohort method).** Let `S_t` = listing IDs scraped on day `t`,
  window `t0..T`. Cohort `C` = listings seen in the first week (`t ≤ t0+6`).
  A listing exits if absent from the terminal snapshot: `i ∉ S_T`.
  `ExitRate = #{i ∈ C : i ∉ S_T} / #C`.
- **Guards.** Exit judged only at the terminal date (a mid-window missed scrape
  can't fake an exit); identity confirmed by monotone view counters; survivors
  are right-censored.
- **Decomposition.** Uybor listings carry a ~43-day term (`config.LISTING_TERM_DAYS`).
  Each completed spell is split into early (<42d), renewal-wall (42–44d), and
  post-renewal (>44d). ~78% of exits are non-renewals at the wall, and those are
  the *highest*-velocity listings — non-renewal reveals success.
- **Why.** Delisting is the terminal outcome online interest anticipates
  (Pangallo & Loberto 2018; Loberto et al. 2022); exit conflates sale/withdrawal/
  expiration (de Wit & van der Klaauw 2013).

### Signal 4 — Time on market
- **Definition.** Completed spell (exited listings) = `last_seen − posted`.
  Stock age (active listings) = `today − posted`, median across live stock.
- **Institutional caveat.** On a fixed-term portal, completed ToM spikes at the
  43-day term and measures platform policy, not demand — so the usable duration
  signal is **stock age**.
- **Why.** ToM falls when demand rises (Genesove & Han 2012); constant-quality
  ToM indices measure liquidity (Carrillo & Williams 2019; van Dijk 2024).

---

## The 13 figures

Colour language: **gold** = median/typical, **teal** = mean/breadth,
**rust** = trough/soft, **purple** = index/duration.

| # | File | What it shows | Key metrics.json inputs |
|---|------|---------------|--------------------------|
| 1 | `fig_evidence_map` | The 4 signals + the studies validating each | (static, from literature) |
| 2 | `fig_concentration_apartments` | Velocity distribution + top-decile share | `med_vpd, mean_vpd, top10/25, bot50`; `L.vpd` |
| 3 | `fig_s1_dimensions` | Velocity by rooms / build type / day-of-week | `rooms_dims, nb_sec, nb_new, dow` |
| 4 | `fig_funnel_apartments` | Views → clicks → favorites attrition | `tot_views, tot_clicks, tot_favs` |
| 5 | `fig_wedge_apartments` | Velocity vs intent by price quintile | `quintiles` |
| 6 | `fig_intent_norm_districts` | Normalized click/fav incidence by district | `intent_norm` |
| 7 | `fig_s2_dimensions` | Intent by rooms / day-of-week | `rooms_dims, dow` |
| 8 | `fig_exit_apartments` | Velocity gap (exit vs stay) + renewal wall | `vpd_exit/stay/exit_gap, exit_*_pct, vpd_*_exit` |
| 9 | `fig_exit_dims` | Exit rate by district / rooms | `districts[*].absorp, exit_rooms` |
| 10 | `fig_tom_dims` | ToM term-wall + stock age by district / rooms | `districts[*].age, age_rooms`; `L.tom_completed` |
| 11 | `fig_metrics_panel_apartments` | District heatmap of the 4 framework signals | `districts, intent_norm` |
| 12 | `fig_supply_demand_bands` | Supply bars vs demand line by price band | `bands` |
| 13 | `fig_demand_map` | Bubble map (size=stock, colour=percentile) + ranked panel | `districts, vpct, map_pos2, map_rad2` |

The paper uses figures 1–13 except `fig_exit_apartments` and one of the
dimension panels are optional; include/exclude in LaTeX as needed. All 13 are
regenerated every run.

---

## Reproducibility notes

- **Deterministic.** No random seeds anywhere; identical CSVs → identical bytes.
- **Day-of-week** uses only consecutive-day snapshot pairs, so scrape gaps don't
  distort weekday patterns.
- **The demand-map bubble positions** are computed by a Dorling-style relaxation
  in `pipeline.py` (nudges overlapping circles apart, max displacement ≈ 1 km),
  so the map stays readable as stocks change.
- To verify a run, check `build/metrics.json → window` against your expected
  date range and listing count.
