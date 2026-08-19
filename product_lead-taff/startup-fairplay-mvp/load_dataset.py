"""
Charge les CSV générés par generate_dataset.py dans une base SQLite créée
à partir de growth-decision-os-schema.sql. Sert à valider que le dataset
respecte bien le schéma (types, contraintes, clés étrangères) et permet
de lancer directement les vues v_couverture_stock / v_reputation_7j dessus.
"""

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("dataset_output/growth_decision_os.db")
CSV_DIR = Path("dataset_output")
SCHEMA_PATH = Path("growth-decision-os-schema.sql")

TABLES = [
    ("categorie.csv", "categorie",
     ["categorie_id", "nom", "famille"]),
    ("produit.csv", "produit",
     ["product_id", "nom", "categorie_id", "sous_categorie", "prix_unitaire",
      "unite", "duree_de_vie_jours", "fournisseur_id"]),
    ("boutique.csv", "boutique",
     ["store_id", "nom", "ville", "zone", "type", "date_ouverture", "actif"]),
    ("vente.csv", "vente",
     ["vente_id", "date", "store_id", "product_id", "quantite", "prix_unitaire", "canal"]),
    ("stock.csv", "stock",
     ["snapshot_id", "date", "store_id", "product_id", "quantite_disponible",
      "seuil_min", "seuil_max"]),
    ("avis_client.csv", "avis_client",
     ["avis_id", "date", "store_id", "product_id", "note", "texte", "sentiment", "canal"]),
]


def charger():
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text())

    for csv_name, table, colonnes in TABLES:
        chemin = CSV_DIR / csv_name
        with open(chemin, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            lignes = []
            for r in reader:
                valeurs = []
                for c in colonnes:
                    v = r[c]
                    valeurs.append(None if v == "" else v)
                lignes.append(valeurs)

        placeholders = ", ".join(["?"] * len(colonnes))
        sql = f"INSERT INTO {table} ({', '.join(colonnes)}) VALUES ({placeholders})"
        conn.executemany(sql, lignes)
        print(f"{table:<15} {len(lignes)} lignes chargées")

    conn.commit()
    return conn


def valider(conn):
    print("\n--- Validation via les vues du schéma ---")

    print("\nCouverture de stock la plus faible (top 5, risque potentiel) :")
    for row in conn.execute(
        "SELECT store_id, product_id, quantite_disponible, seuil_min, couverture_jours "
        "FROM v_couverture_stock WHERE couverture_jours IS NOT NULL "
        "ORDER BY couverture_jours ASC LIMIT 5"
    ):
        print(" ", row)

    print("\nRéputation 7 derniers jours par boutique :")
    for row in conn.execute(
        "SELECT store_id, note_moyenne_7j, nb_avis_7j, pct_avis_negatifs FROM v_reputation_7j"
    ):
        print(" ", row)

    print("\nContrôle clés étrangères (doit être vide) :")
    problemes = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(" ", problemes if problemes else "OK — aucune violation")


if __name__ == "__main__":
    conn = charger()
    valider(conn)
    conn.close()
    print(f"\nBase SQLite écrite : {DB_PATH}")
