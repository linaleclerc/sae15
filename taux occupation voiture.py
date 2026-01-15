import json, pandas as pd, matplotlib.pyplot as plt
from datetime import datetime


with open('donnees_voiture1.json','r',encoding='utf-8') as f:
    raw = json.load(f)

rows = []
for entry in raw:
    dt = datetime.strptime(entry['horodatage'], '%Y-%m-%d %H:%M:%S')
    for rec in entry['donnees']:
        rows.append({
            'date': dt.date().isoformat(),
            'heure': dt.time().isoformat(timespec='minutes'),
            'parking': rec['nom'],
            'places_libres': rec['places_libres'],
            'places_totales': rec['places_totales']
        })

df = pd.DataFrame(rows)
df['taux_occupation'] = (1 - df['places_libres']/df['places_totales']) * 100


DATES = ['2026-01-07','2026-01-09']

plt.style.use('seaborn-v0_8')

for d in DATES:
    sub = df[df['date']==d].copy()

    # retire les parking qui bug
    stats = sub.groupby('parking').agg(
        mean=('taux_occupation','mean'),
        std=('taux_occupation','std'),
        n=('taux_occupation','count')
    ).reset_index()
    stats = stats[(stats['n'] > 1) & (stats['std'] > 0)].sort_values('mean', ascending=False)

   
    hmin = sub['heure'].min() if not sub.empty else ''
    hmax = sub['heure'].max() if not sub.empty else ''

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(stats['parking'], stats['mean'], color='#1f77b4')
    ax.set_title(f"Taux d'occupation des parkings — {d} de {hmin} à {hmax}")
    ax.set_xlabel("Parkings")
    ax.set_ylabel("% d'occupation (moyenne)")
    ax.set_ylim(0, 100)
    plt.xticks(rotation=75, ha='right')

    for x, v in zip(range(len(stats)), stats['mean']):
        ax.text(x, v + 1, f"{v:.0f}%", ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    fig.savefig(f"taux_occcupatiton{d}.png", dpi=200)
    plt.close(fig)

print("2 graphiques crée s")
