import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

with open('donnees_voiture.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

DATE_CIBLE = "2026-01-07"
rows = []

for entry in raw_data:
    dt = datetime.strptime(entry['horodatage'], '%Y-%m-%d %H:%M:%S')
    for p in entry['donnees']:
        if p['places_totales'] > 0:
            taux = (1 - p['places_libres'] / p['places_totales']) * 100
            rows.append({
                'date': entry['horodatage'].split(' ')[0], 
                'heure': dt,
                'nom': p['nom'],
                'taux': taux
            })

df = pd.DataFrame(rows)


stats = df.groupby('nom')['taux'].agg(['std', 'count']).reset_index()

parkings_valides = stats[stats['std'] > 0]['nom'].tolist()

selection_souhaitee = [
    'Comedie', 'Polygone', 'Corum', 'Foch',          
    'Occitanie', 'Sabines', 'Circé', 'Garcia Lorca',
    'Gare', 'Arc de Triomphe'                       
]

selection_finale = [p for p in selection_souhaitee if p in parkings_valides]

df_filtered = df[(df['date'] == DATE_CIBLE) & (df['nom'].isin(selection_finale))]
df_filtered = df_filtered.sort_values('heure')

plt.figure(figsize=(15, 8))
plt.style.use('seaborn-v0_8')

for nom in selection_finale:
    donnees_parking = df_filtered[df_filtered['nom'] == nom]
    if not donnees_parking.empty:
        plt.plot(donnees_parking['heure'], donnees_parking['taux'], label=nom, linewidth=2.5)

plt.title(f"Évolution temporelle des parkings", fontsize=16)
plt.xlabel("Temps (Heures)", fontsize=12)
plt.ylabel("% d'occupation", fontsize=12)
plt.ylim(0, 105)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(title="Parkings", loc='center left', bbox_to_anchor=(1, 0.5))

plt.tight_layout()
nom_fichier = f"comparaison_parkings_propres_{DATE_CIBLE}.png"
plt.savefig(nom_fichier, dpi=300)
plt.show()

print(f"Graphique enregistré. Parkings exclus car figés : {set(selection_souhaitee) - set(selection_finale)}")