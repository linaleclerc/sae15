import requests
import json
import time
from datetime import datetime

URL_PARKINGS = "https://portail-api-data.montpellier3m.fr/offstreetparking?limit=1000"
URL_VELO = "https://portail-api-data.montpellier3m.fr/bikestation?limit=1000"

FICHIER_PARKING = "donnees_voiture_fin.json"
FICHIER_VELO = "donnees_velo_fin.json"

# 2 jours de mesures (1 toutes les 30 min)
NB_MESURES = int(2 * 48)  
TEMPS_ATTENTE = 1800      


def get_val(item, key):
    return item.get(key, {}).get('value')

def recuperer_et_filtrer():
    maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # voiture
    data_parking_clean = None
    try:
        r = requests.get(URL_PARKINGS, timeout=10)
        if r.status_code == 200:
            raw_data = r.json()
            liste_propre = []
            
            for p in raw_data:
                parking_simple = {
                    "nom": get_val(p, 'name'),
                    "statut": get_val(p, 'status'),
                    "places_libres": get_val(p, 'availableSpotNumber'),
                    "places_totales": get_val(p, 'totalSpotNumber')
                }
                liste_propre.append(parking_simple)
            
            data_parking_clean = {
                "horodatage": maintenant,
                "donnees": liste_propre
            }
    except Exception as e:
        print(f"erreur Parking: {e}")

    #velo
    data_velo_clean = None
    try:
        r = requests.get(URL_VELO, timeout=10)
        if r.status_code == 200:
            raw_data = r.json()
            liste_propre = []
            
       
            for v in raw_data:
                adresse = get_val(v, 'address').get('streetAddress', 'Inconnu') if get_val(v, 'address') else "Inconnu"
                
                velo_simple = {
                    "station": adresse,
                    "velos_dispo": get_val(v, 'availableBikeNumber'),
                    "bornes_libres": get_val(v, 'freeSlotNumber')
                }
                liste_propre.append(velo_simple)
            
            data_velo_clean = {
                "horodatage": maintenant,
                "donnees": liste_propre
            }
    except Exception as e:
        print(f" Erreur Vélo: {e}")

    return data_parking_clean, data_velo_clean


def charger_historique(nom):
    try:
        with open(nom, "r", encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def sauvegarder(nom, data):
    with open(nom, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


historique_p = charger_historique(FICHIER_PARKING)
historique_v = charger_historique(FICHIER_VELO)


print(f"Stockage dans : {FICHIER_PARKING} et {FICHIER_VELO}")

for i in range(NB_MESURES):
    print(f"\n Mesure {i+1}/{NB_MESURES} - {datetime.now().strftime('%H:%M:%S')}")
    

    res_p, res_v = recuperer_et_filtrer()

    if res_p:
        historique_p.append(res_p)
        sauvegarder(FICHIER_PARKING, historique_p)
        print(f" Parkings enregistrés ({len(res_p['donnees'])} parkings)")
    
    if res_v:
        historique_v.append(res_v)
        sauvegarder(FICHIER_VELO, historique_v)
        print(f" Vélos enregistrés ({len(res_v['donnees'])} stations)")


    if i < NB_MESURES - 1:
        time.sleep(TEMPS_ATTENTE)

print("\nFin du programme.")