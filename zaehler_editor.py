import streamlit as st
import pandas as pd
from pathlib import Path

_ASSETS_PATH_DEFAULT = "assets/zaehler_parameter.csv"
_SS_KEY_DF = "zaehler_df"
_SS_KEY_DIRTY = "zaehler_dirty"

_DEFAULTS = [
    ("UP-MK Zähler", 0.33, 12.00),
    ("Aufputzzähler, Zapfhahnzähler + Zählwerkkopf", 0.33, 15.00),
    ("Hauswasserzähler (bis Q3=16)", 0.50, 20.00),
    ("Funkmodule WZ", 0.17, 5.00),
    ("Funkmodule WMZ", 0.17, 5.00),
    ("Split WMZ bis QN 10,0 m³/h", 0.75, 75.00),
    ("Split WMZ QN 15,0 - QN 40,0 m³/h", 0.92, 120.00),
    ("Split WMZ größer QN 40,0 m³/h", 1.01, 170.00),
    ("MK- und Verschraubungszähler bis QN 2,5m³/h", 0.50, 30.00),
]

def _default_df() -> pd.DataFrame:
    return pd.DataFrame(_DEFAULTS, columns=["Geraet", "Montageaufwand_h", "Preis_EUR"])

def init_zaehler_state(assets_csv: str = _ASSETS_PATH_DEFAULT):
    """Initialize editable Zähler table in session_state from CSV or defaults."""
    if _SS_KEY_DF in st.session_state:
        return
    path = Path(assets_csv)
    if path.exists():
        try:
            df = pd.read_csv(path)
            expected = {"Geraet", "Montageaufwand_h", "Preis_EUR"}
            if not expected.issubset(df.columns):
                raise ValueError("CSV fehlt benötigte Spalten")
        except Exception:
            df = _default_df()
    else:
        df = _default_df()
    # Basic sanitation
    df["Geraet"] = df["Geraet"].astype(str)
    df["Montageaufwand_h"] = pd.to_numeric(df["Montageaufwand_h"], errors="coerce").fillna(0.0).clip(lower=0.0)
    df["Preis_EUR"] = pd.to_numeric(df["Preis_EUR"], errors="coerce").fillna(0.0).clip(lower=0.0)
    st.session_state[_SS_KEY_DF] = df
    st.session_state[_SS_KEY_DIRTY] = False

def _save_to_assets(df: pd.DataFrame, assets_csv: str):
    path = Path(assets_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)

def get_montage_dict() -> dict:
    """Return the current dict mapping device -> (hours, price)."""
    df = st.session_state.get(_SS_KEY_DF, _default_df())
    return {row["Geraet"]: (float(row["Montageaufwand_h"]), float(row["Preis_EUR"])) for _, row in df.iterrows()}

def render_zaehler_editor(title: str = "Zähler-Montage: Zeiten & Preise", assets_csv: str = _ASSETS_PATH_DEFAULT) -> dict:
    """Render the editable table and return the montage dict."""
    init_zaehler_state(assets_csv=assets_csv)

    st.subheader(title)

    with st.expander("CSV importieren / exportieren", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "Aktuelle Tabelle als CSV downloaden",
                data=st.session_state[_SS_KEY_DF].to_csv(index=False).encode("utf-8"),
                file_name="zaehler_parameter.csv",
                mime="text/csv",
            )
        with c2:
            uploaded = st.file_uploader("CSV importieren (Spalten: Geraet, Montageaufwand_h, Preis_EUR)", type=["csv"], accept_multiple_files=False)
            if uploaded is not None:
                try:
                    new_df = pd.read_csv(uploaded)
                    expected = {"Geraet", "Montageaufwand_h", "Preis_EUR"}
                    if not expected.issubset(new_df.columns):
                        st.error("CSV muss die Spalten Geraet, Montageaufwand_h, Preis_EUR enthalten.")
                    else:
                        # basic sanitation
                        new_df["Geraet"] = new_df["Geraet"].astype(str)
                        new_df["Montageaufwand_h"] = pd.to_numeric(new_df["Montageaufwand_h"], errors="coerce").fillna(0.0).clip(lower=0.0)
                        new_df["Preis_EUR"] = pd.to_numeric(new_df["Preis_EUR"], errors="coerce").fillna(0.0).clip(lower=0.0)
                        st.session_state[_SS_KEY_DF] = new_df
                        st.session_state[_SS_KEY_DIRTY] = True
                        st.success("CSV importiert.")
                except Exception as e:
                    st.error(f"CSV konnte nicht gelesen werden: {e}")
        with c3:
            if st.button("Auf Standardwerte zurücksetzen", type="secondary"):
                st.session_state[_SS_KEY_DF] = _default_df()
                st.session_state[_SS_KEY_DIRTY] = True
                st.info("Standardwerte geladen.")

    # Unique key enforcement hint
    if st.session_state[_SS_KEY_DF]["Geraet"].duplicated().any():
        st.warning("Warnung: Es gibt doppelte Namen in 'Geraet'. Bitte eindeutige Bezeichnungen verwenden.")

    edited_df = st.data_editor(
        st.session_state[_SS_KEY_DF],
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Geraet": st.column_config.TextColumn("Gerät", help="Bezeichnung des Zählers / Geräts"),
            "Montageaufwand_h": st.column_config.NumberColumn(
                "Montageaufwand [h]", min_value=0.0, step=0.05, format="%.2f",
                help="Zeitbedarf in Stunden für die Montage"
            ),
            "Preis_EUR": st.column_config.NumberColumn(
                "Montagepreis [€]", min_value=0.0, step=1.0, format="%.2f",
                help="Vergütung pro Montage (netto oder brutto je nach Modell)"
            ),
        },
        key="zaehler_table_editor",
    )

    # Detect changes
    if not edited_df.equals(st.session_state[_SS_KEY_DF]):
        st.session_state[_SS_KEY_DF] = edited_df.copy()
        st.session_state[_SS_KEY_DIRTY] = True

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Änderungen übernehmen & speichern", type="primary"):
            _save_to_assets(st.session_state[_SS_KEY_DF], assets_csv)
            st.session_state[_SS_KEY_DIRTY] = False
            st.success(f"Gespeichert nach: {assets_csv}")
    with colB:
        st.caption("Tipp: Nutzen Sie CSV-Export/Import für Bulk-Änderungen.")

    return get_montage_dict()
