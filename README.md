# Zähler-Editor – Standalone Wrapper

Diese App macht Ihr Modul `zaehler_editor.py` als vollständige Streamlit-App lauffähig.

## Streamlit Cloud
1. `main.py` ins Repo-Root legen.
2. `zaehler_editor.py` liegt ebenfalls im Repo-Root (mit `init_zaehler_state`, `render_zaehler_editor`).
3. In den App-Einstellungen **Main file** auf `main.py` setzen.
4. Python 3.11 verwenden (empfohlen) und `requirements.txt` passend pinnen.

## Lokal
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run main.py
```
