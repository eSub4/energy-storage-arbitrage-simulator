# Optimierung des Rolling-Window-Horizonts für Batteriespeicher-Arbitrage

## 📊 Bachelorarbeit

**Forschungsfrage:** *"Welcher Rolling-Window-Horizont maximiert den Arbitragegewinn eines Batteriespeichers, der mittels eines heuristischen Preisschwellen-Algorithmus mit Lookahead-Funktion auf Basis historischer deutscher Day-Ahead-Großhandelspreise des Jahres 2024 in 15-minütiger Auflösung operiert?"*

## 🎯 Projektziel

Diese Arbeit untersucht die optimale Zeitfenstergröße für die vorausschauende Optimierung von Batteriespeicher-Handelsstrategien im deutschen Strommarkt. Durch die Analyse verschiedener Rolling-Window-Horizonte wird ermittelt, welche Lookahead-Periode die höchsten Arbitragegewinne bei der Ausnutzung von Preisschwankungen ermöglicht.

## 🔋 Kernkomponenten

### Datengrundlage
- **Marktdaten**: Deutsche Day-Ahead-Großhandelspreise 2024 (SMARD)
- **Zeitauflösung**: 15-Minuten-Intervalle (96 Datenpunkte pro Tag)
- **Datenquelle**: SMARD (Strommarktdaten der Bundesnetzagentur)
- **Analysezeiträume**: 
  - Gesamtjahr 2024
  - Sommerquartal (separater Datensatz)
  - Winterquartal (separater Datensatz)

### Algorithmus
- **Typ**: Heuristischer Preisschwellen-Algorithmus
- **Feature**: Lookahead-Funktion mit variablem Horizont
- **Optimierungsziel**: Maximierung der Arbitragegewinne

### Analyseparameter
- **Rolling-Window-Horizonte**: [Xh, Xh]
- **Batteriespeicher-Spezifikationen**: 
  - Kapazität: [X MWh]
  - Lade-/Entladeleistung: [X MW]
  - Wirkungsgrad: [X %]
  - Zyklenlebensdauer: [X Zyklen]

## 📁 Projektstruktur

```
energy-storage-arbitrage-simulator/
│
├── __pycache__/              # Python-Cache-Dateien
├── data/                     # Preisdaten und Datensätze
├── economic_analysis/        # Wirtschaftlichkeitsanalysen
├── logs/                     # Log-Dateien der Simulationen
├── models/                   # Batteriespeicher-Modelle
├── output_plots/             # Generierte Visualisierungen
├── strategies/               # Handelsstrategien-Implementierungen
├── utils/                    # Hilfsfunktionen und Utilities
├── visualization/            # Visualisierungsskripte
│
├── SMARD_15min_Jahr 2024_DE.csv              # SMARD Day-Ahead-Preisdaten 2024
├── SMARD_15min_Jahr 2024_DE_Sommerquartal.csv # Sommerquartal-Daten
├── SMARD_15min_Jahr 2024_DE_Winterquartal.csv # Winterquartal-Daten
│
├── config.py                 # Konfigurationseinstellungen
├── flow_chart_treshold_simple.py             # Flussdiagramm Preisschwellen-Algorithmus
├── grid-search_short.py      # Grid-Search für Parameteroptimierung
├── grid-search_simulation.py # Vollständige Grid-Search-Simulation
├── main.py                   # Hauptausführungsdatei
├── quarterly_comparison_data_from_logs.py    # Quartalsvergleichsanalyse
├── README.md                 # Diese Datei
└── requirements.txt          # Python-Abhängigkeiten
```

## 🚀 Installation & Setup

### Voraussetzungen
- Python 3.8+
- Git

### Installation

# Repository klonen
git clone https://github.com/[username]/bachelorarbeit-batteriespeicher.git
cd bachelorarbeit-batteriespeicher

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Auf Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

### Konfiguration
```
1. Konfigurationsdatei `config.py` anpassen:
   - Batteriespeicher-Parameter
   - Simulationsparameter
   - Datenquellen-Pfade

2. Daten vorbereiten:
   - SMARD-Daten sind bereits im CSV-Format vorhanden
   - Bei Bedarf weitere Quartale hinzufügen
```

## 💻 Verwendung

### Hauptsimulation ausführen

# Hauptsimulation starten
main.ipynb

# Grid-Search für Parameteroptimierung (Kurzversion)
grid-search_short.ipynb

# Vollständige Grid-Search-Simulation
grid-search_simulation.ipynb

# Preisschwellen-Algorithmus-Flussdiagramm
flow_chart_treshold_simple.ipynb

# Quartalsvergleich aus Log-Daten generieren
quarterly_comparison_data_from_logs.ipynb

## 📈 Methodik

### Preisschwellen-Algorithmus

Der implementierte Algorithmus arbeitet nach folgendem Prinzip:

1. **Lookahead-Phase**: Analyse der Preise im definierten Zeitfenster
2. **Schwellenwertberechnung**: Dynamische Ermittlung von Kauf-/Verkaufsschwellen
3. **Entscheidungslogik**: 
   - Laden bei Preisen < untere Schwelle
   - Entladen bei Preisen > obere Schwelle
   - Halten bei Preisen zwischen den Schwellen
4. **Rolling-Window-Update**: Verschiebung des Zeitfensters und Neuberechnung

### Performancemetriken

- **Primär**: Gesamtarbitragegewinn [€]
- **Sekundär**:
  - Anzahl Lade-/Entladezyklen
  - Durchschnittliche Preisdifferenz pro Zyklus
  - Kapazitätsauslastung [%]

## 📊 Vorläufige Ergebnisse

Die Simulation mit den optimierten Parametern (`ROLLING_WINDOW_SIZE = 6`) für das Jahr 2024 ergab:

* **Jahresgewinn (Arbitrage):** 19.733,69 €
* **Anzahl Zyklen:** 286,5
* **NPV (15 Jahre @ 5%):** -22.152,03 €

## 🔧 Technologie-Stack

- **Programmiersprache**: Python 3.8+
- **Datenverarbeitung**: pandas, numpy
- **Visualisierung**: matplotlib, seaborn, plotly
- **Optimierung**: scipy, optuna
- **Dokumentation**: siehe documentation.pdf

## 👤 Autor

- **Name**: Till Jonas Wellkamp
- **Universität**: HTWK
- **Studiengang**: Bachelorstudiengang Energie-, Gebäude- und Umwelttechnik
- **Betreuer**: Prof. Dr. Jens Schneider
- **Betreuerin**: B. Eng. Anna Hofmann

*Letzte Aktualisierung: [09.08.2025]*
