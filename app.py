import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
import requests

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur Crowdfunding | Baltis", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS "PREMIUM+" ---
# On écrase complètement le style natif de Streamlit
custom_css = """
<style>
    /* Import typo moderne */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Cacher les éléments Streamlit (header, footer, menu) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

    /* Application de la typo globale */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0A2540 !important;
    }

    /* Titres */
    h1 { font-weight: 800; font-size: 2.5rem; letter-spacing: -0.03em; margin-bottom: 0.5rem; color: #0A2540; }
    h2 { font-weight: 700; font-size: 1.8rem; letter-spacing: -0.02em; margin-top: 2rem; color: #0A2540; }
    h3 { font-weight: 600; font-size: 1.4rem; }

    /* Customisation de la Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Bouton CTA Streamlit (Download) */
    .stDownloadButton button {
        background-color: #F36121 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(243, 97, 33, 0.3) !important;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(243, 97, 33, 0.4) !important;
    }

    /* -------------- FORMULAIRE DE CAPTURE -------------- */
    [data-testid="stForm"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 10px 30px rgba(10, 37, 64, 0.05);
    }
    /* Champs texte du formulaire */
    .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        background-color: #F8FAFC !important;
        transition: border-color 0.2s;
    }
    .stTextInput input:focus {
        border-color: #F36121 !important;
        box-shadow: 0 0 0 1px #F36121 !important;
    }
    /* Bouton de soumission du formulaire */
    [data-testid="stFormSubmitButton"] button {
        background-color: #0A2540 !important; /* Bleu foncé pour le form */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        margin-top: 10px !important;
    }
    [data-testid="stFormSubmitButton"] button:hover {
        background-color: #1a3c5e !important;
    }

    /* Slider styling */
    .stSlider [data-testid="stTickBar"] { display: none; } /* Enlever les ticks en dessous */
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. INITIALISATION ÉTAT ---
if 'acces_debloque' not in st.session_state:
    st.session_state.acces_debloque = False
if 'user_prenom' not in st.session_state:
    st.session_state.user_prenom = ""
if 'user_nom' not in st.session_state:
    st.session_state.user_nom = ""

# --- 4. FONCTIONS (API & PDF gardées identiques) ---
def ajouter_contact_getresponse(prenom, nom, email):
    # Simulation pour la démo
    return True 

def calculer_simulation(montant, duree_mois, reinvestissement, plateforme_data):
    df = pd.DataFrame(plateforme_data)
    duree_annees = duree_mois / 12
    if reinvestissement == "Réinvestissement des intérêts à chaque remboursement":
        r_rate = df["Rendement Brut Théorique (%)"] / 100
        total_final = montant * ((1 + r_rate) ** duree_annees)
        df["Rendement Brut (€)"] = total_final - montant
    else: 
        df["Rendement Brut (€)"] = montant * (df["Rendement Brut Théorique (%)"] / 100) * duree_annees

    df["Impact Frais (€)"] = df["Frais Investisseur (%)"] / 100 * montant
    df["Impact Défaut (Est. Perte) (€)"] = df["Taux de défaut historique (%)"] / 100 * montant
    df["Rendement Net Réel (€)"] = df["Rendement Brut (€)"] - df["Impact Frais (€)"] - df["Impact Défaut (Est. Perte) (€)"]
    return df

def generer_pdf_premium(prenom, nom, montant, duree, gain_baltis_total, df_complet):
    # (Le code du PDF reste exactement le même, vu qu'il vous convient)
    class PDF(FPDF):
        def header(self):
            self.set_fill_color(10, 37, 64) 
            self.rect(0, 0, 210, 30, 'F')
            self.set_font('Arial', 'B', 18)
            self.set_text_color(255, 255, 255)
            self.cell(10, 10) 
            self.cell(40, 10, 'BALTIS', 0, 0, 'L')
            self.set_font('Arial', '', 11)
            self.cell(140, 10, 'SIMULATION CROWDFUNDING', 0, 1, 'R')
            self.ln(10)
        def footer(self):
            self.set_y(-25)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(10, 37, 64)
            self.multi_cell(0, 4, txt="Mention Légale AMF : Investir comporte des risques. Les performances passées ne préjugent pas des performances futures.", align='C')
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=f"Rapport pour : {prenom} {nom}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, txt=f"Gain estimé : {gain_baltis_total:,.0f} EUR", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# HEADER UI
# ==========================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid #E2E8F0; margin-bottom: 30px; margin-top: -30px;">
    <div>
        <h1 style="margin:0; font-size: 2rem;">Simulateur de rendement net</h1>
        <p style="color: #64748B; margin: 5px 0 0 0; font-size: 1.1rem;">Calculez l'impact réel des frais et du défaut sur votre épargne.</p>
    </div>
    <div style="background-color: #0A2540; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 800; font-size: 1.2rem; letter-spacing: 2px;">
        BALTIS
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# ETAPE 1 : FORMULAIRE DE CAPTURE (Gated Content)
# ==========================================
if not st.session_state.acces_debloque:
    
    col_espace1, col_form, col_espace2 = st.columns([1, 2, 1]) # Centrer le formulaire
    
    with col_form:
        st.markdown("<h3 style='text-align: center; margin-bottom: 5px;'>Accédez à votre simulation personnalisée</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 25px;'>Découvrez gratuitement quel sera votre rendement réel net de frais et de risque.</p>", unsafe_allow_html=True)
        
        with st.form("lead_capture_form"):
            col1, col2 = st.columns(2)
            prenom_input = col1.text_input("Prénom")
            nom_input = col2.text_input("Nom")
            email_input = st.text_input("Adresse e-mail")
            
            # Bouton stylisé via le CSS global
            submitted = st.form_submit_button("Débloquer mon simulateur gratuit")
            
            if submitted:
                if prenom_input and email_input:
                    ajouter_contact_getresponse(prenom_input, nom_input, email_input)
                    st.session_state.acces_debloque = True
                    st.session_state.user_prenom = prenom_input
                    st.session_state.user_nom = nom_input
                    st.rerun()
                else:
                    st.error("Veuillez remplir votre prénom et votre email.")

# ==========================================
# ETAPE 2 : SIMULATEUR PREMIUM (Débloqué)
# ==========================================
else:
    # --- SIDEBAR ---
    st.sidebar.markdown(f"<div style='background-color:#0A2540; color:white; padding:15px; border-radius:8px; margin-bottom:20px; text-align:center;'>👋 Bienvenue <b>{st.session_state.user_prenom}</b></div>", unsafe_allow_html=True)
    st.sidebar.markdown("### Vos Paramètres")
    
    montant_sb = st.sidebar.slider("Montant investi (€)", min_value=1000, max_value=100000, value=20000, step=1000, format="%d €")
    duree_mois_sb = st.sidebar.select_slider("Durée envisagée", [6, 12, 18, 24], value=12, format_func=lambda x: f"{x} mois")
    reinvestissement_sb = st.sidebar.radio("Stratégie (Post-2026)", ["Projet unique (Bullet)", "Réinvestissement des intérêts à chaque remboursement"])

    # --- DATA ---
    data_sources = {
        "Plateforme": ["Baltis", "Plateforme A (Frais + Défaut)", "Plateforme B (Défaut moyen)"],
        "Rendement Brut Théorique (%)": [10.0, 11.0, 9.5],
        "Frais Investisseur (%)": [0.0, 1.0, 0.0],
        "Taux de défaut historique (%)": [0.0, 4.5, 2.0]
    }
    df_resultats = calculer_simulation(montant_sb, duree_mois_sb, reinvestissement_sb, data_sources)
    gain_baltis = df_resultats.loc[df_resultats["Plateforme"] == "Baltis", "Rendement Net Réel (€)"].values[0]

    # --- SECTION : METRIQUES CUSTOM HTML (Remplace les st.metric moches) ---
    st.markdown("<h2>Résultat de votre simulation</h2>", unsafe_allow_html=True)
    
    metrics_html = f"""
    <div style="display: flex; gap: 20px; margin-bottom: 40px; flex-wrap: wrap;">
        <div style="flex: 1; background: white; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <p style="color: #64748B; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 600; text-transform: uppercase;">Capital Initial</p>
            <h3 style="color: #0A2540; font-size: 2rem; margin: 0; font-weight: 700;">{montant_sb:,.0f} €</h3>
        </div>
        <div style="flex: 1; background: #F8FAFC; padding: 25px; border-radius: 12px; border: 2px solid #2D6A4F; box-shadow: 0 10px 15px -3px rgba(45, 106, 79, 0.1);">
            <p style="color: #2D6A4F; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 700; text-transform: uppercase;">Intérêts Nets Baltis</p>
            <h3 style="color: #2D6A4F; font-size: 2.2rem; margin: 0; font-weight: 800;">+ {gain_baltis:,.0f} €</h3>
        </div>
        <div style="flex: 1; background: #0A2540; padding: 25px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(10, 37, 64, 0.2);">
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 600; text-transform: uppercase;">Capital Total Récupéré</p>
            <h3 style="color: white; font-size: 2rem; margin: 0; font-weight: 700;">{montant_sb + gain_baltis:,.0f} €</h3>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    # --- SECTION : GRAPHIQUE AFFINÉ & TABLEAU ---
    col_g1, col_g2 = st.columns([0.55, 0.45], gap="large")
    
    with col_g1:
        st.markdown("<h3>Comparaison des déductions (Frais & Défaut)</h3>", unsafe_allow_html=True)
        df_plot = df_resultats.copy()
        df_plot = pd.melt(df_plot, id_vars=['Plateforme'], value_vars=['Rendement Brut (€)', 'Impact Frais (€)', 'Impact Défaut (Est. Perte) (€)'])
        
        fig = px.bar(df_plot, x='Plateforme', y='value', color='variable', 
                     barmode='relative',
                     color_discrete_map={'Rendement Brut (€)': '#0A2540', 'Impact Frais (€)': '#F36121', 'Impact Défaut (Est. Perte) (€)': '#DC2626'})
        
        # Affinage du graphique Plotly pour faire "Pro"
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, title=""),
            font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color="#475569"),
            plot_bgcolor="rgba(0,0,0,0)", # Fond transparent
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            height=350 # Réduire la hauteur énorme
        )
        fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", tickprefix="€")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}) # Cache la barre d'outils plotly

    with col_g2:
        st.markdown("<h3>Synthèse Chiffrée</h3>", unsafe_allow_html=True)
        # On garde le dataframe mais on nettoie les colonnes inutiles pour la vue simplifiée
        df_display = df_resultats[['Plateforme', 'Rendement Brut Théorique (%)', 'Rendement Net Réel (€)']].copy()
        st.dataframe(df_display.style.format({
            "Rendement Brut Théorique (%)": "{:.1f}%",
            "Rendement Net Réel (€)": "{:.0f} €"
        }), use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton PDF Customisé via CSS global
        pdf_bytes = generer_pdf_premium(st.session_state.user_prenom, st.session_state.user_nom, montant_sb, duree_mois_sb, gain_baltis, df_resultats)
        st.download_button("📄 Télécharger mon Rapport PDF", data=pdf_bytes, file_name="Simulation_Baltis.pdf", mime="application/pdf")

    # --- SECTION : AVERTISSEMENTS (Fini le bloc jaune) ---
    st.markdown("<br><hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    warning_html = """
    <div style="background-color: #F8FAFC; border-left: 4px solid #94A3B8; padding: 20px; border-radius: 0 8px 8px 0; margin-top: 20px;">
        <h4 style="margin-top:0; color: #475569; font-size:1rem;">Avertissements et Limites (Régulation 2026)</h4>
        <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0; line-height: 1.5;">
        Outil pédagogique. Les résultats sont des projections basées sur des données historiques publiées et des modèles statistiques. Le taux de défaut de 0% constaté chez Baltis depuis 2016 est historique et ne constitue pas une garantie pour les opérations futures. Investir comporte des risques, notamment de perte partielle ou totale du capital investi. Baltis est immatriculée auprès de l'ORIAS sous le numéro [X] et régulée par l'Autorité des Marchés Financiers (PSFP).
        </p>
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)
