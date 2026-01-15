
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FICHIER_VOITURE = "donnees_voiture.json"
FICHIER_VELO    = "donnees_velo.json"

TS_8 = "2026-01-08 08:37:41"  
TS_7 = "2026-01-07 13:25:32"   

VAR_TOL = 1e-6  
EXCLUDE_CARS_MANUAL  = set()  
EXCLUDE_BIKES_MANUAL = set()   

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

car_raw  = load_json(FICHIER_VOITURE)
bike_raw = load_json(FICHIER_VELO)

# Voitures
car_rows = []
for snap in car_raw:
    ts = pd.to_datetime(snap["horodatage"]).strftime("%Y-%m-%d %H:%M:%S")
    for rec in snap["donnees"]:
        car_rows.append({
            "horodatage": ts,
            "parking": rec["nom"],
            "places_libres": rec["places_libres"],
            "places_totales": rec["places_totales"],
        })
car_df = pd.DataFrame(car_rows)
car_df["occupation"] = car_df["places_totales"] - car_df["places_libres"]
car_df["taux_occupation"] = (car_df["occupation"] / car_df["places_totales"]).clip(0, 1)

# Vélos
bike_rows = []
for snap in bike_raw:
    ts = pd.to_datetime(snap["horodatage"]).strftime("%Y-%m-%d %H:%M:%S")
    for rec in snap["donnees"]:
        cap = rec["velos_dispo"] + rec["bornes_libres"]
        taux = (rec["velos_dispo"] / cap) if cap > 0 else np.nan
        bike_rows.append({
            "horodatage": ts,
            "station": rec["station"],
            "velos_dispo": rec["velos_dispo"],
            "bornes_libres": rec["bornes_libres"],
            "capacite_totale": cap,
            "taux_occupation": taux,
        })
bike_df = pd.DataFrame(bike_rows)
bike_df["taux_occupation"] = bike_df["taux_occupation"].clip(0, 1)

# les bugs
car_var = (car_df.groupby("parking")["taux_occupation"]
           .agg(std=lambda s: float(np.nanstd(s.values)), nunique="nunique")
           .reset_index())
buggy_cars = set(car_var.loc[(car_var["std"] <= VAR_TOL) | (car_var["nunique"] <= 1), "parking"])
buggy_cars |= EXCLUDE_CARS_MANUAL

bike_var = (bike_df.groupby("station")["taux_occupation"]
            .agg(std=lambda s: float(np.nanstd(s.values)), nunique="nunique")
            .reset_index())
buggy_bikes = set(bike_var.loc[(bike_var["std"] <= VAR_TOL) | (bike_var["nunique"] <= 1), "station"])
buggy_bikes |= EXCLUDE_BIKES_MANUAL

