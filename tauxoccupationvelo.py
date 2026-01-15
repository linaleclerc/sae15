import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

with open('donnees_velo1.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

rows = []
for entry in raw:
    dt = datetime.strptime(entry['horodatage'], '%Y-%m-%d %H:%M:%S')
    for rec in entry['donnees']:
        capa = rec['velos_dispo'] + rec['bornes_libres']
        if capa > 0:
            rows.append({
                'timestamp': dt,
                'date': dt.date().isoformat(),
                'heure_str': dt.strftime('%H:%M'),
                'station': rec['station'],
                'taux': (rec['velos_dispo'] / capa) * 100
            })

df = pd.DataFrame(rows)

best_date = None
max_duration = 0

for d in df['date'].unique():
    temp = df[df['date'] == d]
    duration = (temp['timestamp'].max() - temp['timestamp'].min()).total_seconds() / 3600
    if duration >= 6 and duration > max_duration:
        max_duration = duration
        best_date = d

if best_date:
    sub = df[df['date'] == best_date].copy()
    h_debut, h_fin = sub['heure_str'].min(), sub['heure_str'].max()
    
    stats = sub.groupby('station')['taux'].agg(['mean', 'std', 'count']).reset_index()
    stats = stats[(stats['count'] > 1) & (stats['std'] > 0)]

    top_5 = stats.sort_values('mean', ascending=False).head(5)
    flop_5 = stats.sort_values('mean', ascending=True).head(5)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))
    plt.style.use('seaborn-v0_8')

    ax1.bar(top_5['station'], top_5['mean'], color='#e74c3c')
    ax1.set_title(f"Plus fortes occupations\n({best_date} de {h_debut} à {h_fin})")
    ax1.set_ylim(0, 110)

    ax2.bar(flop_5['station'], flop_5['mean'], color='#2ecc71')
    ax2.set_title(f"Plus faibles occupations\n({best_date} de {h_debut} à {h_fin})")
    ax2.set_ylim(0, 110)

    for ax in [ax1, ax2]:
        ax.set_ylabel("% d'occupation moyen")
        for p in ax.patches:
            ax.annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width()/2., p.get_height()),
                        ha='center', va='bottom', xytext=(0, 5), textcoords='offset points')
        plt.setp(ax.get_xticklabels(), rotation=20, ha="right")

    plt.tight_layout()
    fig.savefig(f"taux_occupation-velo.png", dpi=200)
    print(f"Graphique créé")
