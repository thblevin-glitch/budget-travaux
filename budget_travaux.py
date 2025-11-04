# --- IMPORTS -------------------------------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from pathlib import Path
from datetime import date
from google.oauth2.service_account import Credentials
import gspread

# 👉 Doit être le 1er appel Streamlit :
st.set_page_config(page_title="Budget travaux", page_icon="🛠️", layout="wide")


# --- CONFIG / INIT ------------------------------------------
DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "depenses.csv"   # conservé si jamais tu veux un backup local
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_BUDGET = 68840
POSTES = [
    "Maçonnerie", "Menuiserie", "Cuisine", "Salle de bain", "Électricité",
    "Plomberie", "Chauffage", "Isolation", "Matériaux", "Peinture", "Divers"
]

# 🎨 Palette de couleurs par poste (tu peux ajuster)
COULEURS_POSTE = {
    "Maçonnerie":   "#b91c1c",  # rouge brique
    "Menuiserie":   "#92400e",  # brun bois
    "Cuisine":      "#d97706",  # orange doré
    "Salle de bain":"#2563eb",  # bleu eau
    "Électricité":  "#facc15",  # jaune vif
    "Plomberie":    "#06b6d4",  # turquoise
    "Chauffage":    "#dc2626",  # rouge chaud
    "Isolation":    "#16a34a",  # vert
    "Matériaux":    "#6b7280",  # gris
    "Peinture":     "#a855f7",  # violet
    "Divers":       "#f97316",  # orange
}


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


# --- GOOGLE SHEETS HELPERS ---------------------------------------------------
def _gs_client():
    info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def _gs_ws():
    """Retourne l'onglet Google Sheets (le crée avec l'entête si besoin)."""
    client = _gs_client()
    sheet_id = st.secrets["SHEETS"]["SHEET_ID"]
    sheet_name = st.secrets["SHEETS"]["SHEET_NAME"]
    sh = client.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=10)
        ws.update('A1:E1', [["poste","fournisseur","description","montant","date"]])
    return ws

def load_data() -> pd.DataFrame:
    try:
        ws = _gs_ws()
        rows = ws.get_all_records()
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["poste","fournisseur","description","montant","date"])
        if "montant" in df.columns:
            df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        return df
    except Exception as e:
        st.sidebar.error(f"❌ Erreur lecture Google Sheets : {e}")
        return pd.DataFrame(columns=["poste","fournisseur","description","montant","date"])

def save_data(df: pd.DataFrame):
    """Réécrit l'entier du DataFrame dans la feuille."""
    try:
        ws = _gs_ws()
        ws.clear()
        ws.update('A1:E1', [["poste","fournisseur","description","montant","date"]])
        out = df.copy()
        out["montant"] = pd.to_numeric(out["montant"], errors="coerce").fillna(0.0)
        out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        if len(out):
            ws.append_rows(out[["poste","fournisseur","description","montant","date"]].values.tolist())
        st.sidebar.success("✅ Données synchronisées avec Google Sheets")
    except Exception as e:
        st.sidebar.error(f"❌ Erreur écriture Google Sheets : {e}")


# === CORPS DE L'APP ==========================================================
st.title("🛠️ Suivi de budget travaux")

# Sidebar : budget + postes + note
budget_global = st.sidebar.number_input("Budget global (€)", value=DEFAULT_BUDGET, step=500, min_value=0)
postes_visibles = st.sidebar.multiselect("Postes visibles", options=POSTES, default=POSTES)
st.sidebar.caption("💾 Données sauvegardées dans Google Sheets (partagées).")

# Chargement des données avec garde-fous
try:
    df = load_data()
except Exception as e:
    st.error(f"❌ Erreur lors du chargement des données : {e}")
    df = pd.DataFrame(columns=["poste","fournisseur","description","montant","date"])


