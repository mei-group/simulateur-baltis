import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
import requests
from io import BytesIO

# --- 1. CONFIGURATION DE LA PAGE & STYLE CSS ---
st.set_page_config(page_title="Simulateur Crowdfunding Immobilier | Baltis", layout="wide", page_icon="🏢")

# Définition des couleurs de la charte graphique
BALTIS_DARK_BLUE = "#0A2540" 
BALTIS_ACCENT = "#F36121"    
WHITE = "#FFFFFF"
LIGHT_GRAY = "#F6F9FC"

# Injection CSS Personnalisé
custom_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif !important;
        color: {BALTIS_DARK_BLUE} !important;
    }}

    h1 {{
        color: {BALTIS_DARK_BLUE};
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0rem;
    }}
    h2, h3, .stSubheader {{
        color: {BALTIS_DARK_BLUE};
        font-weight: 600;
        margin-top: 1.5rem;
    }}

    .stSidebar {{
        background-color: {LIGHT_GRAY};
        padding-top: 2rem;
    }}
    .stSidebar label {{
        color: {BALTIS_DARK_BLUE} !important;
        font-weight: 600;
    }}

    .stSlider {{
        color: {BALTIS_ACCENT} !important;
    }}

    .project-card {{
        background-color: {WHITE};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(10, 37, 64, 0.08);
        border-left: 5px solid {BALTIS_ACCENT};
        margin-bottom: 20px;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        color: {BALTIS_DARK_BLUE} !important;
    }}
    .gain-positive [data-testid="stMetricValue"] {{
        color: #2D6A4F !important; 
    }}

    .stDownloadButton button {{
        background-color: {BALTIS_ACCENT} !important;
        color: {WHITE} !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 20px;
        font-size: 1rem;
        transition: 0.3s;
    }}
    .stDownloadButton button:hover {{
        background-color: #D1521B !important; 
        transform: translateY(-2px);
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: #F8FAFD;
    }}
    .dataframe thead th {{
        background-color: {BALTIS_DARK_BLUE} !important;
        color: {WHITE} !important;
        font-weight: 600 !important;
    }}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- INITIALISATION DE L'ÉTAT ---
if 'acces_debloque' not in st.session_state:
    st.session_state.acces_debloque = False
if 'user_prenom' not in st.session_state:
    st.session_state.user_prenom = ""
if 'user_nom' not in st.session_state:
    st.session_state.user_nom = ""

# --- 2. FONCTION GETRESPONSE ---
def ajouter_contact_getresponse(prenom, nom, email):
    # En production, utilisez st.secrets
    api_key = st.secrets.get("getresponse_api_key", "VOTRE_CLE_API_PAR_DEFAUT")
    campaign_id = st.secrets.get("getresponse_campaign_id", "VOTRE_LISTE_ID_PAR_DEFAUT")
    
    url = "https://api.getresponse.com/v3/contacts"
    headers = {
        "X-Auth-Token": f"api-key {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "name": f"{prenom} {nom}",
        "email": email,
        "campaign": {"campaignId": campaign_id}
    }
    return True 

# --- 3. FONCTIONS DE CALCUL & NOMENCLATURES 2026 ---
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
    df["Rendement Net Réel (%)"] = (df["Rendement Net Réel (€)"] / montant) / duree_annees * 100

    return df

