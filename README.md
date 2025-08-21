# Installations-Wirtschaftlichkeit – Streamlit App

Interaktive Kalkulation zur Wirtschaftlichkeit bei der Installation von Zählern, AMR, HKVE und Rauchmeldern.

## Funktionen
- Bearbeiten Sie **Stückzahlen, Preise, Montagezeiten** je Gerät live in einer Tabelle.
- Setzen Sie **Stundenlohn, Mitarbeiteranzahl, Stunden/Tag**, **Fahrtkosten (€ / km)** und **Sonder-/Wartezeit** (Satz & Stunden).
- Wählen Sie ein **Projekt** (Stadt/Objekt) zur Vorbelegung der Mengen oder arbeiten Sie **manuell**.
- Automatische Berechnung von **Erlös, Arbeitsstunden, Lohnkosten, Deckungsbeitrag**, Marge und kalkulierten Arbeitstagen.
- **Excel-Export** mit Detail- und Summary-Blättern.
- **Pflege der Stammdaten** über `assets/data/catalog.csv` und `assets/data/projects.csv`.

## Installation

**Empfohlen:** Python 3.10–3.12.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Hinweis zu Linux/Python 3.13:** Falls bei `pandas` Build-Fehler auftreten, verwenden Sie Python 3.12 oder 3.11 (z.B. mit `pyenv`/`conda`), da für einige Distributionen noch keine Wheels bereitstehen.

## Start

```bash
streamlit run app.py
```

Die App lädt Katalog- und Projektdaten aus `assets/data/*.csv`. Sie können diese Dateien beliebig anpassen.

## Datenfelder

- **catalog.csv**: `Kategorie, Gerät, Std_pro_Einheit, Preis_EUR, Anzahl`
- **projects.csv**: `Stadt, Objekt, Wasserzähler, WMZ, KMZ, HKV, Bemerkungen`

Bei Projektwahl werden die Mengen je Kategorie **als Startwert** auf die erste Zeile der jeweiligen Kategorie gelegt (zur schnellen Anpassung).

## Lizenz
MIT – Use at your own risk.


## Stadt-Cluster
Unter dem Tab **„Stadt-Cluster“** können Städte per **K-Means** gruppiert werden.
- Wählen Sie die **Features** (Wasserzähler, WMZ, KMZ, HKV).
- Legen Sie **k** (2–8) fest.
- Ergebnis als Tabelle und **PCA-Scatterplot** (matplotlib), plus **CSV-Export**.
