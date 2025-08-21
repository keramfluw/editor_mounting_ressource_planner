
import os
from io import BytesIO
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Installations-Wirtschaftlichkeit", layout="wide")

# ---------- Helpers ----------
BASE_DIR = os.path.dirname(__file__)
CATALOG_CSV = os.path.join(BASE_DIR, "assets", "data", "catalog.csv")
PROJECTS_CSV = os.path.join(BASE_DIR, "assets", "data", "projects.csv")

@st.cache_data
def load_catalog():
    df = pd.read_csv(CATALOG_CSV)
    # enforce columns
    needed = ["Kategorie","Gerät","Std_pro_Einheit","Preis_EUR","Anzahl"]
    for n in needed:
        if n not in df.columns:
            raise ValueError(f"Spalte {n} fehlt in catalog.csv")
    # types
    df["Std_pro_Einheit"] = pd.to_numeric(df["Std_pro_Einheit"], errors="coerce").fillna(0.0)
    df["Preis_EUR"] = pd.to_numeric(df["Preis_EUR"], errors="coerce").fillna(0.0)
    df["Anzahl"] = pd.to_numeric(df["Anzahl"], errors="coerce").fillna(0).astype(int)
    return df

@st.cache_data
def load_projects():
    df = pd.read_csv(PROJECTS_CSV)
    for col in ["Wasserzähler","WMZ","KMZ","HKV"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        else:
            df[col] = 0
    if "Bemerkungen" not in df.columns:
        df["Bemerkungen"] = ""
    return df

def prefill_from_project(cat_df: pd.DataFrame, project: dict) -> pd.DataFrame:
    """Prefill quantities by putting category totals on the first item of each category.
    This is a starting point; the user can then re-allocate counts."""
    df = cat_df.copy()
    df["Anzahl"] = 0

    # map project columns to categories
    mapping = {
        "Wasserzähler": "Wasserzähler",
        "WMZ": "Wärme-/Kältezähler",
        "KMZ": "Wärme-/Kältezähler",  # interpret as (weitere) WMZ/CMZ
        "HKV": "HKVE",
    }
    for proj_col, category in mapping.items():
        if proj_col not in project:
            continue
        total = int(project[proj_col] or 0)
        if total <= 0:
            continue
        idx = df.index[df["Kategorie"] == category]
        if len(idx) == 0:
            continue
        # put everything on the first row of that category as default
        first_idx = idx[0]
        df.loc[first_idx, "Anzahl"] += total
    return df

def compute_kalkulation(df_positions: pd.DataFrame, stundenlohn: float):
    df = df_positions.copy()
    df["Erlös"] = df["Preis_EUR"] * df["Anzahl"]
    df["Arbeitsstunden"] = df["Std_pro_Einheit"] * df["Anzahl"]
    df["Lohnkosten"] = df["Arbeitsstunden"] * stundenlohn
    df["DB_Pos"] = df["Erlös"] - df["Lohnkosten"]
    totals = {
        "Erlös": float(df["Erlös"].sum()),
        "Arbeitsstunden": float(df["Arbeitsstunden"].sum()),
        "Lohnkosten": float(df["Lohnkosten"].sum()),
        "DB_Pos": float(df["DB_Pos"].sum()),
        "Anzahl": int(df["Anzahl"].sum()),
    }
    return df, totals

def style_money(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def to_excel(df_positions, summary):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_positions.to_excel(writer, sheet_name="Positionen", index=False)
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Zusammenfassung", index=False)
    out.seek(0)
    return out

# ---------- Data ----------
catalog = load_catalog()
projects = load_projects()

# ---------- Sidebar: Global inputs ----------
st.sidebar.header("Globale Parameter")
mitarbeiter = st.sidebar.number_input("Mitarbeiteranzahl", min_value=1, value=2, step=1)
stunden_pro_tag = st.sidebar.number_input("Stunden pro Tag", min_value=1.0, value=8.0, step=0.5)
stundenlohn = st.sidebar.number_input("Stundenlohn (€/h)", min_value=0.0, value=28.0, step=0.5)
fahrpauschale = st.sidebar.number_input("Fahrtkostenpauschale (€/km)", min_value=0.0, value=0.30, step=0.01, format="%.2f")
gesamt_km = st.sidebar.number_input("Gesamt-Kilometer (ein Projekt)", min_value=0.0, value=0.0, step=1.0)
mehr_aufsatz = st.sidebar.number_input("Sonder-/Wartezeit-Satz (€/h)", min_value=0.0, value=45.0, step=1.0)
mehr_std = st.sidebar.number_input("Sonder-/Wartezeit-Stunden", min_value=0.0, value=0.0, step=0.5)

st.sidebar.caption("Alle Werte sind live-editierbar und fließen in die Kalkulation ein.")

# ---------- Project selection ----------

# ---------- Tabs ----------
tab_calc, tab_cluster = st.tabs(["Kalkulation", "Stadt-Cluster"])

with tab_calc:
    # ---------- Project selection ----------
    st.header("Projekt & Adresse")
    col1, col2 = st.columns([2, 3])
    with col1:
        proj_options = ["— Manuell —"] + [f"{row['Stadt']} – {row['Objekt']}" for _, row in projects.iterrows()]
        choice = st.selectbox("Projekt laden", proj_options, index=0)
    with col2:
        if choice != "— Manuell —":
            row = projects.iloc[proj_options.index(choice)-1].to_dict()
            st.info(f"Ausgewählt: **{row['Stadt']} – {row['Objekt']}**  |  Hinweis: {row.get('Bemerkungen','')}")
            positions_df_default = prefill_from_project(catalog, row)
        else:
            row = {"Stadt":"", "Objekt":"", "Bemerkungen":""}
            positions_df_default = catalog.copy()

    addr_cols = st.columns(3)
    stadt = addr_cols[0].text_input("Stadt", value=row.get("Stadt",""))
    objekt = addr_cols[1].text_input("Objekt/Adresse", value=row.get("Objekt",""))
    bem = addr_cols[2].text_input("Bemerkungen", value=row.get("Bemerkungen",""))

    st.markdown("---")

    # ---------- Positions editor ----------
    st.subheader("Positionen")
    editor_config = {
        "Anzahl": st.column_config.NumberColumn("Anzahl", min_value=0, step=1),
        "Preis_EUR": st.column_config.NumberColumn("Preis (€/Einheit)", min_value=0.0, step=0.5, format="%.2f"),
        "Std_pro_Einheit": st.column_config.NumberColumn("Std/Einheit", min_value=0.0, step=0.05, format="%.2f"),
    }
    view_cols = ["Kategorie","Gerät","Std_pro_Einheit","Preis_EUR","Anzahl"]

    edited = st.data_editor(
        positions_df_default[view_cols],
        column_config=editor_config,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True
    )

    # ---------- Compute economics ----------
    calc_df, totals = compute_kalkulation(edited, stundenlohn)

    fahrkosten = gesamt_km * fahrpauschale
    sonderkosten = mehr_std * mehr_aufsatz

    gesamtstunden = totals["Arbeitsstunden"]
    arbeitstage = gesamtstunden / (mitarbeiter * max(stunden_pro_tag, 0.0001))

    gesamterlös = totals["Erlös"]
    lohnkosten = totals["Lohnkosten"]
    gesamtkosten = lohnkosten + fahrkosten + sonderkosten
    db_gesamt = gesamterlös - gesamtkosten
    marge = (db_gesamt / gesamterlös * 100) if gesamterlös > 0 else 0.0

    # ---------- KPIs ----------
    st.subheader("Kennzahlen")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Gesamterlös", style_money(gesamterlös))
    k2.metric("Arbeitsstunden (gesamt)", f"{gesamtstunden:,.2f} h".replace(".", ","))
    k3.metric("Lohnkosten", style_money(lohnkosten))
    k4.metric("Fahrt- & Sonderkosten", style_money(fahrkosten + sonderkosten))
    k5.metric("Deckungsbeitrag (gesamt)", style_money(db_gesamt))

    k6, k7 = st.columns(2)
    k6.metric("Kalk. Arbeitstage", f"{arbeitstage:,.2f} d".replace(".", ","), help="Berechnet als Gesamtstunden / (Mitarbeiter × Stunden/Tag)")
    k7.metric("Marge", f"{marge:,.1f} %")

    # ---------- Detailed table ----------
    st.subheader("Detailkalkulation je Position")
    show_cols = ["Kategorie","Gerät","Anzahl","Std_pro_Einheit","Arbeitsstunden","Preis_EUR","Erlös","Lohnkosten","DB_Pos"]
    st.dataframe(calc_df[show_cols], use_container_width=True, hide_index=True)

    # ---------- Downloads ----------
    st.subheader("Export")
    excel_file = to_excel(calc_df[show_cols], {
        "Stadt": stadt, "Objekt": objekt, "Bemerkungen": bem,
        "Mitarbeiter": mitarbeiter, "Stunden/Tag": stunden_pro_tag, "Stundenlohn": stundenlohn,
        "Fahrkosten (€/km)": fahrpauschale, "Gesamt-km": gesamt_km,
        "Sonder-Satz": mehr_aufsatz, "Sonder-Stunden": mehr_std,
        "Gesamterlös": gesamterlös, "Gesamtstunden": gesamtstunden, "Lohnkosten": lohnkosten,
        "Fahrt/Sonder": fahrkosten + sonderkosten, "Deckungsbeitrag": db_gesamt, "Marge %": marge,
        "Arbeitstage": arbeitstage
    })
    st.download_button("Excel herunterladen", data=excel_file, file_name="kalkulation.xlsx")

    st.caption("Tipp: In **assets/data/catalog.csv** und **assets/data/projects.csv** können Sie Stammdaten pflegen. Änderungen werden beim Neuladen berücksichtigt.")

with tab_cluster:
    st.header("Stadt-Cluster (unsupervised)")
    st.write("Gruppiert Städte nach Mengen (Wasserzähler, WMZ, KMZ, HKV). Wählen Sie Features und Clusteranzahl.")

    # Aggregation nach Stadt
    agg_cols = ["Wasserzähler","WMZ","KMZ","HKV"]
    agg_city = projects.groupby("Stadt")[agg_cols].sum().reset_index()

    # Auswahl der Features
    default_features = [c for c in agg_cols if agg_city[c].sum() > 0]
    if not default_features:
        default_features = agg_cols
    features = st.multiselect("Features für das Clustering", agg_cols, default=default_features)

    k = st.slider("Anzahl Cluster (k)", min_value=2, max_value=8, value=3, step=1)

    if features:
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA
        import matplotlib.pyplot as plt

        X = agg_city[features].astype(float).values
        X_scaled = StandardScaler().fit_transform(X)
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)

        agg_city["Cluster"] = labels

        st.subheader("Cluster-Zuordnung je Stadt")
        st.dataframe(agg_city, use_container_width=True, hide_index=True)

        # Download CSV
        csv_bytes = agg_city.to_csv(index=False).encode("utf-8")
        st.download_button("Cluster-Ergebnis als CSV", data=csv_bytes, file_name="city_clusters.csv")

        # 2D-Projektion via PCA
        pca = PCA(n_components=2, random_state=42)
        pts = pca.fit_transform(X_scaled)

        fig = plt.figure()
        for i, (x, y) in enumerate(pts):
            plt.scatter(x, y, c=[labels[i]])
            plt.text(x, y, agg_city.loc[i, "Stadt"])
        plt.xlabel("PCA 1")
        plt.ylabel("PCA 2")
        plt.title("Stadt-Cluster – PCA-Projektion")
        st.pyplot(fig, clear_figure=True)
    else:
        st.info("Bitte mindestens ein Feature auswählen.")
