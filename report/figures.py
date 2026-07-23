"""
figures.py — generate all 11 paper figures from build/metrics.json + build/{L,P}.pkl
=====================================================================================

Run:  python figures.py     (or let build.py call it)
Reads:   build/metrics.json, build/L.pkl, build/P.pkl
Writes:  figures/fig_*.pdf   (all 11 figures used in the paper)

Each function builds exactly one figure and is documented with:
  WHAT   — what the figure shows
  DATA   — the metrics.json keys / panel columns it uses
Colours are fixed so daily re-runs are visually identical: gold=median/typical,
teal=mean/breadth, rust=trough/soft, purple=index/duration.
"""
import pandas as pd, numpy as np, json, os
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, Ellipse
import matplotlib.gridspec as gridspec
import config

mpl.rcParams["font.family"] = "DejaVu Sans"
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["axes.spines.top"] = False
mpl.rcParams["axes.spines.right"] = False

GOLD, TEAL, RUST, PURP = "#C8A15A", "#2E7D8A", "#B24C3C", "#6B5B95"
GREY, INK = "#9AA0A6", "#2b2b2b"

os.makedirs(config.FIG_DIR, exist_ok=True)
R = L = P = SRC = None  # populated by _load() at run time

def _load():
    global R, L, P, SRC
    R = json.load(open(os.path.join(config.BUILD_DIR, "metrics.json")))
    L = pd.read_pickle(os.path.join(config.BUILD_DIR, "L.pkl"))
    P = pd.read_pickle(os.path.join(config.BUILD_DIR, "P.pkl"))
    SRC = ("Source: authors\u2019 calculations, Uybor.uz daily panel, apartments, "
           f"{R['window']['date_min']} \u2013 {R['window']['date_max']}.")
def out(name): return os.path.join(config.FIG_DIR, name)

