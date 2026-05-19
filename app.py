import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
import os

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur Crowdfunding | Baltis", layout="wide", initial_sidebar_state="expanded")

# Fonction utilitaire pour espacer les milliers (ex: 90 000 au lieu de 90,000)
def format_spaces(val):
    return f"{val:,.0f}".replace(",", " ")

# --- 2. CSS "PREMIUM+++" (BALTIS) ---
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* NETTOYAGE TOTAL DE L'INTERFACE STREAMLIT */
    [data-testid="stToolbar"], footer, #MainMenu, .stDeployButton, header, [class^="viewerBadge_container"], [data-testid="stDecoration"] {
        display: none !important; 
        visibility: hidden !important; 
    }
    
    /* VERROUILLAGE DE LA SIDEBAR (On cache les boutons Ouvrir/Fermer) */
    [data-testid="collapsedControl"], 
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* FORCER LE THÈME CLAIR */
    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0A2540 !important;
        background-color: #FAFAFA !important;
    }

    h1 { font-weight: 800; font-size: 2.5rem; letter-spacing: -0.03em; margin-bottom: 0.5rem; color: #0A2540; }
    h2 { font-weight: 700; font-size: 1.8rem; letter-spacing: -0.02em; margin-top: 2rem; color: #0A2540; }
    h3 { font-weight: 600; font-size: 1.4rem; color: #0A2540; }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0;
    }
    [data-testid="stSidebar"] * {
        color: #0A2540 !important;
    }
    
    /* CORRECTION DU FOND BLEU SUR LE TEXTE DE BIENVENUE */
    [data-testid="stSidebar"] .stMarkdown p {
        background-color: transparent !important;
    }
    
    /* BOUTON TELECHARGER (ORANGE BALTIS) */
    .stDownloadButton button {
        background-color: #F36121 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(243, 97, 33, 0.3) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(243, 97, 33, 0.4) !important;
    }
    .stDownloadButton button p { color: white !important; }

    /* BOUTONS SIDEBAR (Déconnexion) */
    [data-testid="stSidebar"] .stButton button {
        background-color: #FFFFFF !important;
        color: #0A2540 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: #F1F5F9 !important;
        border-color: #CBD5E1 !important;
    }

    /* SLIDERS */
    .stSlider [data-testid="stTickBar"] { display: none; }
    
    /* RADIOS (Boutons de choix) */
    .stRadio p { color: #0A2540 !important; font-weight: 500 !important; }
    
    .hoverlayer { font-family: 'Plus Jakarta Sans', sans-serif !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. INITIALISATION ÉTAT ET DÉTECTION DU TOKEN ---
if 'acces_debloque' not in st.session_state:
    st.session_state.acces_debloque = False
if 'user_prenom' not in st.session_state:
    st.session_state.user_prenom = ""
if 'user_nom' not in st.session_state:
    st.session_state.user_nom = ""

# Lecture de l'URL pour débloquer l'accès
if "token" in st.query_params:
    if st.query_params["token"] == "baltis_vip":
        st.session_state.acces_debloque = True
        
        # Récupération du prénom envoyé par GetResponse
        if "name" in st.query_params:
            st.session_state.user_prenom = st.query_params["name"].capitalize()
        elif "firstname" in st.query_params:
            st.session_state.user_prenom = st.query_params["firstname"].capitalize()
        elif not st.session_state.user_prenom:
            st.session_state.user_prenom = "Investisseur"

# --- 4. FONCTIONS METIER ---
def logout():
    st.session_state.acces_debloque = False
    st.session_state.user_prenom = ""
    st.session_state.user_nom = ""

def format_montant(val):
    if val >= 1000000:
        return f"{val/1000000:g} M€"
    elif val >= 10000:
        return f"{val/1000:g} k€"
    else:
        return f"{val} €"

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

# --- 5. FONCTION GENERATION PDF ---
def generer_pdf_premium(prenom, nom, montant, duree, gain_baltis_total, df_complet):
    class PDF(FPDF):
        def header(self):
            self.set_fill_color(10, 37, 64) 
            self.rect(0, 0, 210, 30, 'F')
            self.set_font('Arial', 'B', 18)
            self.set_text_color(255, 255, 255)
            self.cell(10, 10) 
            self.cell(40, 10, 'BALTIS', 0, 0, 'L')
            self.set_font('Arial', '', 11)
            self.cell(140, 10, 'SIMULATION CROWDFUNDING IMMOBILIER', 0, 1, 'R')
            self.ln(10)

        def footer(self):
            self.set_y(-25)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(10, 37, 64)
            legal_text = (
                "Les performances passées ne préjugent pas des performances futures. "
                "Tout investissement comporte un risque de perte totale ou partielle du capital investi. "
                "Baltis est agréée par l'Autorité des Marchés Financiers (AMF) en tant que "
                "Prestataire de Services de Financement Participatif (PSFP) sous le numéro FP-2023-30."
            )
            self.multi_cell(0, 4, txt=legal_text, align='C')
            self.ln(1)
            self.cell(0, 5, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_margins(15, 30, 15)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(10, 37, 64)
    pdf.cell(0, 10, txt=f"Rapport de Simulation Personnalisé pour : {prenom} {nom}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_fill_color(246, 249, 252)
    pdf.rect(15, pdf.get_y(), 180, 25, 'F') 
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(180, 8, txt=f"  Investissement prévu : {format_spaces(montant)} EUR", ln=True)
    pdf.cell(180, 8, txt=f"  Durée envisagée : {duree} mois", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(180, 8, txt=f"  Gain Réel Estimé Baltis (Avant Impôts) : {format_spaces(gain_baltis_total)} EUR", ln=True)
    pdf.ln(15)

    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(243, 97, 33) 
    pdf.cell(0, 10, txt="Comparaison des Rendements Nets de Frais et Risque", ln=True)
    pdf.set_draw_color(10, 37, 64)
    pdf.set_line_width(0.3)
    pdf.line(pdf.get_x(), pdf.get_y(), 195, pdf.get_y()) 
    pdf.ln(2)

    pdf.set_font("Arial", "B", 8.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(10, 37, 64) 
    
    w_plat = 50
    w_brut = 32
    w_frais = 32
    w_risq = 34
    w_net = 32

    pdf.cell(w_plat, 10, "Plateforme", border=1, align='C', fill=True)
    pdf.cell(w_brut, 10, "Gain Brut", border=1, align='C', fill=True)
    pdf.cell(w_frais, 10, "Impact Frais", border=1, align='C', fill=True)
    pdf.cell(w_risq, 10, "Risque Perte", border=1, align='C', fill=True)
    pdf.cell(w_net, 10, "Gain Réel Net", border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 8.5)
    pdf.set_text_color(0, 0, 0)
    fill_row = False
    
    for index, row in df_complet.iterrows():
        if fill_row:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(w_plat, 9, str(row['Plateforme']), border=1, align='C', fill=True)
        pdf.cell(w_brut, 9, f"{format_spaces(row['Rendement Brut (€)'])} EUR", border=1, align='C', fill=True)
        pdf.cell(w_frais, 9, f"- {format_spaces(row['Impact Frais (€)'])} EUR", border=1, align='C', fill=True)
        pdf.cell(w_risq, 9, f"- {format_spaces(row['Impact Défaut (Est. Perte) (€)'])} EUR", border=1, align='C', fill=True)
        
        if row['Plateforme'] == "Baltis": 
            pdf.set_font("Arial", "B", 8.5)
        
        pdf.cell(w_net, 9, f"{format_spaces(row['Rendement Net Réel (€)'])} EUR", border=1, align='C', fill=True)
        pdf.set_font("Arial", "", 8.5)
        pdf.ln()
        fill_row = not fill_row

    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(10, 37, 64)
    pdf.cell(0, 10, txt="Synthèse Projection Flux de Capital (Baltis)", ln=True)
    pdf.set_line_width(0.3)
    pdf.line(pdf.get_x(), pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(255, 255, 255)
    
    col_w = 60
    pdf.cell(col_w, 8, txt="Capital Initial Investi :", align='R')
    pdf.set_font("Arial", "B", 10)
    pdf.cell(col_w, 8, txt=f"{format_spaces(montant)} EUR", ln=True, align='L')
    pdf.set_font("Arial", "", 10)
    
    pdf.cell(col_w, 8, txt="Intérêts Réels Générés :", align='R')
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(45, 106, 79)
    pdf.cell(col_w, 8, txt=f"+ {format_spaces(gain_baltis_total)} EUR", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)

    pdf.cell(col_w, 8, txt="Flux de Capital Récupéré :", align='R')
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(10, 37, 64)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_w, 8, txt=f" {format_spaces(montant + gain_baltis_total)} EUR", ln=True, align='L', fill=True)
    
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# HEADER UI AVEC GESTION DU LOGO
# ==========================================
col_header1, col_header2 = st.columns([0.8, 0.2])

with col_header1:
    st.markdown("<h1 style='margin:0; font-size: 2rem; margin-top: -10px;'>Simulateur de rendement net</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; margin: 5px 0 20px 0; font-size: 1.1rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 15px;'>Calculez l'impact réel des frais et du défaut sur votre épargne.</p>", unsafe_allow_html=True)

with col_header2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("""
        <div style="background-color: #0A2540; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 800; font-size: 1.2rem; letter-spacing: 2px; text-align: center; margin-top: -10px;">
            BALTIS
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# ÉCRAN DE BLOCAGE (GATED CONTENT)
# ==========================================
if not st.session_state.acces_debloque:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_espace1, col_lock, col_espace2 = st.columns([1, 2, 1])
    
    with col_lock:
        lock_html = """
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 40px; text-align: center; box-shadow: 0 10px 30px rgba(10, 37, 64, 0.05);">
            <div style="font-size: 3rem; margin-bottom: 10px;">🔒</div>
            <h2 style="margin-top: 0; color: #0A2540;">Accès restreint</h2>
            <p style="color: #64748B; font-size: 1.1rem; margin-bottom: 30px;">
                Ce simulateur premium est réservé. Pour y accéder gratuitement et obtenir vos résultats personnalisés, veuillez vous inscrire via notre page officielle.
            </p>
            <a href="https://www.baltis.com/" target="_self" style="text-decoration: none;">
                <button style="background-color: #0A2540; color: white; border: none; border-radius: 8px; padding: 1rem 2rem; font-weight: 600; font-size: 1.1rem; cursor: pointer; width: 100%; transition: background-color 0.2s;">
                    Accéder via Baltis.com
                </button>
            </a>
        </div>
        """
        st.markdown(lock_html, unsafe_allow_html=True)

# ==========================================
# SIMULATEUR PREMIUM (Débloqué)
# ==========================================
else:
    # --- SIDEBAR ---
    prenom_display = st.session_state.user_prenom if st.session_state.user_prenom else "Investisseur"
    
    # Encart bienvenue avec couleurs forcées
    st.sidebar.markdown(
        f"""
        <div style="background-color: #0A2540; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
            <span style="color: #FFFFFF !important; font-size: 1.1rem;">👋 Bienvenue <b style="color: #FFFFFF !important;">{prenom_display}</b></span>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.sidebar.markdown("### Vos Paramètres")
    
    options_montants = list(range(100, 1000, 100)) + list(range(1000, 10000, 500)) + list(range(10000, 100000, 1000)) + list(range(100000, 1000001, 10000))
    montant_sb = st.sidebar.select_slider(
        "Montant investi", 
        options=options_montants, 
        value=20000, 
        format_func=format_montant
    )
    
    duree_mois_sb = st.sidebar.slider("Durée envisagée (mois)", min_value=6, max_value=60, value=12, step=1)
    reinvestissement_sb = st.sidebar.radio("Stratégie (Post-2026)", ["Projet unique (Bullet)", "Réinvestissement des intérêts à chaque remboursement"])

    # Bouton Déconnexion
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🔄 Se déconnecter / Quitter"):
        # Vide l'URL des paramètres pour vraiment re-verrouiller l'accès
        st.query_params.clear()
        logout()
        st.rerun()

    # --- DATA ---
    data_sources = {
        "Plateforme": ["Baltis", "Plateforme A (Frais + Défaut)", "Plateforme B (Défaut moyen)"],
        "Rendement Brut Théorique (%)": [10.0, 11.0, 9.5],
        "Frais Investisseur (%)": [0.0, 1.0, 0.0],
        "Taux de défaut historique (%)": [0.0, 4.5, 2.0]
    }
    df_resultats = calculer_simulation(montant_sb, duree_mois_sb, reinvestissement_sb, data_sources)
    gain_baltis = df_resultats.loc[df_resultats["Plateforme"] == "Baltis", "Rendement Net Réel (€)"].values[0]

    # --- METRIQUES ---
    st.markdown("<h2>Résultat de votre simulation</h2>", unsafe_allow_html=True)
    metrics_html = f"""
    <div style="display: flex; gap: 20px; margin-bottom: 40px; flex-wrap: wrap;">
        <div style="flex: 1; background: white; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <p style="color: #64748B; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 600; text-transform: uppercase;">Capital Initial</p>
            <h3 style="color: #0A2540; font-size: 2rem; margin: 0; font-weight: 700;">{format_spaces(montant_sb)} €</h3>
        </div>
        <div style="flex: 1; background: #F8FAFC; padding: 25px; border-radius: 12px; border: 2px solid #2D6A4F; box-shadow: 0 10px 15px -3px rgba(45, 106, 79, 0.1);">
            <p style="color: #2D6A4F; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 700; text-transform: uppercase;">Intérêts Nets Baltis</p>
            <h3 style="color: #2D6A4F; font-size: 2.2rem; margin: 0; font-weight: 800;">+ {format_spaces(gain_baltis)} €</h3>
        </div>
        <div style="flex: 1; background: #0A2540; padding: 25px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(10, 37, 64, 0.2);">
            <p style="color: #94A3B8; font-size: 0.9rem; margin: 0 0 5px 0; font-weight: 600; text-transform: uppercase;">Capital Total Récupéré</p>
            <h3 style="color: white; font-size: 2rem; margin: 0; font-weight: 700;">{format_spaces(montant_sb + gain_baltis)} €</h3>
        </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    # --- GRAPHIQUE & TABLEAU ---
    col_g1, col_g2 = st.columns([0.55, 0.45], gap="large")
    
    with col_g1:
        st.markdown("<h3>Comparaison des déductions (Frais & Défaut)</h3>", unsafe_allow_html=True)
        df_plot = df_resultats.copy()
        df_plot = pd.melt(df_plot, id_vars=['Plateforme'], value_vars=['Rendement Brut (€)', 'Impact Frais (€)', 'Impact Défaut (Est. Perte) (€)'])
        
        df_plot['Nom Variable'] = df_plot['variable'].map({
            'Rendement Brut (€)': 'Gain Théorique',
            'Impact Frais (€)': 'Frais Prélevés',
            'Impact Défaut (Est. Perte) (€)': 'Risque Statistique'
        })
        
        # Ajout d'une colonne de données formatées avec espaces pour le survol du graphique
        df_plot['Formatted Value'] = df_plot['value'].apply(lambda x: format_spaces(x))

        fig = px.bar(df_plot, x='Plateforme', y='value', color='Nom Variable', custom_data=['Formatted Value'],
                     barmode='relative',
                     color_discrete_map={'Gain Théorique': '#0A2540', 'Frais Prélevés': '#F36121', 'Risque Statistique': '#DC2626'})
        
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{data.name}: <b>%{customdata[0]} €</b><extra></extra>")

        fig.update_layout(
            legend=dict(
                orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0, title="",
                itemclick=False, itemdoubleclick=False
            ),
            xaxis=dict(fixedrange=True),
            yaxis=dict(fixedrange=True),
            font=dict(family="Plus Jakarta Sans, sans-serif", size=12, color="#475569"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
            height=350,
            hoverlabel=dict(bgcolor="white", font_size=13, font_family="Plus Jakarta Sans")
        )
        fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", tickprefix="€")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with col_g2:
        st.markdown("<h3>Synthèse Chiffrée</h3>", unsafe_allow_html=True)
        df_display = df_resultats[['Plateforme', 'Rendement Brut Théorique (%)', 'Rendement Net Réel (€)']].copy()
        
        # On formate directement la colonne pour intégrer l'espace des milliers
        df_display['Rendement Net Réel (€)'] = df_display['Rendement Net Réel (€)'].apply(lambda x: f"{format_spaces(x)} €")
        df_display['Rendement Brut Théorique (%)'] = df_display['Rendement Brut Théorique (%)'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        pdf_bytes = generer_pdf_premium(prenom_display, st.session_state.user_nom, montant_sb, duree_mois_sb, gain_baltis, df_resultats)
        st.download_button("📄 Télécharger mon Rapport PDF", data=pdf_bytes, file_name="Simulation_Baltis.pdf", mime="application/pdf")

    # --- AVERTISSEMENTS ---
    st.markdown("<br><hr style='border-color: #E2E8F0;'>", unsafe_allow_html=True)
    warning_html = """
    <div style="background-color: #F8FAFC; border-left: 4px solid #94A3B8; padding: 20px; border-radius: 0 8px 8px 0; margin-top: 20px;">
        <h4 style="margin-top:0; color: #475569; font-size:1rem;">Avertissements et Mentions Légales</h4>
        <p style="font-size: 0.85rem; color: #64748B; margin-bottom: 0; line-height: 1.5;">
        Outil pédagogique. Les résultats sont des projections basées sur des données historiques publiées et des modèles statistiques. 
        <br><b>Les performances passées ne préjugent pas des performances futures. Tout investissement comporte un risque de perte totale ou partielle du capital investi.</b> 
        <br>Baltis est agréée par l'Autorité des Marchés Financiers (AMF) en tant que Prestataire de Services de Financement Participatif (PSFP) sous le numéro d'agrément FP-2023-30.
        </p>
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)