def _bar_chart(x_labels, y_vals, title, filename, color="#1f77b4"):
    plt.figure(figsize=(16, 8))
    bars = plt.bar(x_labels, np.array(y_vals)*100, color=color, edgecolor="white")
    plt.xticks(rotation=70, ha="right")
    plt.ylabel("Taux d'occupation (%)")
    plt.title(title)
    for rect, val in zip(bars, y_vals):
        plt.text(rect.get_x() + rect.get_width()/2.0,
                 rect.get_height() + 0.5,
                 f"{val*100:.1f}%",
                 ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

def plot_bar_taux(df, ts, label_col, taux_col, exclude_set, title, filename):

    d = df[df["horodatage"] == ts].copy()
    d = d[~d[label_col].isin(exclude_set)]
    d = d[np.isfinite(d[taux_col])]

    if d.empty:
        d = df[df["horodatage"] == ts].copy()
        d = d[np.isfinite(d[taux_col])]
        if d.empty:
            return
    d = d.sort_values(taux_col, ascending=False)
    _bar_chart(d[label_col].tolist(), d[taux_col].tolist(), title, filename)

def plot_grouped_bars(df_cars, df_bikes, ts, title, filename,
                      cars_excl, bikes_excl, max_sites=40):

    c = df_cars[df_cars["horodatage"] == ts][["parking", "taux_occupation"]].copy()
    c = c[~c["parking"].isin(cars_excl)]
    b = df_bikes[df_bikes["horodatage"] == ts][["station", "taux_occupation"]].copy()
    b = b[~b["station"].isin(bikes_excl)]

    if c.empty:
        c = df_cars[df_cars["horodatage"] == ts][["parking", "taux_occupation"]].copy()
    if b.empty:
        b = df_bikes[df_bikes["horodatage"] == ts][["station", "taux_occupation"]].copy()

    mapping = {
        "Antigone": "Antigone centre",
        "Comedie": "Comédie",
        "Corum": "Corum",
        "Foch": "Foch",
        "Gambetta": "Gambetta",
        "Gare": "Rue Jules Ferry - Gare Saint-Roch",
        "Pitot": "Les Arceaux",
        "Circe": "Odysseum",
        "Garcia Lorca": "Garcia Lorca",
        "Euromedecine": "Euromédecine",
        "Occitanie": "Occitanie",
    }

    c["station_nominal"] = c["parking"].map(mapping)
    merged = c.merge(b, left_on="station_nominal", right_on="station", how="inner",
                     suffixes=("_car", "_bike"))


    if merged.empty:
        b2 = b.copy(); b2["station_low"] = b2["station"].str.lower()
        c2 = c.copy(); c2["parking_low"] = c2["parking"].str.lower()
        merged = c2.merge(b2, left_on="parking_low", right_on="station_low", how="inner",
                          suffixes=("_car", "_bike"))

        if not merged.empty:
            merged.rename(columns={
                "parking": "parking",
                "taux_occupation_car": "taux_occupation_car",
                "taux_occupation_bike": "taux_occupation_bike"
            }, inplace=True)

    if merged.empty:
        return

    merged = merged.sort_values("taux_occupation_car", ascending=False).head(max_sites)
    labels = merged["parking"].tolist()
    y_car  = merged["taux_occupation_car"].tolist()
    y_bike = merged["taux_occupation_bike"].tolist()

    x = np.arange(len(labels))
    width = 0.42

    plt.figure(figsize=(16, 8))
    r1 = plt.bar(x - width/2, np.array(y_car)*100, width, label="Voitures", color="#1f77b4", edgecolor="white")
    r2 = plt.bar(x + width/2, np.array(y_bike)*100, width, label="Vélos",    color="#ff7f0e", edgecolor="white")

    plt.xticks(x, labels, rotation=70, ha="right")
    plt.ylabel("Taux d'occupation (%)")
    plt.title(title)
    plt.legend()

    for rects, vals in [(r1, y_car), (r2, y_bike)]:
        for rect, val in zip(rects, vals):
            plt.text(rect.get_x() + rect.get_width()/2.0,
                     rect.get_height() + 0.5,
                     f"{val*100:.1f}%",
                     ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()

# cree des graphique de taux d occupation que nous navons finalement pas utiliser car les graphique comparatif sont plus parlant
plot_bar_taux(
    car_df, TS_8, "parking", "taux_occupation", buggy_cars,
    "Taux d'occupation — Parkings VOITURES — 2026-01-08 08:37",
    "taux_voiture_2026-01-08_08-37.png"
)
plot_bar_taux(
    bike_df, TS_8, "station", "taux_occupation", buggy_bikes,
    "Taux d'occupation — Stations VÉLOS — 2026-01-08 08:37",
    "taux_velo_2026-01-08_08-37.png"
)
plot_bar_taux(
    car_df, TS_7, "parking", "taux_occupation", buggy_cars,
    "Taux d'occupation — Parkings VOITURES — 2026-01-07 13:25",
    "taux_voiture_2026-01-07_13-25.png"
)
plot_bar_taux(
    bike_df, TS_7, "station", "taux_occupation", buggy_bikes,
    "Taux d'occupation — Stations VÉLOS — 2026-01-07 13:25",
    "taux_velo_2026-01-07_13-25.png"
)

# graphique comparatif
plot_grouped_bars(
    car_df, bike_df, TS_8,
    "Comparatif VOITURES vs VÉLOS — 2026-01-08 08:37 (barres groupées par site)",
    "comparatif_voiture_vs_velo_2026-01-08_08-37.png",
    cars_excl=buggy_cars, bikes_excl=buggy_bikes, max_sites=40
)
plot_grouped_bars(
    car_df, bike_df, TS_7,
    "Comparatif VOITURES vs VÉLOS — 2026-01-07 13:25 (barres groupées par site)",
    "comparatif_voiture_vs_velo_2026-01-07_13-25.png",
    cars_excl=buggy_cars, bikes_excl=buggy_bikes, max_sites=40
)