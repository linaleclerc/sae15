import pandas as pd
import matplotlib.pyplot as plt
import json

CENTRE = ['Comedie', 'Foch', 'Polygone', 'Triangle', 'Arc de Triomphe']
RELAIS = ['Sabines', 'Occitanie', 'Circé', 'Garcia Lorca', 'Mosson']

with open('donnees_voiture.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

rows = []
for entry in raw:
    ts = pd.to_datetime(entry["horodatage"])
    for rec in entry["donnees"]:
        if rec["places_totales"] > 0:
            rows.append({
                "Temps": ts,
                "parking": rec["nom"],
                "Taux": (1 - rec["places_libres"] / rec["places_totales"]) * 100
            })

df = pd.DataFrame(rows)

stats = df.groupby('parking')['Taux'].agg(std='std', n='count').reset_index()
parkings_ok = stats[(stats['n'] > 1) & (stats['std'] > 0)]['parking'].tolist()

df_propre = df[df['parking'].isin(parkings_ok)].copy()

def attribuer_zone(nom):
    if nom in CENTRE: return "Centre-Ville"
    if nom in RELAIS: return "Parking Relais"
    return "Autre"

df_propre['Zone'] = df_propre['parking'].apply(attribuer_zone)
df_final = df_propre[df_propre['Zone'] != "Autre"]

# Graphique
df_zones = df_final.groupby([df_final['Temps'].dt.hour, 'Zone'])['Taux'].mean().unstack()
df_zones.plot(figsize=(12, 6), linewidth=3)
plt.title("Comparaison entre parking du centre-Ville et Parking Relais ")
plt.ylabel("% d'occupation moyen")
plt.xlabel("Heure de la journée")
plt.grid(True)
plt.savefig("comparaison_parking_ville_relais.png")
plt.show()