"""
figures_en.py — ENGLISH figures for the working paper.
=====================================================
Same data pipeline and layout as figures.py (reach-based demand map, dynamic
axis limits so labels never overflow, 11 paper figures), but all text is in
English and the subplot titles used by the paper are restored. District names
stay in their Uzbek-Latin form (as the paper uses them).

Run:  python figures_en.py   (reads build/metrics.json + build/{L,P}.pkl)
Writes: figures_en/fig_*.pdf
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import config
import demand_map
from pipeline import cut_to_end as pipeline_cut

mpl.rcParams["font.family"] = "DejaVu Sans"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False

GOLD, TEAL, RUST, PURP = "#C8A15A", "#2E7D8A", "#B24C3C", "#6B5B95"
GREY, INK = "#9AA0A6", "#2b2b2b"
AVG = "#444444"

FIG_DIR = "figures_en"
os.makedirs(FIG_DIR, exist_ok=True)
R = L = P = SRC = None
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DOW_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load():
    global R, L, P, SRC
    R = json.load(open(os.path.join(config.BUILD_DIR, "metrics.json")))
    L = pd.read_pickle(os.path.join(config.BUILD_DIR, "L.pkl"))
    P = pd.read_pickle(os.path.join(config.BUILD_DIR, "P.pkl"))
    w = R["window"]
    SRC = ("Source: authors\u2019 calculations, Uybor.uz daily panel, apartments, "
           f"{w['date_min']} \u2013 {w['date_max']}.")


def out(name):
    return os.path.join(FIG_DIR, name)


def build_concentration_apartments():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    v = L.vpd.values
    med, mean = np.median(v), np.mean(v)
    bins = np.logspace(np.log10(max(v.min(), 0.1)), np.log10(v.max() + 1), 45)
    a1.hist(v, bins=bins, color=TEAL, alpha=0.55, edgecolor="white", lw=0.4)
    a1.set_xscale("log")
    a1.axvline(med, color=GOLD, lw=2.2)
    a1.axvline(mean, color=TEAL, lw=2.2)
    a1.text(med * 0.9, a1.get_ylim()[1] * 0.92, f"median {med:.1f}\nthe typical listing",
            color=GOLD, fontsize=8.5, fontweight="bold", ha="right")
    a1.text(mean * 1.1, a1.get_ylim()[1] * 0.74, f"mean {mean:.1f}\ndragged up by the tail",
            color=TEAL, fontsize=8.5, fontweight="bold")
    a1.set_xlabel("new views per day per listing (log scale)")
    a1.set_ylabel("number of listings")
    a1.set_title("(a)  Most listings trickle; a few flood",
                 fontsize=11, fontweight="bold", loc="left")
    vals = [R["top10"], R["top25"], R["bot50"]]
    b = a2.bar(["Top 10%", "Top 25%", "Bottom 50%"], vals,
               color=[TEAL, "#7FB0B8", GOLD], width=0.6)
    for bar, val in zip(b, vals):
        a2.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f"{val}%",
                ha="center", fontweight="bold", fontsize=11)
    a2.set_ylabel("share of all new views captured")
    a2.set_ylim(0, max(vals) * 1.18)
    a2.set_xlabel("listings ranked by attention")
    a2.set_title("(b)  Where the attention goes",
                 fontsize=11, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_concentration_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_concentration_apartments.pdf")


def build_s1_dimensions():
    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    rd = R["rooms_dims"]; ks = sorted(rd)
    vals = [rd[k]["vpd"] for k in ks]
    b = axs[0].bar([f"{k}-rm" for k in ks], vals, color=TEAL, width=0.62)
    for bar, val in zip(b, vals):
        axs[0].text(bar.get_x() + bar.get_width() / 2, val + 0.08, f"{val}",
                    ha="center", fontweight="bold", fontsize=10)
    axs[0].set_ylabel("median new views / day")
    axs[0].set_ylim(0, max(vals) * 1.22)
    axs[0].set_title("(a)  Velocity by room count",
                     fontsize=10.5, fontweight="bold", loc="left")
    nb = [R["nb_sec"], R["nb_new"]]
    b = axs[1].bar(["Secondary", "New build"], nb, color=[GOLD, TEAL], width=0.5)
    for bar, val in zip(b, nb):
        axs[1].text(bar.get_x() + bar.get_width() / 2, val + 0.08, f"{val}",
                    ha="center", fontweight="bold", fontsize=11)
    axs[1].set_ylabel("median new views / day")
    axs[1].set_ylim(0, max(nb) * 1.22)
    axs[1].set_title("(b)  Secondary vs new build",
                     fontsize=10.5, fontweight="bold", loc="left")
    dv = [R["dow"][d]["vpl"] for d in DOW_KEYS]
    cols = [TEAL if x < max(dv) else "#1d5f6b" for x in dv]
    b = axs[2].bar(DAYS_EN, dv, color=cols, width=0.62)
    for bar, val in zip(b, dv):
        axs[2].text(bar.get_x() + bar.get_width() / 2, val + 0.15, f"{val}",
                    ha="center", fontsize=9, fontweight="bold")
    axs[2].set_ylabel("mean new views per listing-day")
    axs[2].set_ylim(0, max(dv) * 1.2)
    axs[2].set_title("(c)  Attention by day of week",
                     fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_s1_dimensions.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_s1_dimensions.pdf")


def build_wedge_apartments():
    Q = R["quintiles"]; ql = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    qlab = ["Q1\n\u2264$" + str(Q['Q1']['pmax'] // 1000) + "k",
            "Q2\n$" + str(Q['Q2']['pmin'] // 1000) + "-" + str(Q['Q2']['pmax'] // 1000) + "k",
            "Q3\n$" + str(Q['Q3']['pmin'] // 1000) + "-" + str(Q['Q3']['pmax'] // 1000) + "k",
            "Q4\n$" + str(Q['Q4']['pmin'] // 1000) + "-" + str(Q['Q4']['pmax'] // 1000) + "k",
            "Q5\n\u2265$" + str(Q['Q5']['pmin'] // 1000) + "k"]
    vpd_q = [Q[q]["vpd"] for q in ql]
    ca = [Q[q]["clicka"] for q in ql]; fa = [Q[q]["fava"] for q in ql]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    cols = [TEAL] * 5; cols[3] = RUST
    a1.bar(range(5), vpd_q, color=cols, width=0.68)
    for i, vv in enumerate(vpd_q):
        a1.text(i, vv + 0.12, f"{vv}", ha="center", fontweight="bold", fontsize=10)
    a1.set_xticks(range(5)); a1.set_xticklabels(qlab, fontsize=8.3)
    a1.set_ylabel("median new views / day"); a1.set_ylim(0, max(vpd_q) * 1.25)
    a1.set_title("(a)  Raw attention: high at both ends",
                 fontsize=11, fontweight="bold", loc="left")
    x = np.arange(5); w = 0.38
    a2.bar(x - w / 2, ca, w, color=TEAL, label="earned a click")
    a2.bar(x + w / 2, fa, w, color=GOLD, label="earned a save")
    for i in range(5):
        a2.text(i - w / 2, ca[i] + 0.4, f"{ca[i]}", ha="center", fontsize=8.2,
                color=TEAL, fontweight="bold")
        a2.text(i + w / 2, fa[i] + 0.4, f"{fa[i]}", ha="center", fontsize=8.2,
                color=GOLD, fontweight="bold")
    a2.set_xticks(x); a2.set_xticklabels(qlab, fontsize=8.3)
    a2.set_ylabel("% of listings"); a2.set_ylim(0, max(max(ca), max(fa)) * 1.22)
    a2.set_title("(b)  Intent: falls monotonically with price",
                 fontsize=11, fontweight="bold", loc="left")
    a2.legend(frameon=False, fontsize=9)
    plt.tight_layout()
    plt.savefig(out("fig_wedge_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_wedge_apartments.pdf")


def build_intent_norm_districts():
    IN = R["intent_norm"]
    order = sorted(IN, key=lambda d: -IN[d]["clicka"])
    ca = [IN[d]["clicka"] for d in order]
    fa = [IN[d]["fava"] for d in order]
    avg_c = float(np.mean([IN[d]["clicka"] for d in IN]))
    avg_f = float(np.mean([IN[d]["fava"] for d in IN]))
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    x = np.arange(len(order)); w = 0.4
    ax.bar(x - w / 2, ca, w, color=TEAL, label="% of listings earning a click")
    ax.bar(x + w / 2, fa, w, color=GOLD, label="% of listings earning a save")
    for i in range(len(order)):
        ax.text(i - w / 2, ca[i] + 0.5, f"{ca[i]:.0f}", ha="center", fontsize=8.2,
                color=TEAL, fontweight="bold")
        ax.text(i + w / 2, fa[i] + 0.5, f"{fa[i]:.0f}", ha="center", fontsize=8.2,
                color=GOLD, fontweight="bold")
    ax.axhline(avg_c, color=TEAL, lw=1.2, ls="--", alpha=0.7)
    ax.axhline(avg_f, color="#a07d2e", lw=1.2, ls="--", alpha=0.7)
    lbl_bbox = dict(facecolor="white", edgecolor="none", pad=1.2)
    ax.text(len(order) - 0.35, avg_c, f"mean click {avg_c:.1f}%",
            fontsize=7.5, color=TEAL, ha="left", va="center", fontweight="bold",
            bbox=lbl_bbox)
    ax.text(len(order) - 0.35, avg_f, f"mean save {avg_f:.1f}%",
            fontsize=7.5, color="#a07d2e", ha="left", va="center", fontweight="bold",
            bbox=lbl_bbox)
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=32, ha="right", fontsize=8.6)
    ax.set_xlim(-0.7, len(order) - 0.5 + 2.2)
    ax.set_ylabel("% of district listings")
    ax.set_ylim(0, max(max(ca), max(fa)) * 1.25)
    ax.set_title("Intent incidence by district (normalized): share of listings earning any click or save",
                 fontsize=11.5, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    plt.tight_layout()
    plt.savefig(out("fig_intent_norm_districts.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_intent_norm_districts.pdf")


def build_s2_dimensions():
    rd = R["rooms_dims"]; ks = sorted(rd)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ca = [rd[k]["clicka"] for k in ks]; fa = [rd[k]["fava"] for k in ks]
    x = np.arange(len(ks)); w = 0.38
    a1.bar(x - w / 2, ca, w, color=TEAL, label="earned a click")
    a1.bar(x + w / 2, fa, w, color=GOLD, label="earned a save")
    for i in range(len(ks)):
        a1.text(i - w / 2, ca[i] + 0.35, f"{ca[i]}", ha="center", fontsize=8.4,
                color=TEAL, fontweight="bold")
        a1.text(i + w / 2, fa[i] + 0.35, f"{fa[i]}", ha="center", fontsize=8.4,
                color=GOLD, fontweight="bold")
    a1.set_xticks(x); a1.set_xticklabels([f"{k}-rm" for k in ks])
    a1.set_ylabel("% of listings"); a1.set_ylim(0, max(max(ca), max(fa)) * 1.28)
    a1.set_title("(a)  Intent incidence by room count",
                 fontsize=10.5, fontweight="bold", loc="left")
    a1.legend(frameon=False, fontsize=8.5)
    ck = [R["dow"][d]["cpk"] for d in DOW_KEYS]
    fk = [R["dow"][d]["fpk"] for d in DOW_KEYS]
    a2.bar(np.arange(7) - w / 2, ck, w, color=TEAL, label="clicks / 1,000 listing-days")
    a2.bar(np.arange(7) + w / 2, fk, w, color=GOLD, label="saves / 1,000 listing-days")
    for i in range(7):
        a2.text(i - w / 2, ck[i] + 0.4, f"{ck[i]:.0f}", ha="center", fontsize=8,
                color=TEAL, fontweight="bold")
        a2.text(i + w / 2, fk[i] + 0.4, f"{fk[i]:.1f}", ha="center", fontsize=7.6,
                color=GOLD, fontweight="bold")
    a2.set_xticks(range(7)); a2.set_xticklabels(DAYS_EN)
    a2.set_ylabel("intent per 1,000 listing-days"); a2.set_ylim(0, max(max(ck), max(fk)) * 1.2)
    a2.set_title("(b)  Intent by day of week",
                 fontsize=10.5, fontweight="bold", loc="left")
    a2.legend(frameon=False, fontsize=8.5)
    plt.tight_layout()
    plt.savefig(out("fig_s2_dimensions.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_s2_dimensions.pdf")


def build_exit_apartments():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    # (a) demand (view velocity) of still-active vs. truly-exiting journeys
    meds = [R["vpd_active_med"], R["vpd_trueexit_med"]]
    means = [R["vpd_active_mean"], R["vpd_trueexit_mean"]]
    b = a1.bar(["Still active\n(censored)", "Exited\n(true exit)"], meds,
               color=[GOLD, TEAL], width=0.55)
    top1 = max(meds) * 1.6
    for bar, md, mn in zip(b, meds, means):
        a1.text(bar.get_x() + bar.get_width() / 2, md + top1 * 0.04,
                f"median {md}\n(mean {mn})", ha="center", va="bottom",
                fontweight="bold", fontsize=9.5)
    a1.set_ylabel("median new views per day"); a1.set_ylim(0, top1)
    a1.set_title("(a)  Demand of exited vs. surviving listings",
                 fontsize=11, fontweight="bold", loc="left")
    # (b) exit timing around the 43-day platform term (no per-bar VPD labels)
    labs = ["Early exit\n(<42 days)", "At renewal wall\n(42\u201344 days)",
            "After renewal\n(>44 days)"]
    shares = [R["exit_early_pct"], R["exit_wall_pct"], R["exit_late_pct"]]
    cols = [GOLD, TEAL, RUST]
    b = a2.bar(labs, shares, color=cols, width=0.6)
    for bar, s in zip(b, shares):
        a2.text(bar.get_x() + bar.get_width() / 2, s + 1.6, f"{s}%",
                ha="center", fontweight="bold", fontsize=10.5)
    a2.set_ylabel("share of disappeared listings"); a2.set_ylim(0, max(shares) * 1.16)
    a2.set_title("(b)  Most disappearances are non-renewals at the 43-day term",
                 fontsize=11, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_exit_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_exit_apartments.pdf")


def build_exit_dims():
    dd = R["districts"]
    order = sorted(dd, key=lambda d: -dd[d]["absorp"])
    ex = [dd[d]["absorp"] for d in order]
    avg_ex = float(np.mean([dd[d]["absorp"] for d in dd]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                 gridspec_kw={"width_ratios": [1.7, 1]})
    cmap = LinearSegmentedColormap.from_list("g", ["#f5ecd8", GOLD])
    n = [(e - min(ex)) / (max(ex) - min(ex)) for e in ex]
    a1.bar(range(len(order)), ex, color=[cmap(0.25 + 0.75 * v) for v in n], width=0.66)
    for i, e in enumerate(ex):
        a1.annotate(f"{e:.0f}%", (i, e), xytext=(0, 3), textcoords="offset points",
                     ha="center", va="bottom", fontsize=8.4, fontweight="bold")
    a1.set_xticks(range(len(order)))
    a1.set_xticklabels(order, rotation=32, ha="right", fontsize=8.4)
    extop = max(max(ex), avg_ex, max(R["exit_rooms"].values())) * 1.18
    a1.set_ylabel("30-day exit probability (%)"); a1.set_ylim(0, extop)
    a1.axhline(avg_ex, color=AVG, lw=1.3, ls="--")
    a1.text(len(order) - 0.5, avg_ex + extop * 0.015, f"district avg {avg_ex:.0f}%",
            fontsize=7.8, color=AVG, ha="right", fontweight="bold")
    a1.set_title("(a)  Exit probability by district",
                 fontsize=10.5, fontweight="bold", loc="left")
    er = {int(k): v for k, v in R["exit_rooms"].items()}
    ks2 = sorted(er)
    b = a2.bar([f"{k}-rm" for k in ks2], [er[k] for k in ks2], color=GOLD, width=0.62)
    for bar, k in zip(b, ks2):
        a2.annotate(f"{er[k]:.0f}%",
                ha="center", fontweight="bold", fontsize=9.5,
                     xy=(bar.get_x() + bar.get_width() / 2, er[k]), xytext=(0, 3),
                     textcoords="offset points", va="bottom")
    a2.set_ylabel("30-day exit probability (%)"); a2.set_ylim(0, extop)
    a2.set_title("(b)  Exit probability by room count",
                 fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_exit_dims.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_exit_dims.pdf")


def build_tom_dims():
    dd = R["districts"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3),
                                 gridspec_kw={"width_ratios": [1.7, 1]})
    order = sorted(dd, key=lambda d: dd[d]["age"])
    ages = [dd[d]["age"] for d in order]
    # reference line: city-wide median over ALL active listings (same basis as the
    # room-count bars), not the unweighted mean of the 12 district medians
    avg_age = float(R["stockage_med"])
    cmap = LinearSegmentedColormap.from_list("p", ["#ece9f2", PURP])
    nrm = [(a - min(ages)) / (max(ages) - min(ages)) for a in ages]
    a1.barh(range(len(order)), ages, color=[cmap(0.2 + 0.8 * (1 - v)) for v in nrm],
            height=0.68)
    for i, a in enumerate(ages):
        a1.text(a + 0.6, i, f"{a:.0f}", va="center", fontsize=8, fontweight="bold")
    a1.set_yticks(range(len(order))); a1.set_yticklabels(order, fontsize=8.4)
    a1.invert_yaxis()
    a1.set_xlabel("median time on market (days)"); a1.set_xlim(0, max(ages) * 1.18)
    a1.axvline(avg_age, color=AVG, lw=1.3, ls="--")
    a1.text(avg_age + 0.5, len(order) - 0.5, f"city median {avg_age:.0f}",
            fontsize=7.8, color=AVG, va="center", fontweight="bold")
    a1.set_title("(a)  Time on market by district",
                 fontsize=10.5, fontweight="bold", loc="left")
    ar = {int(k): v for k, v in R["age_rooms"].items()}
    ks3 = sorted(ar)
    b = a2.bar([f"{k}-rm" for k in ks3], [ar[k] for k in ks3], color=PURP, width=0.62)
    for bar, k in zip(b, ks3):
        a2.text(bar.get_x() + bar.get_width() / 2, ar[k] + 1, f"{ar[k]}",
                ha="center", fontweight="bold", fontsize=9.5)
    a2.set_ylabel("median days on market"); a2.set_ylim(0, max(max(ar.values()), avg_age) * 1.15)
    a2.axhline(avg_age, color=AVG, lw=1.3, ls="--")
    a2.text(len(ks3) - 0.5, avg_age + 0.6, f"city median {avg_age:.0f}",
            fontsize=7.8, color=AVG, ha="right", va="bottom", fontweight="bold")
    a2.set_title("(b)  Time on market by room count",
                 fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_tom_dims.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_tom_dims.pdf")


def build_metrics_panel_apartments():
    d = R["districts"]; intent = R["intent_norm"]
    rows = []
    for dist in d:
        rows.append(dict(district=dist, vpd=d[dist]["vpd"],
                         click=intent[dist]["clicka"],
                         exit=d[dist]["absorp"], age=d[dist]["age"]))
    D = pd.DataFrame(rows).set_index("district").sort_values("vpd", ascending=False)
    avg_row = dict(vpd=round(D.vpd.mean(), 1), click=round(D.click.mean(), 1),
                   exit=round(D["exit"].mean(), 0), age=round(D.age.mean(), 0))
    cols = [("vpd", "Views & Velocity", "median new views / day", False, "{:.1f}"),
            ("click", "Clicks & Saves", "% of listings w/ a click", False, "{:.0f}%"),
            ("exit", "Exit Probability", "% exiting within 30 days", False, "{:.0f}%"),
            ("age", "Time on Market", "median days on market", True, "{:.0f}")]
    cmaps = {"vpd": LinearSegmentedColormap.from_list("t", ["#e8f0f1", TEAL]),
             "click": LinearSegmentedColormap.from_list("g", ["#f5ecd8", GOLD]),
             "exit": LinearSegmentedColormap.from_list("r2", ["#f4e6e2", RUST]),
             "age": LinearSegmentedColormap.from_list("p", ["#ece9f2", PURP])}
    colcolor = {"vpd": TEAL, "click": GOLD, "exit": RUST, "age": PURP}

    def shade(vals, invert):
        v = np.array(vals, float); lo, hi = v.min(), v.max()
        n = (v - lo) / (hi - lo + 1e-9)
        return 1 - n if invert else n

    nrows = len(D) + 1
    fig, ax = plt.subplots(figsize=(9.6, 7.2)); ax.axis("off")
    ax.set_xlim(0, 4); ax.set_ylim(-0.7, nrows + 0.7)
    for j, (key, title, sub, inv, fmt) in enumerate(cols):
        n = shade(D[key], inv)
        ax.text(j + 0.5, nrows + 0.2, title, ha="center", va="bottom", fontweight="bold",
                fontsize=9.5, color=colcolor[key])
        ax.text(j + 0.5, nrows - 0.18, sub, ha="center", fontsize=7.1, color=GREY)
        for rr in range(len(D)):
            val = D[key].iloc[rr]; c = cmaps[key](0.15 + 0.85 * n[rr])
            tc = "white" if n[rr] > 0.55 else INK
            ax.add_patch(plt.Rectangle((j + 0.06, nrows - 1 - rr - 0.4), 0.88, 0.8,
                                       fc=c, ec="white", lw=1.6))
            ax.text(j + 0.5, nrows - 1 - rr, fmt.format(val), ha="center",
                    va="center", fontsize=9.3, color=tc,
                    fontweight="bold" if n[rr] > 0.8 else "normal")
        ax.add_patch(plt.Rectangle((j + 0.06, -0.4), 0.88, 0.8,
                                   fc="#e6e6e6", ec="white", lw=1.6))
        ax.text(j + 0.5, 0, fmt.format(avg_row[key]), ha="center", va="center",
                fontsize=9.3, color=INK, fontweight="bold")
    for rr in range(len(D)):
        ax.text(-0.06, nrows - 1 - rr, D.index[rr], ha="right", va="center",
                fontsize=9, color=INK)
    ax.text(-0.06, 0, "DISTRICT AVERAGE", ha="right", va="center",
            fontsize=8.5, color=INK, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out("fig_metrics_panel_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_metrics_panel_apartments.pdf")


def build_demand_map():
    """Fig 4 — district choropleth of demand (see demand_map.py)."""
    demand_map.draw(L, P, out("fig_demand_map.pdf"), dict(
        title_a="(a)  Reach: share of all new views",
        title_b="(b)  Intensity: new views per active listing-day",
        cbar_a="share of all new views (%, square-root scale)",
        cbar_b="new views per active listing-day",
        footnote=("District territories approximated from listing locations (each point "
                  "takes the district of its nearest listings). Arrow on a colour bar: values "
                  "above it share the darkest shade.  * fewer than 40 listings.")))
    print("  fig_demand_map.pdf")


def build_supply_demand_bands():
    bl = [b for b in config.PRICE_BAND_LABELS if b in R["bands"]]
    sup = [R["bands"][b]["supply"] for b in bl]
    dem = [R["bands"][b]["medvpd"] for b in bl]
    n = len(bl)
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.bar(range(n), sup, color="#e7e2da", edgecolor="#c9c2b6", width=0.72, zorder=2)
    for i, s in enumerate(sup):
        ax1.text(i, s + max(sup) * 0.02, f"{s}", ha="center", fontsize=8.5, color=GREY)
    ax1.set_ylabel("Listings (supply)", fontsize=10); ax1.set_ylim(0, max(sup) * 1.14)
    ax1.set_xticks(range(n)); ax1.set_xticklabels(bl, fontsize=9)
    ax1.set_xlabel("Price band (USD)")
    ax2 = ax1.twinx(); ax2.spines["top"].set_visible(False)
    ax2.plot(range(n), dem, color=RUST, marker="o", lw=2.4, ms=7, zorder=3)
    for i, dv in enumerate(dem):
        ax2.text(i + 0.08, dv + 0.25, f"{dv}", fontsize=9, color=RUST, fontweight="bold")
    ax2.set_ylabel("Median new views / day (demand)", color=RUST, fontsize=10)
    ax2.tick_params(axis="y", colors=RUST); ax2.set_ylim(0, max(dem) * 1.18)
    def band(b):   # "50-75k" -> "$50–75k" (escaped $ so mathtext doesn't trigger)
        return "\\$" + b.replace("-", "–")
    ax1.set_title(f"Supply peaks at {band(bl[int(np.argmax(sup))])}; "
                  f"demand intensity peaks at {band(bl[int(np.argmax(dem))])}",
                  fontsize=12, fontweight="bold", loc="left", pad=12)
    plt.tight_layout()
    plt.savefig(out("fig_supply_demand_bands.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_supply_demand_bands.pdf")


def build_tightness_districts():
    """Fig 12 — market tightness by district (horizontal).

    Tightness_j = (sum of new views) / (sum of active listing-days) across all
    listings in district j (Eq. 3): aggregate attention per active listing-day.
    The dashed reference line is the same ratio for the whole city. Districts
    with fewer than 40 listings are drawn in a separate colour, since their
    ratios rest on thin data.
    """
    NMIN = 40
    g = L.groupby("district").agg(nv=("nv", "sum"), days=("days_obs", "sum"),
                                  nlist=("nv", "size"))
    g = g[g.days > 0].copy()
    g["tight"] = g.nv / g.days
    city = float(L.nv.sum() / L.days_obs.sum())
    g = g.sort_values("tight", ascending=False)
    order = list(g.index)                    # highest tightness first
    vals = [float(g.tight[d]) for d in order]
    ns = [int(g.nlist[d]) for d in order]
    cols = [GOLD if n < NMIN else TEAL for n in ns]
    y = np.arange(len(order))[::-1]          # so the first entry sits at the top

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.barh(y, vals, color=cols, height=0.72, zorder=2)
    xmax = max(max(vals), city) * 1.14
    for yi, v, n in zip(y, vals, ns):
        ax.text(xmax * 0.008, yi, f"n={n}", va="center", ha="left",
                fontsize=7, color="white", fontweight="bold", zorder=4)
        ax.text(v + xmax * 0.012, yi, f"{v:.1f}", va="center", ha="left",
                fontsize=8.6, color=INK, fontweight="bold")
    ax.axvline(city, color=AVG, lw=1.3, ls="--", zorder=3)
    ax.text(city, len(order) - 0.35, f"city average {city:.1f}", ha="center",
            va="bottom", fontsize=8, color=AVG, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(order, fontsize=9)
    ax.set_xlim(0, xmax); ax.set_ylim(-0.7, len(order) - 0.2)
    ax.set_xlabel("market tightness:  new views per active listing-day")
    ax.set_title("Market tightness by district",
                 fontsize=12.5, fontweight="bold", loc="left", pad=14)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=TEAL, label=f"n ≥ {NMIN} listings"),
                       Patch(fc=GOLD, label=f"n < {NMIN} listings (interpret with caution)")],
              frameon=False, fontsize=8.2, loc="lower right")
    plt.tight_layout()
    plt.savefig(out("fig_tightness_districts.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_tightness_districts.pdf")


def _hedonic():
    """Hedonic panel + OLS fit for the promotion figure (Eq. 6).

    Reads the raw CSVs directly (they carry floor/material/promotion columns the
    core pipeline drops), rebuilds the listing-day panel with the same segment
    and plausibility filters as pipeline.clean, forms daily new-view velocity per
    interval, and fits ln(1+vpd) on characteristics + a paid-promotion flag +
    day fixed effects by OLS (numpy lstsq; no statsmodels in this env).

    Returns dict: r2, adj_fold (exp of promotion coef), raw_fold (unadjusted
    mean ratio), n_obs, n_listings, promo_share.
    """
    need = ["listing_id", "snapshot_date", "category", "city", "district",
            "price_usd", "area_m2", "rooms", "floor", "total_floors",
            "is_new_building", "renovation", "building_material",
            "is_vip", "is_premium", "is_urgently", "views"]
    frames = []
    for path, sd in config.CSV_INPUTS:
        df = pd.read_csv(path, usecols=lambda c: c in need, low_memory=False)
        if sd is not None:
            df["snapshot_date"] = sd
        frames.append(df)
    df = pipeline_cut(pd.concat(frames, ignore_index=True))
    for col in need:
        if col not in df.columns:
            df[col] = np.nan
    df = df.drop_duplicates(subset=["listing_id", "snapshot_date"], keep="first")
    df = df[(df.category == config.CATEGORY) & (df.city == config.CITY)].copy()
    df = df[df.district.isin(config.DISTRICT_MAP)]
    df["snapshot_date"] = pd.to_datetime(df.snapshot_date)
    df["price_usd"] = pd.to_numeric(df.price_usd, errors="coerce")
    df["area_m2"] = pd.to_numeric(df.area_m2, errors="coerce")
    df["rooms_n"] = pd.to_numeric(df.rooms, errors="coerce")
    df["views"] = pd.to_numeric(df.views, errors="coerce")
    df["ppsm"] = df.price_usd / df.area_m2
    b = config.BOUNDS
    df = df[df.price_usd.between(*b["price_usd"]) & df.area_m2.between(*b["area_m2"])
            & df.rooms_n.between(*b["rooms"]) & df.ppsm.between(*b["ppsm"])]

    # listing-day new-view velocity over each observed interval
    df = df.sort_values(["listing_id", "snapshot_date"])
    grp = df.groupby("listing_id")
    df["dv"] = grp["views"].diff().clip(lower=0)
    df["gap"] = grp["snapshot_date"].diff().dt.days
    d = df[(df.gap > 0) & df.dv.notna()].copy()
    d["vpd_it"] = d.dv / d.gap

    def b01(s):
        m = {True: 1, False: 0, "true": 1, "false": 0, "t": 1, "f": 0,
             "True": 1, "False": 0, 1: 1, 0: 0, "1": 1, "0": 0}
        return pd.to_numeric(s.map(m), errors="coerce").fillna(0.0)

    promo = ((b01(d.is_vip) + b01(d.is_premium) + b01(d.is_urgently)) > 0).astype(float)
    d = d.assign(promo=promo.values)

    y = np.log1p(d.vpd_it.to_numpy(float))
    cols, names = [], []

    def add(name, arr):
        cols.append(np.asarray(arr, float)); names.append(name)

    add("const", np.ones(len(d)))
    add("ln_area", np.log(d.area_m2.to_numpy(float)))
    add("ln_price", np.log(d.price_usd.to_numpy(float)))
    fl = pd.to_numeric(d.floor, errors="coerce"); fl = fl.fillna(fl.median())
    tf = pd.to_numeric(d.total_floors, errors="coerce"); tf = tf.fillna(tf.median())
    add("floor", fl.to_numpy(float))
    add("total_floors", tf.to_numpy(float))
    add("new_build", b01(d.is_new_building).to_numpy(float))
    add("promo", d.promo.to_numpy(float))
    for pref, ser in [("rm", d.rooms_n.astype("Int64").astype(str)),
                      ("reno", d.renovation.astype(str)),
                      ("mat", d.building_material.astype(str)),
                      ("day", d.snapshot_date.dt.strftime("%Y-%m-%d"))]:
        du = pd.get_dummies(ser, prefix=pref, drop_first=True)
        for c in du.columns:
            add(c, du[c].to_numpy(float))

    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    ss_res = float((resid ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    coef_promo = float(beta[names.index("promo")])
    m1 = d.vpd_it[d.promo == 1].mean()
    m0 = d.vpd_it[d.promo == 0].mean()
    raw_fold = float(m1 / m0) if m0 > 0 else float("nan")
    return dict(r2=r2, adj_fold=float(np.exp(coef_promo)), raw_fold=raw_fold,
                n_obs=int(len(d)), n_listings=int(d.listing_id.nunique()),
                promo_share=float(d.promo.mean() * 100))


def build_hedonic_results():
    """Fig 13 — what a hedonic model says about paid promotion.

    (a) Effect of paid promotion on daily views: raw mean ratio vs. the
        hedonic-adjusted multiple (exp of the promotion coefficient, holding
        size, price, floor, building, room count, renovation, material and the
        calendar day fixed).
    (b) Share of the variation in ln(1+views) the observables explain (model
        R^2) vs. what remains unexplained.
    """
    h = _hedonic()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))

    labs = ["Raw\n(unadjusted)", "Hedonic-\nadjusted"]
    vals = [h["raw_fold"], h["adj_fold"]]
    b = a1.bar(labs, vals, color=[GREY, TEAL], width=0.5)
    for bar, v in zip(b, vals):
        a1.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.02, f"{v:.2f}×",
                ha="center", fontweight="bold", fontsize=12)
    a1.set_ylabel("daily views vs. an identical non-promoted listing")
    a1.set_ylim(0, max(vals) * 1.2)
    a1.axhline(1, color=INK, lw=0.8, ls=":")
    a1.set_title("(a)  Paid promotion multiplies daily views",
                 fontsize=11, fontweight="bold", loc="left")
    a1.text(0.5, max(vals) * 1.1,
            f"n = {h['n_obs']:,} listing-days, {h['n_listings']:,} apartments; "
            f"{h['promo_share']:.0f}% promoted",
            ha="center", fontsize=7.6, color=GREY)

    r2pct = h["r2"] * 100
    parts = [r2pct, 100 - r2pct]
    plabs = ["Explained by\nobservables", "Unexplained\n(demand signal + noise)"]
    b = a2.bar(plabs, parts, color=[PURP, "#d9d4e2"], width=0.5)
    for bar, v in zip(b, parts):
        a2.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontweight="bold", fontsize=12,
                color=INK)
    a2.set_ylabel("% of variation in ln(1 + daily views)")
    a2.set_ylim(0, 100)
    a2.set_title("(b)  Characteristics explain little of the variation",
                 fontsize=11, fontweight="bold", loc="left")

    fig.text(0.5, -0.03,
             "Hedonic OLS of ln(1+daily views) on log area, log price, floor, "
             "building height, new-build, room-count, renovation, material and "
             "day fixed effects.", ha="center", fontsize=7, color=GREY)
    plt.tight_layout()
    plt.savefig(out("fig_hedonic_results.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_hedonic_results.pdf")


def build_dynamics_districts():
    """Fig 10 (paper) — demand dynamics across three monthly windows
    (24th-to-24th): (a) demand reach and (b) click-through rate, by district."""
    import timeseries as TS
    anchors = TS.resolve_anchors(P)
    dist = pd.concat([TS.series(P[P.district_en == d], anchors, d)
                      for d in sorted(P.district_en.unique())], ignore_index=True)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(14, 11))
    TS.draw_multihorizon(a1, dist, "new_views", "new views in the period",
                         "(a)  Demand reach by district", "{:,.0f}",
                         thousands=True, title_size=12)
    TS.draw_multihorizon(a2, dist, "ctr_pct", "clicks per 100 new views",
                         "(b)  Click-through rate by district", "{:.2f}", title_size=12)
    plt.tight_layout()
    plt.savefig(out("fig_dynamics_districts.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_dynamics_districts.pdf")


ALL_FIGURES = [
    build_concentration_apartments,
    build_s1_dimensions,
    build_wedge_apartments,
    build_intent_norm_districts,
    build_s2_dimensions,
    build_exit_apartments,
    build_exit_dims,
    build_tom_dims,
    build_metrics_panel_apartments,
    build_demand_map,
    build_supply_demand_bands,
    build_tightness_districts,
    build_hedonic_results,
    build_dynamics_districts,
]


def main():
    _load()
    print("[figures_en] English figures:", len(ALL_FIGURES), "->", FIG_DIR)
    for fn in ALL_FIGURES:
        fn()
    print("[figures_en] done")


if __name__ == "__main__":
    main()
