# --- IMPORTS -------------------------------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import date
from google.oauth2.service_account import Credentials
import gspread

# 👉 Doit être le 1er appel Streamlit :
st.set_page_config(page_title="Budget travaux", page_icon="🛠️", layout="wide")

# --- DIAGNOSTIC GOOGLE SHEETS -------------------------------
with st.sidebar.expander("🔍 Diagnostic Google Sheets", expanded=False):
    try:
        has_secrets = "gcp_service_account" in st.secrets and "SHEETS" in st.secrets
        st.write("Secrets chargés :", has_secrets)
        if has_secrets:
            sheet_id = st.secrets["SHEETS"].get("SHEET_ID", "(manquant)")
            sheet_name = st.secrets["SHEETS"].get("SHEET_NAME", "Feuille 1")
            st.write("Sheet ID :", sheet_id)
            st.write("Sheet name :", sheet_name)

            info = st.secrets["gcp_service_account"]
            creds = Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)
            st.success("✅ Authentification Google réussie")

            sh = client.open_by_key(sheet_id)
            ws = sh.worksheet(sheet_name)
            st.success(f"✅ Onglet trouvé : {ws.title}")

            if st.button("🧪 Écrire une ligne de test"):
                ws.append_row(["TEST", "Streamlit", "Connexion OK", 1.23, str(date.today())])
                st.success("✅ Ligne test écrite dans Google Sheets !")
        else:
            st.warning("Les secrets ne sont pas correctement configurés.")
    except Exception as e:
        st.error(f"❌ Erreur : {e}")
# ------------------------------------------------------------

# --- CONFIG / INIT ------------------------------------------
DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "depenses.csv"
DEFAULT_BUDGET = 68000
POSTES = ["Maçonnerie","Menuiserie","Cuisine","Salle de bain","Électricité","Plomberie","Chauffage","Isolation","Matériaux","Peinture","Divers"]
DATA_DIR.mkdir(exist_ok=True)
