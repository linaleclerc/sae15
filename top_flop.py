import pandas as pd
import matplotlib.pyplot as plt
import json
with open('donnees_voiture.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

rows = []
for entry in raw:
    for rec in entry["donnees"]:
        if rec["places_totales"] > 0:
            rows.append({
                "parking": rec["nom"],
                "taux_occupation": (1 - rec["places_libres"] / rec["places_totales"]) * 100
            })

sub = pd.DataFrame(rows)

stats = sub.groupby('parking').agg(
    mean=('taux_occupation', 'mean'),
    std=('taux_occupation', 'std'),
    n=('taux_occupation', 'count')
).reset_index()

stats_propres = stats[(stats['n'] > 1) & (stats['std'] > 2)]
stats_triee = stats_propres.sort_values('mean', ascending=False)

top_5 = stats_triee.head(5)
flop_5 = stats_triee.tail(5)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))

top_5.plot(kind='bar', x='parking', y='mean', ax=ax1, color='#d32f2f', legend=False)
ax1.set_title('TOP 5 : Parkings les plus saturés (%)', fontweight='bold')
ax1.set_ylabel('Taux moyen (%)')
ax1.set_ylim(0, 100)

flop_5.sort_values('mean').plot(kind='bar', x='parking', y='mean', ax=ax2, color='#388e3c', legend=False)
ax2.set_title('FLOP 5 : Parkings les moins utilisés (%)', fontweight='bold')
ax2.set_ylabel('Taux moyen (%)')
ax2.set_ylim(0, 100)

plt.tight_layout()

plt.savefig('top_flop.png', dpi=300)
print("graphique créé.")

plt.show()