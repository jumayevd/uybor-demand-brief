"""
figures.py — barcha figuralarni Uzbek tilida yaratadi (build/metrics.json dan)
=============================================================================
O'zgarishlar (foydalanuvchi so'rovi bo'yicha):
  - Lit review'dagi rangli 4-signal chart olib tashlandi (faqat jadval qoldi)
  - Funnel (views->clicks->favorites) aniq va toza
  - Tuman grafiklariga tuman o'rtachasi (mean) chizig'i qo'shildi (makro daraja)
  - Renewal exit aniqroq izohlangan
  - ToM 43-kun spike olib tashlandi
  - Bubble map: geografik joylashuv aniq, bir xil rang, o'lcham = qamrov (reach)
  - Barcha matnlar Uzbek lotin
Ingliz texnik atamalar figuralarda saqlanadi (masalan VPD, reach).
"""
import pandas as pd, numpy as np, json, os
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Ellipse
import config

mpl.rcParams["font.family"] = "DejaVu Sans"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False

GOLD, TEAL, RUST, PURP = "#C8A15A", "#2E7D8A", "#B24C3C", "#6B5B95"
GREY, INK = "#9AA0A6", "#2b2b2b"
AVG = "#444444"

os.makedirs(config.FIG_DIR, exist_ok=True)
R = L = P = SRC = None
DAYS_UZ = ["Dush", "Sesh", "Chor", "Pay", "Juma", "Shan", "Yak"]
DOW_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _load():
    global R, L, P, SRC
    R = json.load(open(os.path.join(config.BUILD_DIR, "metrics.json")))
    L = pd.read_pickle(os.path.join(config.BUILD_DIR, "L.pkl"))
    P = pd.read_pickle(os.path.join(config.BUILD_DIR, "P.pkl"))
    SRC = ("Manba: mualliflar hisob-kitobi, Uybor.uz kunlik panel, kvartiralar, "
           f"{R['window']['date_min']} \u2013 {R['window']['date_max']}.")


def out(name):
    return os.path.join(config.FIG_DIR, name)


# CHANGE 1: evidence_map (rangli lit-review chart) OLIB TASHLANDI.


