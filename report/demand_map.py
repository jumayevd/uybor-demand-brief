# -*- coding: utf-8 -*-
"""
demand_map.py — district choropleth of demand, shared by the Uzbek (figures.py)
and English (figures_en.py) daily figure sets. Only the visible text differs.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, Normalize, PowerNorm
from matplotlib.cm import ScalarMappable

TEAL, RUST, INK, GREY = "#2E7D8A", "#B24C3C", "#2b2b2b", "#9AA0A6"


def _knn(pts, q, k, chunk=2000):
    """k nearest points by brute force (numpy, chunked): distances and indices."""
    D = np.empty((len(q), k)); I = np.empty((len(q), k), dtype=int)
    p2 = (pts ** 2).sum(1)
    for s in range(0, len(q), chunk):
        qq = q[s:s + chunk]
        d2 = (qq ** 2).sum(1)[:, None] + p2[None, :] - 2 * qq @ pts.T
        part = np.argpartition(d2, k, axis=1)[:, :k]
        dd = np.take_along_axis(d2, part, axis=1)
        o = np.argsort(dd, axis=1)
        I[s:s + chunk] = np.take_along_axis(part, o, axis=1)
        D[s:s + chunk] = np.sqrt(np.maximum(np.take_along_axis(dd, o, axis=1), 0))
    return D, I


def _box(a, r):
    """Sum over a (2r+1)x(2r+1) window (zero-padded), via cumulative sums."""
    n = 2 * r + 1
    a = np.pad(a.astype(float), r)
    c = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
    c[1:, 1:] = a.cumsum(0).cumsum(1)
    return c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]


def draw(L, P, out_path, text):
    """Fig 4 — district choropleth of demand: (a) reach, (b) intensity.

    Official boundaries aren't available, so each district's territory is derived
    from the data: every point of the city takes the district most common among
    its 15 nearest listings (smoothed), i.e. the territory as Uybor labels it. The
    city footprint is the area within ~1.5 km of a listing, holes filled. Regions
    are drawn as smooth vector contours.
    (a) share of all new views, square-root colour scale (Yunusobod dominates).
    (b) new views per active listing-day; the scale stops at the largest
        non-outlier (Tukey fence) and outliers share the darkest shade.
    text keys: cbar_a, cbar_b (required); title_a, title_b, footnote (optional).
    """
    df = L.join(P.groupby("listing_id")[["latitude", "longitude"]].median())
    df = df[df.latitude.between(41.15, 41.45) & df.longitude.between(69.10, 69.45)]
    asp = np.cos(np.radians(df.latitude.median()))
    g = df.groupby("district").agg(nv=("nv", "sum"), days=("days_obs", "sum"), n=("nv", "size"))
    g["reach"] = g.nv / g.nv.sum() * 100
    g["intensity"] = g.nv / g.days.clip(lower=1)
    names = list(g.index); idx = {d: i for i, d in enumerate(names)}

    pad = 0.024   # > footprint radius, so the city outline is never clipped
    x0, x1 = df.longitude.min() - pad, df.longitude.max() + pad
    y0, y1 = df.latitude.min() - pad, df.latitude.max() + pad
    NX = 320; NY = int(NX * (y1 - y0) / ((x1 - x0) * asp))
    gx, gy = np.meshgrid(np.linspace(x0, x1, NX), np.linspace(y0, y1, NY))
    q = np.c_[gx.ravel() * asp, gy.ravel()]
    dist, nn = _knn(np.c_[df.longitude.values * asp, df.latitude.values], q, 15)
    lab = df.district.map(idx).values
    votes = np.zeros((len(q), len(names)))
    for k in range(nn.shape[1]):
        votes[np.arange(len(q)), lab[nn[:, k]]] += 1
    votes = votes.reshape(NY, NX, len(names))
    score = np.stack([_box(votes[:, :, c], 3) for c in range(len(names))], axis=2)
    score /= score.sum(axis=2, keepdims=True) + 1e-9            # local vote share
    near = dist[:, 0].reshape(NY, NX) < 0.014
    near = _box(_box(near, 2) > 0, 2) >= 25 - 1e-9                # closing: seal thin gaps
    outside = np.zeros_like(near)
    outside[0, :] = outside[-1, :] = outside[:, 0] = outside[:, -1] = True
    outside &= ~near
    for _ in range(NX + NY):                                      # flood-fill holes
        grown = (_box(outside, 1) > 0) & ~near
        if (grown == outside).all():
            break
        outside = grown
    foot = _box(~outside, 5) / 11 ** 2                            # smooth footprint 0..1
    margin = [np.minimum(score[:, :, c] - np.delete(score, c, axis=2).max(axis=2), foot - 0.5)
              for c in range(len(names))]

    def robust(vals):
        q1, q3 = np.percentile(vals, [25, 75])
        vmax = vals[vals <= q3 + 1.5 * (q3 - q1)].max()
        return Normalize(vmin=vals.min(), vmax=vmax), vmax < vals.max()

    reach_cmap = LinearSegmentedColormap.from_list("reach", ["#f7ecdc", "#e0a35f", RUST, "#6b2418"])
    int_cmap = LinearSegmentedColormap.from_list("int", ["#e8f1f2", "#86b6bd", TEAL, "#164a53"])
    panels = [
        ("reach", reach_cmap, text.get("title_a"), "{:.1f}%",
         text["cbar_a"],
         (PowerNorm(0.5, vmin=g.reach.min(), vmax=g.reach.max()), False)),
        ("intensity", int_cmap, text.get("title_b"), "{:.1f}",
         text["cbar_b"], robust(g.intensity.values)),
    ]
    fig, axs = plt.subplots(1, 2, figsize=(14, 7.4))
    for ax, (metric, cmap, title, fmt, cblabel, (norm, clipped)) in zip(axs, panels):
        for c, d in enumerate(names):
            col = cmap(norm(min(g.loc[d, metric], norm.vmax)))
            ax.contourf(gx, gy, margin[c], levels=[0, 10], colors=[col], zorder=1)
            ax.contour(gx, gy, margin[c], levels=[0], colors="white", linewidths=1.6, zorder=2)
        ax.contour(gx, gy, foot, levels=[0.5], colors="#7a7a7a", linewidths=1.3, zorder=3)
        for c, d in enumerate(names):
            m = margin[c] > 0
            if not m.any():
                continue
            v = g.loc[d, metric]
            dark = norm(min(v, norm.vmax)) > 0.6
            ax.text(np.median(gx[m]), np.median(gy[m]),
                    f"{d}\n{fmt.format(v)}{'*' if g.loc[d, 'n'] < 40 else ''}",
                    ha="center", va="center", fontsize=8.6, fontweight="bold", zorder=5,
                    color="white" if dark else INK,
                    path_effects=[pe.withStroke(linewidth=2.2,
                                  foreground=(0, 0, 0, 0.35) if dark else "white")])
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / asp)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
        if title:
            ax.set_title(title, fontsize=11.5, fontweight="bold", loc="left")
        cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                          orientation="horizontal", fraction=0.045, pad=0.02, aspect=35,
                          extend="max" if clipped else "neither")
        cb.set_label(cblabel, fontsize=9); cb.ax.tick_params(labelsize=8)
        cb.outline.set_visible(False)
        if metric == "reach":
            ticks = [t for t in (1, 2, 5, 10, 20, 30) if norm.vmin <= t <= norm.vmax]
            cb.set_ticks(ticks); cb.set_ticklabels([str(t) for t in ticks])
    if text.get("footnote"):
        fig.text(0.5, 0.015, text["footnote"], ha="center", fontsize=8, color=GREY)
    plt.tight_layout(rect=(0, 0.03, 1, 1))
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close()