# === FORMULAIRE : AJOUT DÉPENSE =============================================
st.subheader("➕ Ajouter une dépense")
with st.form("form_depense", clear_on_submit=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        poste = st.selectbox("Poste", options=POSTES)
        fournisseur = st.text_input("Fournisseur", placeholder="Ex: Leroy Merlin")
        montant = st.number_input("Montant (€)", min_value=0.0, step=10.0, format="%.2f")
    with col2:
        description = st.text_input("Description", placeholder="Ex: Carrelage salle de bain")
        d = st.date_input("Date", value=date.today())
    submitted = st.form_submit_button("Ajouter")

if submitted:
    new_row = {
        "poste": poste,
        "fournisseur": fournisseur,
        "description": description,
        "montant": float(montant),
        "date": d,   # save_data s'occupe du formatage
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    try:
        save_data(df)
        st.success("✅ Dépense ajoutée et enregistrée.")
    except Exception as e:
        st.error(f"❌ Erreur lors de l’enregistrement : {e}")


# === METRICS =================================================================
total_depenses = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0).sum() if not df.empty else 0.0
reste = budget_global - total_depenses
colA, colB, colC = st.columns(3)
fmt = lambda n: f"{n:,.2f} €".replace(",", " ").replace(".", ",")
colA.metric("Budget global", fmt(budget_global))
colB.metric("Total dépensé", fmt(total_depenses))
colC.metric("Reste à dépenser", fmt(reste))
st.divider()


# === GRAPHIQUE PAR POSTE =====================================================
st.subheader("📊 Répartition des dépenses par poste")

if not df.empty and "poste" in df.columns and "montant" in df.columns:
    df_visu = df[df["poste"].isin(postes_visibles)]
    agg = (
        df_visu.groupby("poste", dropna=False)["montant"]
        .sum()
        .reindex(POSTES, fill_value=0)
    )

    fig, ax = plt.subplots(figsize=(6, 4))

    # 🎨 Couleurs par poste (sans légende)
    colors = [COULEURS_POSTE.get(poste, "#9ca3af") for poste in agg.index]
    ax.bar(agg.index, agg.values, color=colors)

    # ✅ Format € sans notation scientifique
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, p: f"{x:,.0f} €".replace(",", " ").replace(".", ","))
    )

    ax.set_ylabel("Montant (€)")
    ax.set_xticklabels(agg.index, rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=False)
else:
    st.info("Aucune dépense enregistrée pour l’instant.")


# === TABLE ÉDITABLE (compacte) ===============================================
st.subheader("📄 Liste des dépenses (modifiable)")

if not df.empty:
    # Trie les données récentes en premier
    df_sorted = df.sort_values(by="date", ascending=False).reset_index(drop=True)

    # ✅ Tableau interactif éditable, sans index et plus compact
    edited_df = st.data_editor(
        df_sorted,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,           # 👈 enlève les numéros à gauche
        height=280,                # 👈 réduit la hauteur visible du tableau
        key="depenses_editor",
        column_config={
            "poste": st.column_config.TextColumn("Poste"),
            "fournisseur": st.column_config.TextColumn("Fournisseur"),
            "description": st.column_config.TextColumn("Description"),
            "montant": st.column_config.NumberColumn("Montant (€)", help="Montant en euros", step=1, format="%.2f"),
            "date": st.column_config.DateColumn("Date"),
        }
    )

    # 🔄 Détection de modifications
    if not edited_df.equals(df_sorted):
        st.info("💾 Modifications détectées. Cliquez pour enregistrer.")
        if st.button("✅ Enregistrer les changements dans Google Sheets"):
            try:
                edited_df["montant"] = pd.to_numeric(edited_df["montant"], errors="coerce").fillna(0.0)
                edited_df["date"] = pd.to_datetime(edited_df["date"], errors="coerce").dt.date
                save_data(edited_df)
                st.success("✅ Données mises à jour dans Google Sheets !")
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde : {e}")
else:
    st.caption("La table s’affichera après l’ajout de vos premières dépenses.")



# === EXPORT ==================================================================
st.download_button(
    "⬇️ Télécharger en CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="depenses.csv",
    mime="text/csv",
    use_container_width=True
)
# ============================================================================
