
import json, textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

SEUIL_SURDIM = 40.0
PERCENTILE = 95
JSON_FILE = "donnees_voiture.json"  

with open(JSON_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

rows = []
for entry in raw:
    dt = datetime.strptime(entry["horodatage"], "%Y-%m-%d %H:%M:%S")
    for rec in entry["donnees"]:
        tot = rec["places_totales"]
        libres = rec["places_libres"]
        occ_pct = (1 - libres / tot) * 100 if tot else np.nan
        rows.append({
            "datetime": dt,
            "date": dt.date().isoformat(),
            "heure": dt.time().isoformat(timespec="minutes"),
            "parking": rec["nom"],
            "libres": libres,
            "tot": tot,
            "taux": occ_pct
        })

df = pd.DataFrame(rows).dropna(subset=["taux"]).copy()

stats = df.groupby("parking").agg(
    n=("taux","count"),
    std=("taux","std")
).reset_index()

faulty = set(stats.loc[(stats["n"] <= 1) | (stats["std"].fillna(0) <= 1e-9), "parking"])
df_ok = df[~df["parking"].isin(faulty)].copy()

def p_high(g):
    if len(g) >= 10:
        return np.nanpercentile(g, PERCENTILE)
    return np.nanpercentile(g, max(90, PERCENTILE - 5))

high = df_ok.groupby("parking")["taux"].apply(p_high).reset_index(name="p_high")

peaks = df_ok.sort_values("taux").groupby("parking").tail(1)[["parking","date","heure","taux"]]
peaks = peaks.rename(columns={"taux":"pic_observe"})
summary = high.merge(peaks, on="parking", how="left")

surdim = summary[summary["p_high"] < SEUIL_SURDIM].sort_values("p_high", ascending=True)

use = surdim if len(surdim) >= 5 else summary.sort_values("p_high", ascending=True).head(5)

caption_lines = [f"• {row.parking} — {row.date}" for row in use.itertuples(index=False)]
caption = "\n".join(caption_lines)

plt.style.use("seaborn-v0_8")
fig, ax = plt.subplots(figsize=(max(10, len(use)*1.2), 6))

bars = ax.bar(use["parking"], use["p_high"], color="#1b9e77", width=0.55)
ax.set_ylim(0, 100)
ax.set_ylabel("% d'occupation (quantile haut)")
ax.set_xlabel("Parkings")
ax.set_title(f"Parkings potentiellement surdimensionnés (seuil {SEUIL_SURDIM:.0f}%)")
plt.xticks(rotation=30, ha="right")


ax.axhline(SEUIL_SURDIM, color="#d62728", linestyle="--", linewidth=1, alpha=0.7)
ax.text(0.99, SEUIL_SURDIM/100, f"Seuil {SEUIL_SURDIM:.0f}%", color="#d62728",
        ha="right", va="bottom", transform=ax.get_yaxis_transform(), fontsize=9)

wrapped = textwrap.fill(caption, width=120, break_long_words=False, replace_whitespace=False)
fig.text(0.01, 0.01, wrapped, fontsize=9, va="bottom", ha="left")

plt.tight_layout(rect=[0, 0.08, 1, 1])
fig.savefig("surdimension.png", dpi=200)
plt.close(fig)

print("surdimension.png créé")