def build_concentration_apartments():
    """S1: Talab tezligi konsentratsiyasi (og'ir dumli taqsimot)."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    v = L.vpd.values
    med, mean = np.median(v), np.mean(v)
    bins = np.logspace(np.log10(max(v.min(), 0.1)), np.log10(v.max() + 1), 45)
    a1.hist(v, bins=bins, color=TEAL, alpha=0.55, edgecolor="white", lw=0.4)
    a1.set_xscale("log")
    a1.axvline(med, color=GOLD, lw=2.2)
    a1.axvline(mean, color=TEAL, lw=2.2)
    a1.text(med * 0.9, a1.get_ylim()[1] * 0.92, f"mediana {med:.1f}\ntipik e'lon",
            color=GOLD, fontsize=8.5, fontweight="bold", ha="right")
    a1.text(mean * 1.1, a1.get_ylim()[1] * 0.74, f"o'rtacha {mean:.1f}\n\"dum\" tortadi",
            color=TEAL, fontsize=8.5, fontweight="bold")
    a1.set_xlabel("kunlik yangi ko'rishlar (log shkala)")
    a1.set_ylabel("e'lonlar soni")
    a1.set_title("(a)  Ko'pchilik oz, ozchilik ko'p e'tibor oladi",
                 fontsize=10.5, fontweight="bold", loc="left")
    vals = [R["top10"], R["top25"], R["bot50"]]
    b = a2.bar(["Yuqori 10%", "Yuqori 25%", "Quyi 50%"], vals,
               color=[TEAL, "#7FB0B8", GOLD], width=0.6)
    for bar, val in zip(b, vals):
        a2.text(bar.get_x() + bar.get_width() / 2, val + 1.5, f"{val}%",
                ha="center", fontweight="bold", fontsize=11)
    a2.set_ylabel("barcha yangi ko'rishlar ulushi, %")
    a2.set_ylim(0, 90)
    a2.set_xlabel("e'tibor bo'yicha saralangan e'lonlar")
    a2.set_title("(b)  E'tibor qayerga to'planadi",
                 fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_concentration_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_concentration_apartments.pdf")


def build_s1_dimensions():
    """S1: Tezlik xonalar / bino turi / hafta kuni bo'yicha."""
    fig, axs = plt.subplots(1, 3, figsize=(13, 4))
    rd = R["rooms_dims"]; ks = sorted(rd)
    vals = [rd[k]["vpd"] for k in ks]
    b = axs[0].bar([f"{k}-xona" for k in ks], vals, color=TEAL, width=0.62)
    for bar, val in zip(b, vals):
        axs[0].text(bar.get_x() + bar.get_width() / 2, val + 0.08, f"{val}",
                    ha="center", fontweight="bold", fontsize=10)
    axs[0].set_ylabel("mediana yangi ko'rishlar / kun")
    axs[0].set_ylim(0, 6.5)
    axs[0].set_title("(a)  Xonalar soni bo'yicha tezlik",
                     fontsize=10.5, fontweight="bold", loc="left")
    b = axs[1].bar(["Ikkilamchi", "Yangi qurilish"], [R["nb_sec"], R["nb_new"]],
                   color=[GOLD, TEAL], width=0.5)
    for bar, val in zip(b, [R["nb_sec"], R["nb_new"]]):
        axs[1].text(bar.get_x() + bar.get_width() / 2, val + 0.08, f"{val}",
                    ha="center", fontweight="bold", fontsize=11)
    axs[1].set_ylabel("mediana yangi ko'rishlar / kun")
    axs[1].set_ylim(0, 6.5)
    axs[1].set_title("(b)  Ikkilamchi va yangi qurilish",
                     fontsize=10.5, fontweight="bold", loc="left")
    dv = [R["dow"][d]["vpl"] for d in DOW_KEYS]
    cols = [TEAL if x < max(dv) else "#1d5f6b" for x in dv]
    b = axs[2].bar(DAYS_UZ, dv, color=cols, width=0.62)
    for bar, val in zip(b, dv):
        axs[2].text(bar.get_x() + bar.get_width() / 2, val + 0.15, f"{val}",
                    ha="center", fontsize=9, fontweight="bold")
    axs[2].set_ylabel("o'rtacha yangi ko'rishlar / e'lon-kun")
    axs[2].set_ylim(0, 14.5)
    axs[2].set_title("(c)  Hafta kuni bo'yicha e'tibor",
                     fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_s1_dimensions.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_s1_dimensions.pdf")


def build_funnel_apartments():
    """S2: E'tibor voronkasi — ko'rish -> bosish -> saqlash."""
    tv, tc, tf = R["tot_views"], R["tot_clicks"], R["tot_favs"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    stages = ["Ko'rishlar", "Bosishlar", "Saqlanganlar"]
    vals = [tv, tc, tf]; cols = [TEAL, GOLD, RUST]; y = [2, 1, 0]
    for i in range(3):
        a1.barh(y[i], vals[i], color=cols[i], height=0.6)
        a1.text(vals[i] * 1.5, y[i], f"{vals[i]:,}", va="center", fontsize=11,
                fontweight="bold")
    a1.set_xscale("log"); a1.set_yticks(y); a1.set_yticklabels(stages, fontsize=11)
    a1.set_xlim(10, tv * 5)
    a1.set_xlabel("son (log shkala)")
    a1.set_title("(a)  E'tibor voronkasi", fontsize=11, fontweight="bold", loc="left")
    a1.text(tv * 0.35, 1.5, f"{tc/tv*100:.2f}% \u2192 bosish",
            fontsize=8.5, color=GREY, style="italic", ha="center")
    a1.text(tc * 0.35, 0.5, f"bosishlarning {tf/tc*100:.0f}% \u2192 saqlash",
            fontsize=8.5, color=GREY, style="italic", ha="center")
    per = [100000, tc / tv * 100000, tf / tv * 100000]
    b = a2.bar(stages, per, color=cols, width=0.6)
    a2.set_yscale("log"); a2.set_ylim(10, 200000)
    for bar, vv in zip(b, per):
        a2.text(bar.get_x() + bar.get_width() / 2, vv * 1.3, f"{vv:,.0f}",
                ha="center", fontweight="bold", fontsize=10)
    a2.set_ylabel("100,000 ko'rishga nisbatan (log shkala)")
    a2.set_title("(b)  Chuqurlik qimmat: signal kamayadi",
                 fontsize=11, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_funnel_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_funnel_apartments.pdf")


def build_wedge_apartments():
    """S2: Narx va talab ajralishi (kvintillar)."""
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
    a1.set_ylabel("mediana yangi ko'rishlar / kun"); a1.set_ylim(0, 7)
    a1.set_title("(a)  Xom e'tibor: ikki uchda yuqori",
                 fontsize=11, fontweight="bold", loc="left")
    x = np.arange(5); w = 0.38
    a2.bar(x - w / 2, ca, w, color=TEAL, label="bosish olgan")
    a2.bar(x + w / 2, fa, w, color=GOLD, label="saqlangan")
    for i in range(5):
        a2.text(i - w / 2, ca[i] + 0.4, f"{ca[i]}", ha="center", fontsize=8.2,
                color=TEAL, fontweight="bold")
        a2.text(i + w / 2, fa[i] + 0.4, f"{fa[i]}", ha="center", fontsize=8.2,
                color=GOLD, fontweight="bold")
    a2.set_xticks(x); a2.set_xticklabels(qlab, fontsize=8.3)
    a2.set_ylabel("e'lonlar ulushi, %"); a2.set_ylim(0, 32)
    a2.set_title("(b)  Intent: narx oshgani sari kamayadi",
                 fontsize=11, fontweight="bold", loc="left")
    a2.legend(frameon=False, fontsize=9)
    plt.tight_layout()
    plt.savefig(out("fig_wedge_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_wedge_apartments.pdf")


def build_intent_norm_districts():
    """S2: Tuman bo'yicha normalangan intent + o'rtacha chiziq (makro)."""
    IN = R["intent_norm"]
    order = sorted(IN, key=lambda d: -IN[d]["clicka"])
    ca = [IN[d]["clicka"] for d in order]
    fa = [IN[d]["fava"] for d in order]
    nn = [IN[d]["n"] for d in order]
    avg_c = float(np.mean([IN[d]["clicka"] for d in IN]))
    avg_f = float(np.mean([IN[d]["fava"] for d in IN]))
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    x = np.arange(len(order)); w = 0.4
    ax.bar(x - w / 2, ca, w, color=TEAL, label="bosish olgan e'lonlar, %")
    ax.bar(x + w / 2, fa, w, color=GOLD, label="saqlangan e'lonlar, %")
    for i in range(len(order)):
        ax.text(i - w / 2, ca[i] + 0.5, f"{ca[i]:.0f}", ha="center", fontsize=8.2,
                color=TEAL, fontweight="bold")
        ax.text(i + w / 2, fa[i] + 0.5, f"{fa[i]:.0f}", ha="center", fontsize=8.2,
                color=GOLD, fontweight="bold")
        ax.text(i, -3.2, f"n={nn[i]}", ha="center", fontsize=6.8, color=GREY)
    ax.axhline(avg_c, color=TEAL, lw=1.2, ls="--", alpha=0.7)
    ax.text(len(order) - 0.4, avg_c + 0.4, f"o'rtacha bosish {avg_c:.1f}%",
            fontsize=7.5, color=TEAL, ha="right", fontweight="bold")
    ax.axhline(avg_f, color="#a07d2e", lw=1.2, ls="--", alpha=0.7)
    ax.text(len(order) - 0.4, avg_f + 0.4, f"o'rtacha saqlash {avg_f:.1f}%",
            fontsize=7.5, color="#a07d2e", ha="right", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(order, rotation=32, ha="right", fontsize=8.6)
    ax.set_ylabel("tuman e'lonlari ulushi, %"); ax.set_ylim(0, 32)
    ax.set_title("Tuman bo'yicha intent (normalangan): bosish yoki saqlash olgan e'lonlar ulushi",
                 fontsize=11.5, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    plt.tight_layout()
    plt.savefig(out("fig_intent_norm_districts.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_intent_norm_districts.pdf")


def build_s2_dimensions():
    """S2: Intent xonalar / hafta kuni bo'yicha."""
    rd = R["rooms_dims"]; ks = sorted(rd)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ca = [rd[k]["clicka"] for k in ks]; fa = [rd[k]["fava"] for k in ks]
    x = np.arange(len(ks)); w = 0.38
    a1.bar(x - w / 2, ca, w, color=TEAL, label="bosish olgan, %")
    a1.bar(x + w / 2, fa, w, color=GOLD, label="saqlangan, %")
    for i in range(len(ks)):
        a1.text(i - w / 2, ca[i] + 0.35, f"{ca[i]}", ha="center", fontsize=8.4,
                color=TEAL, fontweight="bold")
        a1.text(i + w / 2, fa[i] + 0.35, f"{fa[i]}", ha="center", fontsize=8.4,
                color=GOLD, fontweight="bold")
    a1.set_xticks(x); a1.set_xticklabels([f"{k}-xona" for k in ks])
    a1.set_ylabel("e'lonlar ulushi, %"); a1.set_ylim(0, 18.5)
    a1.set_title("(a)  Xonalar soni bo'yicha intent",
                 fontsize=10.5, fontweight="bold", loc="left")
    a1.legend(frameon=False, fontsize=8.5)
    ck = [R["dow"][d]["cpk"] for d in DOW_KEYS]
    fk = [R["dow"][d]["fpk"] for d in DOW_KEYS]
    a2.bar(np.arange(7) - w / 2, ck, w, color=TEAL, label="bosish / 1000 e'lon-kun")
    a2.bar(np.arange(7) + w / 2, fk, w, color=GOLD, label="saqlash / 1000 e'lon-kun")
    for i in range(7):
        a2.text(i - w / 2, ck[i] + 0.4, f"{ck[i]:.0f}", ha="center", fontsize=8,
                color=TEAL, fontweight="bold")
        a2.text(i + w / 2, fk[i] + 0.4, f"{fk[i]:.1f}", ha="center", fontsize=7.6,
                color=GOLD, fontweight="bold")
    a2.set_xticks(range(7)); a2.set_xticklabels(DAYS_UZ)
    a2.set_ylabel("intent / 1000 e'lon-kun"); a2.set_ylim(0, 22.5)
    a2.set_title("(b)  Hafta kuni bo'yicha intent",
                 fontsize=10.5, fontweight="bold", loc="left")
    a2.legend(frameon=False, fontsize=8.5)
    plt.tight_layout()
    plt.savefig(out("fig_s2_dimensions.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_s2_dimensions.pdf")


def build_exit_apartments():
    """S3: Chiqish tezlik farqi + yangilash chegarasi dekompozitsiyasi."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    b = a1.bar(["Bozorda qolgan", "Chiqib ketgan"],
               [R["vpd_stay"], R["vpd_exit"]], color=[GOLD, TEAL], width=0.55)
    for bar, vv in zip(b, [R["vpd_stay"], R["vpd_exit"]]):
        a1.text(bar.get_x() + bar.get_width() / 2, vv + 0.25, f"{vv}",
                ha="center", fontweight="bold", fontsize=12)
    a1.set_ylabel("mediana yangi ko'rishlar / kun"); a1.set_ylim(0, 14)
    a1.set_title(f"(a)  Chiqishdan oldin {R['exit_gap']}\u00d7 ko'proq e'tibor",
                 fontsize=11, fontweight="bold", loc="left")
    a1.text(0.5, 12.8,
            f"1-hafta kogortasi; {R['exit_rate']:.0f}% davr oxiriga qadar chiqqan",
            ha="center", fontsize=8, color=GREY)
    labs = ["Erta chiqish\n(<42 kun)", "Yangilash chegarasi\n(42\u201344 kun)",
            "Yangilashdan keyin\n(>44 kun)"]
    shares = [R["exit_early_pct"], R["exit_wall_pct"], R["exit_late_pct"]]
    vpds = [R["vpd_early_exit"], R["vpd_wall_exit"], R["vpd_late_exit"]]
    cols = [GOLD, TEAL, RUST]
    b = a2.bar(labs, shares, color=cols, width=0.6)
    for bar, s, vv in zip(b, shares, vpds):
        a2.text(bar.get_x() + bar.get_width() / 2, s + 1.6, f"{s}%",
                ha="center", fontweight="bold", fontsize=10.5)
        a2.text(bar.get_x() + bar.get_width() / 2, max(s - 8, 3), f"VPD {vv}",
                ha="center", fontsize=8.2, color="white" if s > 12 else INK,
                fontweight="bold")
    a2.set_ylabel("chiqishlar ulushi, %"); a2.set_ylim(0, 92)
    a2.set_title("(b)  Ko'p chiqish 43-kun muddatida yangilanmaslik",
                 fontsize=11, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_exit_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_exit_apartments.pdf")


def build_exit_dims():
    """S3: Chiqish darajasi tuman / xonalar bo'yicha + o'rtacha chiziq."""
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
        a1.text(i, e + 1.2, f"{e:.0f}%", ha="center", fontsize=8.4, fontweight="bold")
    a1.set_xticks(range(len(order)))
    a1.set_xticklabels(order, rotation=32, ha="right", fontsize=8.4)
    a1.set_ylabel("kogortani tark etish ulushi, %"); a1.set_ylim(0, 84)
    a1.axhline(avg_ex, color=AVG, lw=1.3, ls="--")
    a1.text(len(order) - 0.5, avg_ex + 1.5, f"tuman o'rtachasi {avg_ex:.0f}%",
            fontsize=7.8, color=AVG, ha="right", fontweight="bold")
    a1.set_title("(a)  Tuman bo'yicha chiqish darajasi",
                 fontsize=10.5, fontweight="bold", loc="left")
    er = {int(k): v for k, v in R["exit_rooms"].items()}
    ks2 = sorted(er)
    b = a2.bar([f"{k}-xona" for k in ks2], [er[k] for k in ks2], color=GOLD, width=0.62)
    for bar, k in zip(b, ks2):
        a2.text(bar.get_x() + bar.get_width() / 2, er[k] + 1.2, f"{er[k]:.0f}%",
                ha="center", fontweight="bold", fontsize=9.5)
    a2.set_ylabel("chiqish ulushi, %"); a2.set_ylim(0, 84)
    a2.axhline(avg_ex, color=AVG, lw=1.3, ls="--")
    a2.set_title("(b)  Xonalar soni bo'yicha chiqish",
                 fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_exit_dims.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_exit_dims.pdf")


def build_tom_dims():
    """S4: Zaxira yoshi tuman va xonalar bo'yicha (43-kun spike olib tashlandi)."""
    dd = R["districts"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3),
                                 gridspec_kw={"width_ratios": [1.7, 1]})
    order = sorted(dd, key=lambda d: dd[d]["age"])
    ages = [dd[d]["age"] for d in order]
    avg_age = float(np.mean([dd[d]["age"] for d in dd]))
    cmap = LinearSegmentedColormap.from_list("p", ["#ece9f2", PURP])
    nrm = [(a - min(ages)) / (max(ages) - min(ages)) for a in ages]
    a1.barh(range(len(order)), ages, color=[cmap(0.2 + 0.8 * (1 - v)) for v in nrm],
            height=0.68)
    for i, a in enumerate(ages):
        a1.text(a + 0.6, i, f"{a:.0f}", va="center", fontsize=8, fontweight="bold")
    a1.set_yticks(range(len(order))); a1.set_yticklabels(order, fontsize=8.4)
    a1.invert_yaxis()
    a1.set_xlabel("faol zaxira mediana yoshi (kun)"); a1.set_xlim(0, 47)
    a1.axvline(avg_age, color=AVG, lw=1.3, ls="--")
    a1.text(avg_age + 0.5, len(order) - 0.5, f"o'rtacha {avg_age:.0f}",
            fontsize=7.8, color=AVG, va="center", fontweight="bold")
    a1.set_title("(a)  Tuman bo'yicha zaxira yoshi",
                 fontsize=10.5, fontweight="bold", loc="left")
    ar = {int(k): v for k, v in R["age_rooms"].items()}
    ks3 = sorted(ar)
    b = a2.bar([f"{k}-xona" for k in ks3], [ar[k] for k in ks3], color=PURP, width=0.62)
    for bar, k in zip(b, ks3):
        a2.text(bar.get_x() + bar.get_width() / 2, ar[k] + 1, f"{ar[k]}",
                ha="center", fontweight="bold", fontsize=9.5)
    a2.set_ylabel("mediana faol kunlar"); a2.set_ylim(0, 58)
    a2.axhline(avg_age, color=AVG, lw=1.3, ls="--")
    a2.set_title("(b)  Xonalar soni bo'yicha zaxira yoshi",
                 fontsize=10.5, fontweight="bold", loc="left")
    plt.tight_layout()
    plt.savefig(out("fig_tom_dims.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_tom_dims.pdf")


def build_metrics_panel_apartments():
    """To'rt asosiy signal heatmap + tuman o'rtachasi qatori."""
    d = R["districts"]; intent = R["intent_norm"]
    rows = []
    for dist in d:
        rows.append(dict(district=dist, vpd=d[dist]["vpd"],
                         click=intent[dist]["clicka"],
                         exit=d[dist]["absorp"], age=d[dist]["age"]))
    D = pd.DataFrame(rows).set_index("district").sort_values("vpd", ascending=False)
    avg_row = dict(vpd=round(D.vpd.mean(), 1), click=round(D.click.mean(), 1),
                   exit=round(D["exit"].mean(), 0), age=round(D.age.mean(), 0))
    cols = [("vpd", "Talab tezligi", "yangi ko'rishlar / kun", False, "{:.1f}"),
            ("click", "Bosish & saqlash", "bosish olgan e'lon %", False, "{:.0f}%"),
            ("exit", "Chiqish darajasi", "kogorta chiqishi %", False, "{:.0f}%"),
            ("age", "Bozorda turish", "mediana faol kun", True, "{:.0f}")]
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
    fig, ax = plt.subplots(figsize=(9.6, 7.6)); ax.axis("off")
    ax.set_xlim(0, 4); ax.set_ylim(-1.4, nrows + 1.4)
    ax.text(2, nrows + 1.15, "To'rt talab signali tumanlar bo'yicha \u2014 faqat kvartiralar",
            ha="center", fontsize=13, fontweight="bold", color=INK)
    ax.text(2, nrows + 0.72,
            "Talab tezligi bo'yicha saralangan. Har ustun alohida; to'q = kuchliroq talab (Bozorda turish teskari).",
            ha="center", fontsize=7.6, color=GREY, style="italic")
    for j, (key, title, sub, inv, fmt) in enumerate(cols):
        n = shade(D[key], inv)
        ax.text(j + 0.5, nrows + 0.18, title, ha="center", fontweight="bold",
                fontsize=9.5, color=colcolor[key])
        ax.text(j + 0.5, nrows - 0.14, sub, ha="center", fontsize=7.1, color=GREY)
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
    ax.text(-0.06, 0, "TUMAN O'RTACHASI", ha="right", va="center",
            fontsize=8.5, color=INK, fontweight="bold")
    ax.text(2, -1.15, SRC + " Bektemir n=11.", ha="center", fontsize=7, color=GREY)
    plt.tight_layout()
    plt.savefig(out("fig_metrics_panel_apartments.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_metrics_panel_apartments.pdf")


def build_demand_map():
    """Talab xaritasi: original layout (o'ng panel bilan), o'lcham = qamrov (reach), bir xil rang."""
    global R, L, P
    import matplotlib.gridspec as gridspec
    d = R["districts"]; cc = R["centroids"]
    asp = np.cos(np.radians(41.3))
    BG = "#faf7f1"; PANEL = "#faf7f1"
    BUBBLE = "#c17b38"   # bir xil rang (barcha aylanalar uchun)

    # reach bo'yicha o'lcham; overlaplarni oldini olish uchun engil ajratish
    names = list(cc)
    pos = np.array([[cc[k]["lon"], cc[k]["lat"]] for k in names], float)
    orig = pos.copy()
    reach = np.array([d[k]["reach"] for k in names], float)
    maxr = reach.max()
    rad = {names[i]: 0.004 + 0.017 * (reach[i] / maxr) ** 0.5 for i in range(len(names))}
    radarr = np.array([rad[k] for k in names])
    for _ in range(400):
        moved = 0
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                dx = (pos[j, 0] - pos[i, 0]) * asp; dy = pos[j, 1] - pos[i, 1]
                dist = np.hypot(dx, dy); mind = (radarr[i] + radarr[j]) * 1.08
                if 1e-9 < dist < mind:
                    push = (mind - dist) / 2; ux, uy = dx / dist, dy / dist
                    pos[i, 0] -= ux * push / asp; pos[i, 1] -= uy * push
                    pos[j, 0] += ux * push / asp; pos[j, 1] += uy * push
                    moved += 1
        pos += (orig - pos) * 0.04
        if moved == 0:
            break
    posd = {names[i]: tuple(pos[i]) for i in range(len(names))}

    fig = plt.figure(figsize=(13.5, 8.4))
    gs = gridspec.GridSpec(1, 2, width_ratios=[2.4, 1], wspace=0.03)
    axm = fig.add_subplot(gs[0]); axr = fig.add_subplot(gs[1])

    # ---- MAP ----
    axm.set_facecolor(BG)
    for s in axm.spines.values():
        s.set_color("#eae4d8"); s.set_linewidth(1)
    axm.set_xticks([]); axm.set_yticks([])
    xs = [posd[k][0] for k in cc]; ys = [posd[k][1] for k in cc]
    padx = (max(xs) - min(xs)) * 0.14; pady = (max(ys) - min(ys)) * 0.16
    axm.set_xlim(min(xs) - padx, max(xs) + padx)
    axm.set_ylim(min(ys) - pady, max(ys) + pady * 1.3)
    axm.set_aspect(1 / asp)

    pcloud = P.drop_duplicates("listing_id")[["longitude", "latitude"]].dropna()
    pcloud = pcloud[(pcloud.latitude.between(*axm.get_ylim())) &
                    (pcloud.longitude.between(*axm.get_xlim()))]
    axm.scatter(pcloud.longitude, pcloud.latitude, s=2.5, color="#cbb68f",
                alpha=0.30, zorder=1, linewidths=0)

    # bubbles: bir xil rang, o'lcham = reach, katta->kichik chizish
    for k in sorted(cc, key=lambda x: -d[x]["reach"]):
        rr = rad[k]
        e = Ellipse(posd[k], width=rr * 2 / asp, height=rr * 2, facecolor=BUBBLE,
                    edgecolor="white", lw=2, zorder=3, alpha=0.97)
        axm.add_patch(e)
    for k in cc:
        rr = rad[k]
        below = {"Shaykhantakhur", "Mirabad", "Yakkasaray"}
        if k in below:
            axm.text(posd[k][0], posd[k][1] - rr - 0.006, k, ha="center", va="top",
                     fontsize=9.3, fontweight="bold", color=INK, zorder=5)
        else:
            axm.text(posd[k][0], posd[k][1] + rr + 0.006, k, ha="center", va="bottom",
                     fontsize=9.3, fontweight="bold", color=INK, zorder=5)

    axm.set_title("Qamrov (reach)", fontsize=12, fontweight="bold", loc="right",
                  color="#7a6a58", pad=8)

    # ---- RANKED PANEL (o'ng tomonda, saqlanadi) — reach bo'yicha ----
    axr.set_facecolor(PANEL)
    for s in axr.spines.values():
        s.set_color("#eae4d8"); s.set_linewidth(1)
    axr.set_xticks([]); axr.set_yticks([]); axr.set_xlim(0, 1); axr.set_ylim(0, 1)
    axr.text(0.08, 0.955, "Tumanlar qamrov bo'yicha", fontsize=11.5,
             fontweight="bold", color=INK)
    axr.text(0.08, 0.925, "jami yangi ko'rishlar (reach)", fontsize=8.5, color=GREY)
    order = sorted(cc, key=lambda x: -d[x]["reach"])
    rmax = max(d[k]["reach"] for k in cc)
    y0 = 0.86; dy = 0.067
    for i, k in enumerate(order):
        y = y0 - i * dy; rv = d[k]["reach"]
        axr.add_patch(plt.Rectangle((0.08, y - 0.011), 0.022, 0.022, fc=BUBBLE, ec="none"))
        axr.text(0.125, y, k, fontsize=9.3, color=INK, va="center")
        bw = 0.30 * rv / rmax
        axr.add_patch(plt.Rectangle((0.56, y - 0.006), 0.34, 0.012, fc="#e7ded0", ec="none"))
        axr.add_patch(plt.Rectangle((0.56, y - 0.006), max(bw, 0.004), 0.012, fc=BUBBLE, ec="none"))
        axr.text(0.985, y, f"{rv:,}", fontsize=8.3, color=INK, va="center", ha="right",
                 fontweight="bold")

    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.03,
             "Har tuman o'z e'lonlarining mediana koordinatalarida; aylana o'lchami = qamrov (reach). "
             "So'nik nuqtalar: alohida kvartiralar. " + SRC,
             ha="center", fontsize=7.2, color=GREY)
    plt.savefig(out("fig_demand_map.pdf"), bbox_inches="tight", facecolor="white")
    plt.close()
    print("  fig_demand_map.pdf")



def build_supply_demand_bands():
    """Talab va taklif narx oralig'i bo'yicha."""
    bl = ["<30k", "30-50k", "50-75k", "75-100k", "100-150k", "150-250k", "250k+"]
    sup = [R["bands"][b]["supply"] for b in bl]
    dem = [R["bands"][b]["medvpd"] for b in bl]
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.bar(range(7), sup, color="#e7e2da", edgecolor="#c9c2b6", width=0.72, zorder=2)
    for i, s in enumerate(sup):
        ax1.text(i, s + 14, f"{s}", ha="center", fontsize=8.5, color=GREY)
    ax1.set_ylabel("E'lonlar soni (taklif)", fontsize=10); ax1.set_ylim(0, 860)
    ax1.set_xticks(range(7)); ax1.set_xticklabels(bl, fontsize=9)
    ax1.set_xlabel("Narx oralig'i (USD)")
    ax2 = ax1.twinx(); ax2.spines["top"].set_visible(False)
    ax2.plot(range(7), dem, color=RUST, marker="o", lw=2.4, ms=7, zorder=3)
    for i, dv in enumerate(dem):
        ax2.text(i + 0.08, dv + 0.25, f"{dv}", fontsize=9, color=RUST, fontweight="bold")
    ax2.set_ylabel("Mediana yangi ko'rishlar / kun (talab)", color=RUST, fontsize=10)
    ax2.tick_params(axis="y", colors=RUST); ax2.set_ylim(0, 11.5)
    ax1.set_title("Taklif $50\u2013150k oralig'ida to'plangan; talab $30k dan pastda cho'qqida",
                  fontsize=12, fontweight="bold", loc="left", pad=12)
    fig.text(0.5, -0.02, SRC, ha="center", fontsize=7.3, color=GREY)
    plt.tight_layout()
    plt.savefig(out("fig_supply_demand_bands.pdf"), bbox_inches="tight")
    plt.close()
    print("  fig_supply_demand_bands.pdf")


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
]


def main():
    _load()
    print("[figures] Uzbek figuralar:", len(ALL_FIGURES), "->", config.FIG_DIR)
    for fn in ALL_FIGURES:
        fn()
    print("[figures] tayyor")


if __name__ == "__main__":
    main()
