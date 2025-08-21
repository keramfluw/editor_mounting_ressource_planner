import streamlit as st

st.set_page_config(page_title="Zähler-Editor – Zeiten & Preise", layout="wide")
st.title("Zähler-Montage: Zeiten & Preise (Standalone)")

try:
    import zaehler_editor as ze
except Exception as e:
    st.error("Konnte das Modul 'zaehler_editor' nicht importieren. "
             "Stellen Sie sicher, dass 'zaehler_editor.py' im Repo liegt "
             "und die Funktionen 'init_zaehler_state' & 'render_zaehler_editor' bereitstellt.")
    st.exception(e)
    st.stop()

ze.init_zaehler_state()
montage_daten = ze.render_zaehler_editor(title="Zähler-Montage: Zeiten & Preise")

st.markdown("---")
st.subheader("Vorschau der aktuellen Tabelle")
import pandas as pd
df = pd.DataFrame([(k, v[0], v[1]) for k, v in montage_daten.items()],
                  columns=["Gerät", "Montageaufwand (h)", "Vergütung (€)"])
st.dataframe(df, use_container_width=True)