# --- 4. FONCTION GENERATION PDF PREMIUM ---
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
            self.multi_cell(0, 4, txt="Mention Légale AMF (Régulation 2026) : Investir comporte des risques, notamment de perte partielle ou totale du capital. Les performances passées ne préjugent pas des performances futures. Baltis est immatriculée sous le numéro [X] à l'ORIAS et régulée par l'AMF en tant que PSFP (Prestataire de Services de Financement Participatif).", align='C')
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
    pdf.cell(180, 8, txt=f"  Investissement prévu : {montant:,} EUR", ln=True)
    pdf.cell(180, 8, txt=f"  Durée envisagée : {duree} mois ({duree/12:.1f} an)", ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(180, 8, txt=f"  Gain Réel Estimé Baltis (Avant Impôts) : {gain_baltis_total:,.0f} EUR", ln=True)
    pdf.ln(15)

    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(243, 97, 33) 
    pdf.cell(0, 10, txt="Comparaison des Rendements Nets de Frais et Risque", ln=True)
    pdf.set_draw_color(10, 37, 64)
    pdf.set_line_width(0.3)
    pdf.line(pdf.get_x(), pdf.get_y(), 195, pdf.get_y()) 
    pdf.ln(2)

    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(10, 37, 64) 
    pdf.cell(40, 10, "Plateforme", border=1, align='C', fill=True)
    pdf.cell(35, 10, "Gain Brut (EUR)", border=1, align='C', fill=True)
    pdf.cell(35, 10, "Impact Frais (EUR)", border=1, align='C', fill=True)
    pdf.cell(40, 10, "Impact Risque Perte", border=1, align='C', fill=True)
    pdf.cell(30, 10, "Gain Réel (EUR)", border=1, align='C', fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    fill_row = False
    for index, row in df_complet.iterrows():
        if fill_row:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(40, 9, row['Plateforme'], border=1, align='C', fill=True)
        pdf.cell(35, 9, f"{row['Rendement Brut (€)']:.0f}", border=1, align='C', fill=True)
        pdf.cell(35, 9, f"- {row['Impact Frais (€)']:.0f}", border=1, align='C', fill=True)
        pdf.cell(40, 9, f"- {row['Impact Défaut (Est. Perte) (€)']:.0f}", border=1, align='C', fill=True)
        if row['Plateforme'] == "Baltis": pdf.set_font("Arial", "B", 9)
        pdf.cell(30, 9, f"{row['Rendement Net Réel (€)']:.0f}", border=1, align='C', fill=True)
        pdf.set_font("Arial", "", 9)
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
    pdf.cell(col_w, 8, txt=f"{montant:,.0f} EUR", ln=True, align='L')
    pdf.set_font("Arial", "", 10)
    
    pdf.cell(col_w, 8, txt="Intérêts Réels Générés :", align='R')
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(45, 106, 79) # CORRECTION COULEUR ICI (Vert)
    pdf.cell(col_w, 8, txt=f"+ {gain_baltis_total:,.0f} EUR", ln=True, align='L')
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)

    pdf.cell(col_w, 8, txt="Flux de Capital Récupéré :", align='R')
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(10, 37, 64)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(col_w, 8, txt=f" {montant + gain_baltis_total:,.0f} EUR", ln=True, align='L', fill=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(243, 97, 33) 
    pdf.cell(0, 8, txt="Avertissements et Limites du Simulateur", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    
    warning_text = ("Outil pédagogique. Les résultats ci-dessus sont des projections basées sur des données historiques publiées et des modèles statistiques. Le taux de défaut de 0% constaté chez Baltis depuis 2016 ne constitue pas une garantie pour les opérations futures. Le risque de perte partielle ou totale du capital est réel et doit être intégré dans toute décision d'investissement.")
    pdf.multi_cell(0, 5, warning_text)
    
    return pdf.output(dest="S").encode("latin-1")

# ==========================================
# GESTION DES SECTIONS PRINCIPALES
# ==========================================

with st.container():
    col_t1, col_t2 = st.columns([0.8, 0.2])
    col_t1.title("Simulateur de comparaison plateformes crowdfunding immobilier")
    col_t1.subheader("Calculez l'impact réel des frais, du taux de défaut et du rendement net sur votre épargne")
    
    col_t2.markdown(f'<div style="text-align: right; margin-top: 15px; background-color: {BALTIS_DARK_BLUE}; color: {WHITE}; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 1.2rem;">BALTIS</div>', unsafe_allow_html=True)
    st.write("---")

if not st.session_state.acces_debloque:
    col_f1, col_f2 = st.columns([0.6, 0.4])
    with col_f1:
        st.markdown(f"### Obtenez vos résultats personnalisés")
        st.caption("Outil pédagogique. Résultats basés sur les données historiques publiées. Ne constitue pas un conseil en investissement.")
    
        with st.form("lead_capture_form"):
            col1, col2 = st.columns(2)
            prenom_input = col1.text_input("Prénom")
            nom_input = col2.text_input("Nom")
            email_input = st.text_input("Email")
            
            submitted = st.form_submit_button("Accéder à mon simulateur gratuit - Calculez votre rendement net réel selon la plateforme choisie")
            
            if submitted: # CORRECTION INDENTATION ICI
                if prenom_input and email_input:
                    ajouter_contact_getresponse(prenom_input, nom_input, email_input)
                    st.session_state.acces_debloque = True
                    st.session_state.user_prenom = prenom_input
                    st.session_state.user_nom = nom_input
                    st.rerun()
                else:
                    st.error("Veuillez remplir au moins votre prénom et votre email.")
    with col_f2:
        st.markdown(f'<div style="background-color: {LIGHT_GRAY}; border-radius: 12px; padding: 30px; text-align: center; color: #888; font-size: 1rem; border: 2px dashed #DDD; margin-top: 20px;">🔒 Entrez vos informations pour débloquer l\'outil premium de comparaison et votre PDF</div>', unsafe_allow_html=True)

else:
    st.sidebar.markdown(f"**Bienvenue {st.session_state.user_prenom} !**")
    st.sidebar.markdown("### Vos Paramètres")
    
    montant_sb = st.sidebar.slider("Montant que vous souhaitez investir (€)", min_value=1000, max_value=100000, value=15000, step=1000, format="%d €")
    duree_mois_sb = st.sidebar.select_slider("Durée d'investissement envisagée", [6, 12, 18, 24], value=6, format_func=lambda x: f"{x} mois ({x/12:.1f} an)")
    reinvestissement_sb = st.sidebar.radio("Fréquence globale de réinvestissement (Post-2026)", ["Une seule fois", "Réinvestissement des intérêts à chaque remboursement"])

    data_sources = {
        "Plateforme": ["Baltis", "Plateforme A (Frais + Défaut)", "Plateforme B (Défaut moyen)"],
        "Rendement Brut Théorique (%)": [10.0, 11.0, 9.5],
        "Frais Investisseur (%)": [0.0, 1.0, 0.0],
        "Taux de défaut historique (%)": [0.0, 4.5, 2.0]
    }
    
    df_resultats = calculer_simulation(montant_sb, duree_mois_sb, reinvestissement_sb, data_sources)

    st.header("1. Comparaison des plateformes sur vos chiffres")
    
    col_c1, col_c2 = st.columns([0.65, 0.35])
    with col_c1:
        st.write("### Impact Réel : Brut vs Frais vs Défaut")
        df_plot = df_resultats.copy()
        df_plot = pd.melt(df_plot, id_vars=['Plateforme'], value_vars=['Rendement Brut (€)', 'Impact Frais (€)', 'Impact Défaut (Est. Perte) (€)'])
        df_plot['Action'] = np.where(df_plot['variable'] == 'Rendement Brut (€)', 'Rendement', 'Coût/Risque')

        fig = px.bar(df_plot, x='Plateforme', y='value', color='variable', 
                     barmode='relative',
                     color_discrete_map={
                         'Rendement Brut (€)': '#2D6A4F',       
                         'Impact Frais (€)': '#D1521B',        
                         'Impact Défaut (Est. Perte) (€)': '#8B0000' 
                     },
                     labels={'value': 'Montant (EUR)', 'variable': 'Détail du Flux'})
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Montserrat, sans-serif", size=11),
            yaxis_tickprefix="€",
            margin=dict(l=0, r=0, b=0, t=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_c2:
        st.write("### Votre Gain Net Réel")
        st.dataframe(df_resultats.style.format({
            "Rendement Brut Théorique (%)": "{:.1f}%",
            "Frais Investisseur (%)": "{:.1f}%",
            "Taux de défaut historique (%)": "{:.1f}%",
            "Rendement Brut (€)": "{:.0f} €",
            "Impact Frais (€)": "-{:.0f} €",
            "Impact Défaut (Est. Perte) (€)": "-{:.0f} €",
            "Rendement Net Réel (€)": "**{:.0f} €**",
            "Rendement Net Réel (%)": "{:.1f}%/an"
        }), height=230, use_container_width=True)

    st.write("---")
    st.header("2. Simulation Baltis détaillée")
    
    gain_baltis = df_resultats.loc[df_resultats["Plateforme"] == "Baltis", "Rendement Net Réel (€)"].values[0]
    rendement_baltis_brut = df_resultats.loc[df_resultats["Plateforme"] == "Baltis", "Rendement Brut Théorique (%)"].values[0]
    
    col_b1, col_b2 = st.columns([0.45, 0.55])
    
    with col_b1:
        project_details_html = f"""
        <div class="project-card">
            <h4>🏢 Exemple de projet type correspondant</h4>
            <ul style="font-size: 0.95rem; line-height: 1.6;">
                <li><strong>Durée :</strong> {duree_mois_sb} mois</li>
                <li><strong>Rendement cible :</strong> {rendement_baltis_brut:.1f}% annuel</li>
                <li><strong>Type de garantie :</strong> Hypothèque de 1er rang</li>
                <li><strong>Secteur géographique :</strong> Île-de-France (92)</li>
                <li><strong>Profil du promoteur :</strong> Historique positif, 15 projets réalisés</li>
            </ul>
        </div>
        """
        st.markdown(project_details_html, unsafe_allow_html=True)

    with col_b2:
        st.write("### Projection des Gains")
        col1_m, col2_m, col3_m = st.columns(3)
        col1_m.metric("Capital Initial", f"{montant_sb:,} €".replace(",", " "))
        
        col2_m.markdown(f'<div class="gain-positive">', unsafe_allow_html=True)
        col2_m.metric("Intérêts Réels (Baltis)", f"+{gain_baltis:,.0f} €".replace(",", " "))
        col2_m.markdown(f'</div>', unsafe_allow_html=True)
        
        col3_m.metric("Capital Récupéré", f"{montant_sb + gain_baltis:,.0f} €".replace(",", " "))
        
        st.write("")
        pdf_bytes = generer_pdf_premium(st.session_state.user_prenom, st.session_state.user_nom, montant_sb, duree_mois_sb, gain_baltis, df_resultats)
        st.download_button(
            label="📄 Télécharger ma simulation Premium PDF",
            data=pdf_bytes,
            file_name="Simulation_Baltis_Premium.pdf",
            mime="application/pdf"
        )

    st.write("---")
    st.write("### Avertissements et limites")
    st.warning("""
    **Attention :** Outil pédagogique. Les résultats ci-dessus sont des projections basées sur des données historiques publiées par les plateformes référencées et des modèles statistiques ajustés au marché 2026. 
    Le taux de défaut de 0% constaté chez Baltis depuis 2016 est historique et ne constitue pas une garantie pour les opérations futures. Le risque de perte partielle ou totale du capital investi est réel et doit être intégré dans toute décision d'investissement.
    """)
    st.caption("Investir comporte des risques, notamment de perte partielle ou totale du capital investi. Les performances passées ne préjugent pas des performances futures. Les rendements cibles affichés sont des objectifs et non des garanties. Baltis est immatriculée auprès de l'ORIAS sous le numéro [X] et régulée par l'Autorité des Marchés Financiers au titre du statut de Prestataire de Services de Financement Participatif (PSFP).")

    st.write("---")
    st.markdown(f'<div style="text-align: center; margin-top: 15px; background-color: {BALTIS_DARK_BLUE}; color: {WHITE}; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);"><h2>🏢 Passez à l\'action aujourd\'hui</h2><p style="font-size: 1.1rem; max-width: 600px; margin: 10px auto;">Créez votre compte Baltis pour accéder aux projets ouverts. Accessible dès 100€, plateforme régulée par l\'AMF.</p></div>', unsafe_allow_html=True)
    
    col_j, col_j2, col_j3 = st.columns([0.35, 0.3, 0.35])
    with col_j2:
        st.markdown("")
        st.link_button("🚀 Créer mon compte gratuitement", "https://www.baltis.com")
