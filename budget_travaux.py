# budget_travaux.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import date

# --- CONFIG / INIT -----------------------------------------------------------
DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "depenses.csv"

DEFAULT_BUDGET = 68000  # ajuste si besoin
POSTES = [
    "Maçonnerie", "Menuiserie", "Cuisine", "Salle de bain",
    "Électricité", "Plomberie", "Chauffage", "Isolation",
    "Matériaux", "Peinture", "Divers"
]

DATA_DIR.mkdir(exist_ok=True)

def load_data() -> pd.DataFrame:
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    return pd.DataFrame(columns=["poste", "fournisseur", "description", "montant", "date"])

def save_data(df: pd.DataFrame):
    df.to_csv(CSV_PATH, index=False)

# --- SIDEBAR / PARAMS --------------------------------------------------------
st.set_page_config(page_title="Budget travaux", page_icon="🛠️", layout="wide")
st.title("🛠️ Suivi de budget travaux")

budget_global = st.sidebar.number_input("Budget global (€)", value=DEFAULT_BUDGET, step=500, min_value=0)
postes_visibles = st.sidebar.multiselect("Postes visibles", options=POSTES, default=POSTES)
st.sidebar.caption("💾 Les données sont sauvegardées dans `data/depenses.csv`.")

df = load_data()

# --- FORM: AJOUT DÉPENSE -----------------------------------------------------
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
        new_row = {"poste": poste, "fournisseur": fournisseur, "description": description, "montant": float(montant), "date": d}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("✅ Dépense ajoutée.")

# --- METRICS -----------------------------------------------------------------
total_depenses = df["montant"].sum() if not df.empty else 0.0
reste = budget_global - total_depenses
colA, colB, colC = st.columns(3)
colA.metric("Budget global", f"{budget_global:,.0f} €".replace(",", " "))
colB.metric("Total dépensé", f"{total_depenses:,.0f} €".replace(",", " "))
colC.metric("Reste à dépenser", f"{reste:,.0f} €".replace(",", " "), delta=None)

st.divider()

# --- GRAPHIQUE PAR POSTE -----------------------------------------------------
st.subheader("📊 Répartition des dépenses par poste")
df_visu = df[df["poste"].isin(postes_visibles)] if not df.empty else df

if not df_visu.empty:
    agg = df_visu.groupby("poste")["montant"].sum().reindex(POSTES, fill_value=0)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(agg.index, agg.values, color="#3b82f6")
    ax.set_ylabel("Montant (€)")
    ax.set_xticklabels(agg.index, rotation=45, ha="right", fontsize=9)
    plt.tight_layout()  # 👈 évite le chevauchement
    st.pyplot(fig, use_container_width=False)
else:
    st.info("Aucune dépense enregistrée pour l’instant.")

# --- TABLE -------------------------------------------------------------------
st.subheader("📄 Liste des dépenses")
if not df.empty:
    st.dataframe(
        df.sort_values(by="date", ascending=False),
        use_container_width=True,
        height=320
    )
else:
    st.caption("La table s’affichera après l’ajout de vos premières dépenses.")

# --- EXPORT ------------------------------------------------------------------
st.download_button(
    "⬇️ Télécharger en CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="depenses.csv",
    mime="text/csv",
    use_container_width=True
)