def build_evidence_map():
    """S0 Evidence map: 4 signals + validating studies"""
    global R, L, P
    apt = P
    import pandas as pd, numpy as np, json, matplotlib.pyplot as plt, matplotlib as mpl
    from matplotlib.patches import FancyBboxPatch
    from matplotlib.colors import LinearSegmentedColormap
    mpl.rcParams['font.family']='DejaVu Sans'; mpl.rcParams['pdf.fonttype']=42
    mpl.rcParams['axes.spines.top']=False; mpl.rcParams['axes.spines.right']=False
    GOLD='#C8A15A'; TEAL='#2E7D8A'; RUST='#B24C3C'; PURP='#6B5B95'; GREY='#9AA0A6'; INK='#2b2b2b'

    SRC='Source: authors\u2019 calculations, Uybor.uz daily panel, apartments, 24 June \u2013 21 July 2026.'

    # ---------- 1. EVIDENCE MAP (4 signals) ----------
    fig,ax=plt.subplots(figsize=(9.4,6.4)); ax.set_xlim(0,10); ax.set_ylim(0,10); ax.axis('off')
    ax.text(5,9.6,'Four listing signals validated as housing-demand proxies',ha='center',fontsize=13.5,fontweight='bold',color=INK)
    ax.text(5,9.15,'What each signal measures, the outcome it was validated against, and the studies that showed it',ha='center',fontsize=9,color=GREY,style='italic')
    rows=[('Views &\nvelocity',TEAL,'Breadth and current intensity\nof buyer attention','Views-per-property = industry demand score;\nclick flows Granger-cause prices & liquidity','Realtor.com (2025); van Dijk & Francke (2018)'),
          ('Clicks &\nfavorites',GOLD,'Costly, deliberate actions;\ngraded depth of intent','Low interest predicts longer TOM & price cuts;\ntop-favorited homes sell faster, above list','Pangallo & Loberto (2018); Zillow Research (2018)'),
          ('Exit rate',RUST,'Share of stock leaving the\nmarket over a period','Delisting is the standard listing-data outcome;\nexit conflates sale, withdrawal, expiration','Pangallo & Loberto (2018); de Wit & van der Klaauw (2013)'),
          ('Time on\nmarket',PURP,'How long stock lingers\nbefore the market absorbs it','TOM falls when demand rises; constant-quality\nTOM indices measure market liquidity','Genesove & Han (2012); Carrillo & Williams (2019)')]
    y0=8.15; h=1.85
    ax.text(2.55,8.42,'WHAT IT MEASURES',fontsize=8,fontweight='bold',color=GREY)
    ax.text(5.35,8.42,'VALIDATED AGAINST (market outcome)',fontsize=8,fontweight='bold',color=GREY)
    for i,(name,col,what,valid,cite) in enumerate(rows):
        y=y0-i*h
        ax.add_patch(FancyBboxPatch((0.3,y-h+0.34),1.9,h-0.5,boxstyle='round,pad=0.02,rounding_size=0.08',fc=col,ec='none',alpha=0.93))
        ax.text(1.25,y-h/2+0.09,name,ha='center',va='center',color='white',fontsize=10,fontweight='bold')
        ax.text(2.55,y-h/2+0.09,what,ha='left',va='center',fontsize=8.7,color=INK)
        ax.text(5.35,y-h/2+0.09,valid,ha='left',va='center',fontsize=8.5,color=INK)
        ax.text(5.35,y-h+0.44,cite,ha='left',va='center',fontsize=7.7,color=GREY,style='italic')
    ax.annotate('',xy=(0.12,y0-4*h+0.36),xytext=(0.12,y0),arrowprops=dict(arrowstyle='-|>',color=GREY,lw=1.4))
    ax.text(0.02,y0-2*h,'attention \u2192 intent \u2192 outcome',rotation=90,va='center',ha='center',fontsize=8,color=GREY,style='italic')
    ax.text(5,0.32,'Signals run from attention through intent to realized market outcomes; each has independent empirical validation as a demand indicator.',ha='center',fontsize=7.6,color=GREY)
    plt.tight_layout(); plt.savefig(out('fig_evidence_map.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_evidence_map.pdf')


def build_concentration_apartments():
    """S1 Velocity concentration (Lorenz-style)"""
    global R, L, P
    apt = P


    # ---------- 3. CONCENTRATION ----------
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.3))
    v=L.vpd.values; med=np.median(v); mean=np.mean(v)
    bins=np.logspace(np.log10(max(v.min(),0.1)),np.log10(v.max()+1),45)
    a1.hist(v,bins=bins,color=TEAL,alpha=0.55,edgecolor='white',lw=0.4); a1.set_xscale('log')
    a1.axvline(med,color=GOLD,lw=2.2); a1.axvline(mean,color=TEAL,lw=2.2)
    a1.text(med*0.9,a1.get_ylim()[1]*0.92,f'median {med:.1f}\nthe typical listing',color=GOLD,fontsize=8.5,fontweight='bold',ha='right')
    a1.text(mean*1.1,a1.get_ylim()[1]*0.74,f'mean {mean:.1f}\ndragged up by the tail',color=TEAL,fontsize=8.5,fontweight='bold')
    a1.set_xlabel('new views per day per listing (log scale)'); a1.set_ylabel('number of listings')
    a1.set_title('(a)  Most listings trickle; a few flood',fontsize=11,fontweight='bold',loc='left')
    vals=[R['top10'],R['top25'],R['bot50']]
    b=a2.bar(['Top 10%','Top 25%','Bottom 50%'],vals,color=[TEAL,'#7FB0B8',GOLD],width=0.6)
    for bar,val in zip(b,vals): a2.text(bar.get_x()+bar.get_width()/2,val+1.5,f'{val}%',ha='center',fontweight='bold',fontsize=11)
    a2.set_ylabel('share of all new views captured'); a2.set_ylim(0,90); a2.set_xlabel('listings ranked by attention')
    a2.set_title('(b)  Where the attention goes',fontsize=11,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_concentration_apartments.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_concentration_apartments.pdf')


def build_s1_dimensions():
    """S1 Velocity by rooms / build type / day-of-week"""
    global R, L, P
    apt = P
    import pandas as pd, numpy as np, json, matplotlib.pyplot as plt, matplotlib as mpl
    from matplotlib.colors import LinearSegmentedColormap
    mpl.rcParams['font.family']='DejaVu Sans'; mpl.rcParams['pdf.fonttype']=42
    mpl.rcParams['axes.spines.top']=False; mpl.rcParams['axes.spines.right']=False
    GOLD='#C8A15A'; TEAL='#2E7D8A'; RUST='#B24C3C'; PURP='#6B5B95'; GREY='#9AA0A6'; INK='#2b2b2b'

    days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    # ============ S1 DIMENSIONS: rooms | build type | day of week ============
    fig,axs=plt.subplots(1,3,figsize=(13,4))
    rd=R['rooms_dims']; ks=sorted(rd)
    vals=[rd[k]['vpd'] for k in ks]
    b=axs[0].bar([f'{k}-rm' for k in ks],vals,color=TEAL,width=0.62)
    for bar,v in zip(b,vals): axs[0].text(bar.get_x()+bar.get_width()/2,v+0.08,f'{v}',ha='center',fontweight='bold',fontsize=10)
    axs[0].set_ylabel('median new views / day'); axs[0].set_ylim(0,6.5)
    axs[0].set_title('(a)  Velocity by room count',fontsize=10.5,fontweight='bold',loc='left')
    b=axs[1].bar(['Secondary','New build'],[R['nb_sec'],R['nb_new']],color=[GOLD,TEAL],width=0.5)
    for bar,v in zip(b,[R['nb_sec'],R['nb_new']]): axs[1].text(bar.get_x()+bar.get_width()/2,v+0.08,f'{v}',ha='center',fontweight='bold',fontsize=11)
    axs[1].set_ylabel('median new views / day'); axs[1].set_ylim(0,6.5)
    axs[1].set_title('(b)  Secondary vs new build',fontsize=10.5,fontweight='bold',loc='left')
    dv=[R['dow'][d]['vpl'] for d in days]
    cols=[TEAL if v<max(dv) else '#1d5f6b' for v in dv]
    b=axs[2].bar(days,dv,color=cols,width=0.62)
    for bar,v in zip(b,dv): axs[2].text(bar.get_x()+bar.get_width()/2,v+0.15,f'{v}',ha='center',fontsize=9,fontweight='bold')
    axs[2].set_ylabel('mean new views per listing-day'); axs[2].set_ylim(0,14.5)
    axs[2].set_title('(c)  Attention by day of week',fontsize=10.5,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_s1_dimensions.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_s1_dimensions.pdf')


def build_funnel_apartments():
    """S2 Attention funnel views->clicks->favorites"""
    global R, L, P
    apt = P


    # ---------- 4. FUNNEL ----------
    tv,tc,tf=R['tot_views'],R['tot_clicks'],R['tot_favs']
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.4))
    stages=['Views','Clicks','Favorites']; vals=[tv,tc,tf]; cols=[TEAL,GOLD,RUST]; y=[2,1,0]
    for i,(s,vv,c) in enumerate(zip(stages,vals,cols)):
        a1.barh(y[i],vv,color=c,height=0.6); a1.text(vv*1.4,y[i],f'{vv:,}',va='center',fontsize=10,fontweight='bold')
    a1.set_xscale('log'); a1.set_yticks(y); a1.set_yticklabels(stages,fontsize=11); a1.set_xlim(10,tv*4)
    a1.set_xlabel('count (log scale)'); a1.set_title('(a)  The attention funnel',fontsize=11,fontweight='bold',loc='left')
    a1.text(tv*0.45,1.5,f'{tc/tv*100:.2f}% convert',fontsize=8.5,color=GREY,style='italic',ha='center')
    a1.text(tc*0.45,0.5,f'{tf/tc*100:.0f}% of clicks',fontsize=8.5,color=GREY,style='italic',ha='center')
    per=[100000,tc/tv*100000,tf/tv*100000]
    b=a2.bar(stages,per,color=cols,width=0.6); a2.set_yscale('log'); a2.set_ylim(10,200000)
    for bar,vv in zip(b,per): a2.text(bar.get_x()+bar.get_width()/2,vv*1.3,f'{vv:,.0f}',ha='center',fontweight='bold',fontsize=10)
    a2.set_ylabel('per 100,000 views (log scale)'); a2.set_title('(b)  Depth is costly: attrition by signal',fontsize=11,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_funnel_apartments.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_funnel_apartments.pdf')


def build_wedge_apartments():
    """S2 Price wedge: velocity vs intent by quintile"""
    global R, L, P
    apt = P


    # ---------- 6. WEDGE ----------
    Q=R['quintiles']; ql=['Q1','Q2','Q3','Q4','Q5']
    qlab=[f"Q1\n\u2264${Q['Q1']['pmax']//1000}k",f"Q2\n\${Q['Q2']['pmin']//1000}-{Q['Q2']['pmax']//1000}k",
          f"Q3\n\${Q['Q3']['pmin']//1000}-{Q['Q3']['pmax']//1000}k",f"Q4\n\${Q['Q4']['pmin']//1000}-{Q['Q4']['pmax']//1000}k",
          f"Q5\n\u2265${Q['Q5']['pmin']//1000}k"]
    vpd_q=[Q[q]['vpd'] for q in ql]; ca=[Q[q]['clicka'] for q in ql]; fa=[Q[q]['fava'] for q in ql]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.4))
    cols=[TEAL]*5; cols[3]=RUST
    b=a1.bar(range(5),vpd_q,color=cols,width=0.68)
    for i,v in enumerate(vpd_q): a1.text(i,v+0.12,f'{v}',ha='center',fontweight='bold',fontsize=10)
    a1.set_xticks(range(5)); a1.set_xticklabels(qlab,fontsize=8.3); a1.set_ylabel('median new views / day'); a1.set_ylim(0,7)
    a1.set_title('(a)  Raw attention: high at both ends',fontsize=11,fontweight='bold',loc='left')
    a1.annotate('the upper-middle trough',xy=(3,vpd_q[3]+0.15),xytext=(3,6.35),ha='center',fontsize=8.5,color=RUST,arrowprops=dict(arrowstyle='-',color=RUST,lw=1))
    x=np.arange(5); w=0.38
    a2.bar(x-w/2,ca,w,color=TEAL,label='earned a click')
    a2.bar(x+w/2,fa,w,color=GOLD,label='earned a favorite')
    for i in range(5):
        a2.text(i-w/2,ca[i]+0.4,f'{ca[i]}',ha='center',fontsize=8.2,color=TEAL,fontweight='bold')
        a2.text(i+w/2,fa[i]+0.4,f'{fa[i]}',ha='center',fontsize=8.2,color=GOLD,fontweight='bold')
    a2.set_xticks(x); a2.set_xticklabels(qlab,fontsize=8.3); a2.set_ylabel('% of listings'); a2.set_ylim(0,32)
    a2.set_title('(b)  Intent: falls monotonically with price',fontsize=11,fontweight='bold',loc='left')
    a2.legend(frameon=False,fontsize=9)
    plt.tight_layout(); plt.savefig(out('fig_wedge_apartments.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_wedge_apartments.pdf')


def build_intent_norm_districts():
    """S2 Normalized intent by district"""
    global R, L, P
    apt = P


    # ============ S2: NORMALIZED intent by district ============
    IN=R['intent_norm']; order=sorted(IN,key=lambda d:-IN[d]['clicka'])
    ca=[IN[d]['clicka'] for d in order]; fa=[IN[d]['fava'] for d in order]; nn=[IN[d]['n'] for d in order]
    fig,ax=plt.subplots(figsize=(10,4.8))
    x=np.arange(len(order)); w=0.4
    ax.bar(x-w/2,ca,w,color=TEAL,label='% of listings earning a click')
    ax.bar(x+w/2,fa,w,color=GOLD,label='% of listings earning a favorite')
    for i in range(len(order)):
        ax.text(i-w/2,ca[i]+0.5,f'{ca[i]:.0f}',ha='center',fontsize=8.3,color=TEAL,fontweight='bold')
        ax.text(i+w/2,fa[i]+0.5,f'{fa[i]:.0f}',ha='center',fontsize=8.3,color=GOLD,fontweight='bold')
        ax.text(i,-3.4,f'n={nn[i]}',ha='center',fontsize=6.8,color=GREY)
    ax.set_xticks(x); ax.set_xticklabels(order,rotation=32,ha='right',fontsize=8.6)
    ax.set_ylabel('% of district listings'); ax.set_ylim(0,32)
    ax.set_title('Intent incidence by district (normalized): share of listings earning any click or favorite',fontsize=11.5,fontweight='bold',loc='left')
    ax.legend(frameon=False,fontsize=9)
    plt.tight_layout(); plt.savefig(out('fig_intent_norm_districts.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_intent_norm_districts.pdf')


def build_s2_dimensions():
    """S2 Intent by rooms / day-of-week"""
    global R, L, P
    apt = P
    rd=R['rooms_dims']; ks=sorted(rd)
    days=['Mon','Tue','Wed','Thu','Fri','Sat','Sun']


    # ============ S2 DIMENSIONS: rooms | day of week ============
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.2))
    ca=[rd[k]['clicka'] for k in ks]; fa=[rd[k]['fava'] for k in ks]
    x=np.arange(len(ks)); w=0.38
    a1.bar(x-w/2,ca,w,color=TEAL,label='% earned a click')
    a1.bar(x+w/2,fa,w,color=GOLD,label='% earned a favorite')
    for i in range(len(ks)):
        a1.text(i-w/2,ca[i]+0.35,f'{ca[i]}',ha='center',fontsize=8.4,color=TEAL,fontweight='bold')
        a1.text(i+w/2,fa[i]+0.35,f'{fa[i]}',ha='center',fontsize=8.4,color=GOLD,fontweight='bold')
    a1.set_xticks(x); a1.set_xticklabels([f'{k}-rm' for k in ks]); a1.set_ylabel('% of listings'); a1.set_ylim(0,32)
    a1.set_title('(a)  Intent incidence by room count',fontsize=10.5,fontweight='bold',loc='left')
    a1.legend(frameon=False,fontsize=8.5)
    ck=[R['dow'][d]['cpk'] for d in days]; fk=[R['dow'][d]['fpk'] for d in days]
    a2.bar(np.arange(7)-w/2,ck,w,color=TEAL,label='clicks / 1,000 listing-days')
    a2.bar(np.arange(7)+w/2,fk,w,color=GOLD,label='favorites / 1,000 listing-days')
    for i in range(7):
        a2.text(i-w/2,ck[i]+0.4,f'{ck[i]:.0f}',ha='center',fontsize=8,color=TEAL,fontweight='bold')
        a2.text(i+w/2,fk[i]+0.4,f'{fk[i]:.1f}',ha='center',fontsize=7.6,color=GOLD,fontweight='bold')
    a2.set_xticks(range(7)); a2.set_xticklabels(days); a2.set_ylabel('intent per 1,000 listing-days'); a2.set_ylim(0,22.5)
    a2.set_title('(b)  Intent by day of week',fontsize=10.5,fontweight='bold',loc='left')
    a2.legend(frameon=False,fontsize=8.5)
    plt.tight_layout(); plt.savefig(out('fig_s2_dimensions.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_s2_dimensions.pdf')


def build_exit_apartments():
    """S3 Exit velocity gap + renewal-wall decomposition"""
    global R, L, P
    apt = P


    # ---------- 7. EXIT ----------
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.4))
    b=a1.bar(['Stayed on market','Exited during window'],[R['vpd_stay'],R['vpd_exit']],color=[GOLD,TEAL],width=0.55)
    for bar,v in zip(b,[R['vpd_stay'],R['vpd_exit']]): a1.text(bar.get_x()+bar.get_width()/2,v+0.25,f'{v}',ha='center',fontweight='bold',fontsize=12)
    a1.set_ylabel('median new views / day'); a1.set_ylim(0,14)
    a1.set_title(f"(a)  {R['exit_gap']}\u00d7 the attention \u2014 before exit",fontsize=11,fontweight='bold',loc='left')
    a1.text(0.5,12.8,f"cohort present in week 1; {R['exit_rate']:.0f}% exited by 21 July",ha='center',fontsize=8,color=GREY,transform=a1.transData)
    labs=['Early exit\n(<42 days)','At renewal wall\n(42\u201344 days)','After renewal\n(>44 days)']
    shares=[R['exit_early_pct'],R['exit_wall_pct'],R['exit_late_pct']]
    vpds=[R['vpd_early_exit'],R['vpd_wall_exit'],R['vpd_late_exit']]
    cols=[TEAL,'#7FB0B8',RUST]
    b=a2.bar(labs,shares,color=cols,width=0.6)
    for bar,s,vv in zip(b,shares,vpds):
        a2.text(bar.get_x()+bar.get_width()/2,s+1.6,f'{s}%',ha='center',fontweight='bold',fontsize=10.5)
        a2.text(bar.get_x()+bar.get_width()/2,max(s-8,3),f'VPD {vv}',ha='center',fontsize=8.2,color='white' if s>12 else INK,fontweight='bold')
    a2.set_ylabel('share of exits'); a2.set_ylim(0,92)
    a2.set_title('(b)  Most exits are non-renewals at the 43-day term',fontsize=11,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_exit_apartments.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_exit_apartments.pdf')


def build_exit_dims():
    """S3 Exit rate by district / rooms"""
    global R, L, P
    apt = P
    dd=R['districts']


    # ============ S3 DIMENSIONS: exit by district | rooms ============
    dd=R['districts']; order=sorted(dd,key=lambda d:-dd[d]['absorp'])
    ex=[dd[d]['absorp'] for d in order]
    fig,(a1,a2)=plt.subplots(1,2,figsize=(11,4.2),gridspec_kw={'width_ratios':[1.7,1]})
    cmap=LinearSegmentedColormap.from_list('g',['#f5ecd8',GOLD])
    n=[(e-min(ex))/(max(ex)-min(ex)) for e in ex]
    b=a1.bar(range(len(order)),ex,color=[cmap(0.25+0.75*v) for v in n],width=0.66)
    for i,e in enumerate(ex): a1.text(i,e+1.2,f'{e:.0f}%',ha='center',fontsize=8.4,fontweight='bold')
    a1.set_xticks(range(len(order))); a1.set_xticklabels(order,rotation=32,ha='right',fontsize=8.4)
    a1.set_ylabel('% of week-one cohort exiting'); a1.set_ylim(0,84)
    a1.axhline(53,color=GREY,lw=1,ls='--'); a1.text(11.4,54.5,'city 53%',fontsize=7.5,color=GREY,ha='right')
    a1.set_title('(a)  Exit rate by district',fontsize=10.5,fontweight='bold',loc='left')
    er=R['exit_rooms']; ks2=sorted(er)
    b=a2.bar([f'{k}-rm' for k in ks2],[er[k] for k in ks2],color=GOLD,width=0.62)
    for bar,k in zip(b,ks2): a2.text(bar.get_x()+bar.get_width()/2,er[k]+1.2,f'{er[k]:.0f}%',ha='center',fontweight='bold',fontsize=9.5)
    a2.set_ylabel('% exiting'); a2.set_ylim(0,84)
    a2.set_title('(b)  Exit rate by room count',fontsize=10.5,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_exit_dims.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_exit_dims.pdf')


def build_tom_dims():
    """S4 ToM term-wall + stock age by district / rooms"""
    global R, L, P
    apt = P
    dd=R['districts']


    # ============ S4: ToM 3-panel ============
    comp=L.loc[L.exited & L.tom_completed.ge(0),'tom_completed']
    fig,axs=plt.subplots(1,3,figsize=(13,4))
    axs[0].hist(comp[comp<=120],bins=60,color=PURP,alpha=0.85,edgecolor='white',lw=0.3)
    axs[0].axvline(43,color=RUST,lw=2,ls='--'); axs[0].text(46,axs[0].get_ylim()[1]*0.88,'43-day\nlisting term',color=RUST,fontsize=8.5,fontweight='bold')
    axs[0].set_xlabel('completed time on market (days)'); axs[0].set_ylabel('exited listings')
    axs[0].set_title('(a)  Spells pile up at the term',fontsize=10.5,fontweight='bold',loc='left')
    order=sorted(dd,key=lambda d:dd[d]['age']); ages=[dd[d]['age'] for d in order]
    cmap=LinearSegmentedColormap.from_list('p',['#ece9f2',PURP])
    nrm=[(a-min(ages))/(max(ages)-min(ages)) for a in ages]
    axs[1].barh(range(len(order)),ages,color=[cmap(0.2+0.8*(1-v)) for v in nrm],height=0.68)
    for i,a in enumerate(ages): axs[1].text(a+0.6,i,f'{a:.0f}',va='center',fontsize=8,fontweight='bold')
    axs[1].set_yticks(range(len(order))); axs[1].set_yticklabels(order,fontsize=7.8); axs[1].invert_yaxis()
    axs[1].set_xlabel('median age of active stock (days)'); axs[1].set_xlim(0,47)
    axs[1].set_title('(b)  Stock age by district',fontsize=10.5,fontweight='bold',loc='left')
    ar=R['age_rooms']; ks3=sorted(ar)
    b=axs[2].bar([f'{k}-rm' for k in ks3],[ar[k] for k in ks3],color=PURP,width=0.62)
    for bar,k in zip(b,ks3): axs[2].text(bar.get_x()+bar.get_width()/2,ar[k]+1,f'{ar[k]}',ha='center',fontweight='bold',fontsize=9.5)
    axs[2].set_ylabel('median days live'); axs[2].set_ylim(0,58)
    axs[2].set_title('(c)  Stock age by room count',fontsize=10.5,fontweight='bold',loc='left')
    plt.tight_layout(); plt.savefig(out('fig_tom_dims.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_tom_dims.pdf')


def build_metrics_panel_apartments():
    """District heatmap: 4 framework signals"""
    global R, L, P
    apt = P
    import pandas as pd, numpy as np, json, matplotlib.pyplot as plt, matplotlib as mpl
    from matplotlib.colors import LinearSegmentedColormap
    mpl.rcParams['font.family']='DejaVu Sans'; mpl.rcParams['pdf.fonttype']=42
    GOLD='#C8A15A'; TEAL='#2E7D8A'; RUST='#B24C3C'; PURP='#6B5B95'; GREY='#9AA0A6'; INK='#2b2b2b'

    d=R['districts']; intent=R['intent_norm']

    # Build dataframe with the FOUR FRAMEWORK SIGNALS
    rows=[]
    for dist in d:
        rows.append(dict(district=dist, vpd=d[dist]['vpd'], click=intent[dist]['clicka'],
                         exit=d[dist]['absorp'], age=d[dist]['age']))
    D=pd.DataFrame(rows).set_index('district').sort_values('vpd',ascending=False)

    # columns: (key, title, subtitle, invert?, fmt)  invert=True -> lower is stronger demand
    cols=[('vpd','Views & Velocity','median new views / day',False,'{:.1f}'),
          ('click','Clicks & Saves','% of listings w/ a click',False,'{:.0f}%'),
          ('exit','Exit Rate','% of cohort exiting',False,'{:.0f}%'),
          ('age','Time on Market','median days live',True,'{:.0f}')]
    cmaps={'vpd':LinearSegmentedColormap.from_list('t',['#e8f0f1',TEAL]),
           'click':LinearSegmentedColormap.from_list('g',['#f5ecd8',GOLD]),
           'exit':LinearSegmentedColormap.from_list('r2',['#f4 e6 e2'.replace(' ',''),RUST]),
           'age':LinearSegmentedColormap.from_list('p',['#ece9f2',PURP])}
    colcolor={'vpd':TEAL,'click':GOLD,'exit':RUST,'age':PURP}

    def shade(vals,invert):
        v=np.array(vals,float); lo,hi=v.min(),v.max(); n=(v-lo)/(hi-lo+1e-9)
        return 1-n if invert else n

    fig,ax=plt.subplots(figsize=(9.6,7)); ax.axis('off')
    ax.set_xlim(0,4); ax.set_ylim(-1,len(D)+1.4)
    ax.text(2,len(D)+1.15,'Four demand signals across Tashkent districts \u2014 apartments only',
            ha='center',fontsize=13,fontweight='bold',color=INK)
    ax.text(2,len(D)+0.72,'Ordered by demand velocity. Each column shaded independently; darker = stronger demand (Time on Market shaded inversely).',
            ha='center',fontsize=7.6,color=GREY,style='italic')
    for j,(key,title,sub,inv,fmt) in enumerate(cols):
        n=shade(D[key],inv)
        ax.text(j+0.5,len(D)+0.18,title,ha='center',fontweight='bold',fontsize=10,color=colcolor[key])
        ax.text(j+0.5,len(D)-0.12,sub,ha='center',fontsize=7.3,color=GREY)
        for r in range(len(D)):
            val=D[key].iloc[r]; c=cmaps[key](0.15+0.85*n[r]); tc='white' if n[r]>0.55 else INK
            ax.add_patch(plt.Rectangle((j+0.06,len(D)-1-r-0.4),0.88,0.8,fc=c,ec='white',lw=1.6))
            ax.text(j+0.5,len(D)-1-r,fmt.format(val),ha='center',va='center',fontsize=9.5,color=tc,
                    fontweight='bold' if n[r]>0.8 else 'normal')
    for r in range(len(D)):
        ax.text(-0.06,len(D)-1-r,D.index[r],ha='right',va='center',fontsize=9.2,color=INK)
    ax.text(2,-0.85,'Source: authors\u2019 calculations, Uybor.uz daily panel, apartments, 24 June \u2013 21 July 2026. Bektemir n=11 (caution).',
            ha='center',fontsize=7,color=GREY)
    plt.tight_layout(); plt.savefig(out('fig_metrics_panel_apartments.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_metrics_panel_apartments.pdf')


def build_supply_demand_bands():
    """Supply vs demand by price band"""
    global R, L, P
    apt = P


    # ---------- 2. SUPPLY VS DEMAND BY PRICE BAND ----------
    bl=['<30k','30-50k','50-75k','75-100k','100-150k','150-250k','250k+']
    sup=[R['bands'][b]['supply'] for b in bl]; dem=[R['bands'][b]['medvpd'] for b in bl]
    fig,ax1=plt.subplots(figsize=(9,4.8))
    ax1.bar(range(7),sup,color='#e7e2da',edgecolor='#c9c2b6',width=0.72,zorder=2)
    for i,s in enumerate(sup): ax1.text(i,s+14,f'{s}',ha='center',fontsize=8.5,color=GREY)
    ax1.set_ylabel('Listings (supply)',fontsize=10); ax1.set_ylim(0,860)
    ax1.set_xticks(range(7)); ax1.set_xticklabels(bl,fontsize=9); ax1.set_xlabel('Price band (USD)')
    ax2=ax1.twinx(); ax2.spines['top'].set_visible(False)
    ax2.plot(range(7),dem,color=RUST,marker='o',lw=2.4,ms=7,zorder=3)
    for i,d in enumerate(dem): ax2.text(i+0.08,d+0.25,f'{d}',fontsize=9,color=RUST,fontweight='bold')
    ax2.set_ylabel('Median new views / day (demand)',color=RUST,fontsize=10); ax2.tick_params(axis='y',colors=RUST)
    ax2.set_ylim(0,11.5)
    ax1.set_title(r'Supply clusters at \$50\u2013150k; demand intensity peaks below \$30k',fontsize=12.5,fontweight='bold',loc='left',pad=12)
    fig.text(0.5,-0.02,SRC,ha='center',fontsize=7.3,color=GREY)
    plt.tight_layout(); plt.savefig(out('fig_supply_demand_bands.pdf'),bbox_inches='tight'); plt.close()
    print('  fig_supply_demand_bands.pdf')


def build_demand_map():
    """Demand bubble map + ranked panel"""
    global R, L, P
    apt = P
    import pandas as pd, numpy as np, json, matplotlib.pyplot as plt, matplotlib as mpl
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Ellipse
    import matplotlib.gridspec as gridspec
    mpl.rcParams['font.family']='DejaVu Sans'; mpl.rcParams['pdf.fonttype']=42
    INK='#3a3a3a'; GREY='#9AA0A6'; BG='#faf7f1'; PANEL='#faf7f1'

    cc=R['centroids']; d=R['districts']; vpct=R['vpct']

    # earthy pale->rust like reference
    cmap=LinearSegmentedColormap.from_list('reach',['#efe7d6','#e6c893','#d9a860','#c17b38','#a94e22'])
    vals=np.array([vpct[k] for k in cc]); vmin,vmax=vals.min(),vals.max()
    def col(v): return cmap((v-vmin)/(vmax-vmin))
    asp=np.cos(np.radians(41.3))

    fig=plt.figure(figsize=(13.5,8.4))
    gs=gridspec.GridSpec(1,2,width_ratios=[2.4,1],wspace=0.03)
    axm=fig.add_subplot(gs[0]); axr=fig.add_subplot(gs[1])

    # ---- MAP (rounded card background like reference) ----
    axm.set_facecolor(BG)
    for s in axm.spines.values(): s.set_color('#eae4d8'); s.set_linewidth(1)
    axm.set_xticks([]); axm.set_yticks([])

    pos={k:tuple(R['map_pos2'][k]) for k in cc}
    maxn=max(d[k]['nlist'] for k in cc)
    # bubble radius in degrees (latitude units); ellipse width divides by asp
    rad={k: R['map_rad2'][k] for k in cc}

    xs=[pos[k][0] for k in cc]; ys=[pos[k][1] for k in cc]
    padx=(max(xs)-min(xs))*0.14; pady=(max(ys)-min(ys))*0.16
    axm.set_xlim(min(xs)-padx,max(xs)+padx)
    axm.set_ylim(min(ys)-pady,max(ys)+pady*1.3)
    axm.set_aspect(1/asp)

    # faint listing cloud
    pcloud=apt=P.drop_duplicates('listing_id')[['longitude','latitude']].dropna()
    pcloud=pcloud[(pcloud.latitude.between(axm.get_ylim()[0],axm.get_ylim()[1]))&
                  (pcloud.longitude.between(axm.get_xlim()[0],axm.get_xlim()[1]))]
    axm.scatter(pcloud.longitude,pcloud.latitude,s=2.5,color='#cbb68f',alpha=0.30,zorder=1,linewidths=0)

    # bubbles (draw big->small), label ABOVE each
    for k in sorted(cc,key=lambda x:-d[x]['nlist']):
        v=vpct[k]; rr=rad[k]
        e=Ellipse(pos[k],width=rr*2/asp,height=rr*2,facecolor=col(v),
                  edgecolor='white',lw=2,zorder=3,alpha=0.97)
        axm.add_patch(e)
    for k in cc:
        rr=rad[k]
        below={'Shaykhantakhur','Mirabad','Yakkasaray'}
        if k in below:
            axm.text(pos[k][0],pos[k][1]-rr-0.006,k,ha='center',va='top',
                     fontsize=9.3,fontweight='bold',color=INK,zorder=5)
        else:
            axm.text(pos[k][0],pos[k][1]+rr+0.006,k,ha='center',va='bottom',
                     fontsize=9.3,fontweight='bold',color=INK,zorder=5)

    axm.set_title('Reach (views)',fontsize=12,fontweight='bold',loc='right',color='#7a6a58',pad=8)

    # color scale bar top-right of map
    cax=fig.add_axes([0.135,0.885,0.14,0.014])
    cax.imshow(np.linspace(0,1,256).reshape(1,-1),aspect='auto',cmap=cmap); cax.set_xticks([]); cax.set_yticks([])
    for s in cax.spines.values(): s.set_visible(False)
    fig.text(0.128,0.892,f'{vmin:.1f}',fontsize=8,color=GREY,ha='right',va='center')
    fig.text(0.285,0.892,f'{vmax:.1f}',fontsize=8,color=GREY,ha='left',va='center')

    # size legend (bottom-left of map)
    axsl=fig.add_axes([0.13,0.11,0.22,0.06]); axsl.axis('off'); axsl.set_xlim(0,1); axsl.set_ylim(0,1)
    axsl.text(0,0.85,'circle size = district stock',fontsize=8,color=INK,va='center')
    for i,(nn,lab) in enumerate([(50,'50'),(250,'250'),(570,'570')]):
        rr=(0.004+0.014*(nn/maxn)**0.5)*90
        x=0.10+i*0.30
        axsl.add_patch(plt.Circle((x,0.35),rr*0.02,fc='#cbb68f',ec='white',lw=1))
        axsl.text(x,0.02,lab,fontsize=7,color=GREY,ha='center')

    # ---- RANKED PANEL (reference style) ----
    axr.set_facecolor(PANEL)
    for s in axr.spines.values(): s.set_color('#eae4d8'); s.set_linewidth(1)
    axr.set_xticks([]); axr.set_yticks([]); axr.set_xlim(0,1); axr.set_ylim(0,1)
    axr.text(0.08,0.955,'Districts by reach (views)',fontsize=11.5,fontweight='bold',color=INK)
    axr.text(0.08,0.925,'view velocity, percentile',fontsize=8.5,color=GREY)
    order=sorted(cc,key=lambda x:-vpct[x])
    y0=0.86; dy=0.067
    for i,k in enumerate(order):
        y=y0-i*dy; v=vpct[k]
        axr.add_patch(plt.Rectangle((0.08,y-0.011),0.022,0.022,fc=col(v),ec='none'))
        axr.text(0.125,y,k,fontsize=9.3,color=INK,va='center')
        bw=0.28*(v-vmin)/(vmax-vmin+1e-9)
        axr.add_patch(plt.Rectangle((0.60,y-0.006),0.30,0.012,fc='#e7ded0',ec='none'))
        axr.add_patch(plt.Rectangle((0.60,y-0.006),max(bw,0.004),0.012,fc=col(v),ec='none'))
        axr.text(0.985,y,f'{v:.1f}',fontsize=9,color=INK,va='center',ha='right',fontweight='bold')

    fig.patch.set_facecolor('white')
    fig.text(0.5,0.02,'Each district plotted at the median coordinates of its listings; bubble size = cleaned stock, color = mean view-velocity percentile. '
             'Faint dots: individual apartments. Source: Uybor.uz daily panel, apartments, 24 June \u2013 21 July 2026.',
             ha='center',fontsize=7.2,color=GREY)
    plt.savefig(out('fig_demand_map.pdf'),bbox_inches='tight',facecolor='white'); plt.close()
    print('  fig_demand_map.pdf')


ALL_FIGURES = [
    build_evidence_map,
    build_concentration_apartments,
    build_s1_dimensions,
    build_funnel_apartments,
    build_wedge_apartments,
    build_intent_norm_districts,
    build_s2_dimensions,
    build_exit_apartments,
    build_exit_dims,
    build_tom_dims,
    build_metrics_panel_apartments,
    build_supply_demand_bands,
    build_demand_map
]

def main():
    _load()
    print("[figures] building", len(ALL_FIGURES), "figures ->", config.FIG_DIR)
    for fn in ALL_FIGURES:
        fn()
    print("[figures] done")

if __name__ == "__main__":
    main()
