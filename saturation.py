

import json, textwrap
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

SEUIL = 90.0
JSON_FILE = "donnees_voiture.json"


with open(JSON_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

rows = []
for entry in raw:
    dt = datetime.strptime(entry["horodatage"], "%Y-%m-%d %H:%M:%S")
    for rec in entry["donnees"]:
        rows.append({
            "datetime": dt,
            "date": dt.date().isoformat(),
            "heure": dt.time().isoformat(timespec="minutes"),
            "parking": rec["nom"],
            "libres": rec["places_libres"],
            "tot": rec["places_totales"]
        })

df = pd.DataFrame(rows)
df["taux"] = (1 - df["libres"] / df["tot"]) * 100

# retire les parking fqui bug
stats = df.groupby("parking").agg(n=("taux","count"), std=("taux","std")).reset_index()
faulty = set(stats.loc[(stats["n"]<=1) | (stats["std"].fillna(0)<=1e-9), "parking"])
df_ok = df[~df["parking"].isin(faulty)].copy()

peaks = df_ok.sort_values("taux").groupby("parking").tail(1)[["parking","date","heure","taux"]]
peaks = peaks.sort_values("taux", ascending=False)

peaks90 = peaks[peaks["taux"] >= SEUIL].copy()
use = peaks90 if len(peaks90) >= 5 else peaks.head(5)

caption_lines = [f"• {row.parking} : {row.date} {row.heure}" for row in use.itertuples(index=False)]
caption = "\n".join(caption_lines)

plt.style.use("seaborn-v0_8")
fig, ax = plt.subplots(figsize=(max(10, len(use)*1.2), 6))
bars = ax.bar(use["parking"], use["taux"], color="#2c7fb8", width=0.55)
ax.set_ylim(0, 100)
ax.set_ylabel("% d'occupation (pic observé)")
ax.set_xlabel("Parkings")
ax.set_title("Pics d'occupation par parking ")
plt.xticks(rotation=30, ha="right")

for rect, v in zip(bars, use["taux"]):
    ax.text(rect.get_x()+rect.get_width()/2., v+1, f"{v:.1f}%", ha="center", va="bottom", fontsize=10)

ax.axhline(90, color="#d62728", linestyle="--", linewidth=1, alpha=0.7)
ax.text(0.99, 0.90, "Seuil 90%", color="#d62728", ha="right", va="bottom", transform=ax.transAxes, fontsize=9)

wrapped = textwrap.fill(caption, width=120, break_long_words=False, replace_whitespace=False)
fig.text(0.01, 0.01, f"Dates/heures des pics :\n{wrapped}", fontsize=9, va="bottom", ha="left")

plt.tight_layout(rect=[0, 0.08, 1, 1])
fig.savefig("saturation.png", dpi=200)
plt.close(fig)

print("graphique crée")
