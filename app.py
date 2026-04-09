import streamlit as st
import pandas as pd
from fpdf import FPDF
import requests
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur Crowdfunding - Baltis", layout="centered")

# --- INITIALISATION DE L'ÉTAT (Gérer l'accès après le formulaire) ---
if 'acces_debloque' not in st.session_state:
    st.session_state.acces_debloque = False
if 'user_prenom' not in st.session_state:
    st.session_state.user_prenom = ""
if 'user_nom' not in st.session_state:
    st.session_state.user_nom = ""

# --- FONCTION GETRESPONSE ---
def ajouter_contact_getresponse(prenom, nom, email):
    # Remplacez par votre vraie clé API et votre ID de liste (Campaign ID)
    api_key = "VOTRE_CLE_API_GETRESPONSE"
    campaign_id = "VOTRE_LISTE_ID"
    
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
    # En production : requests.post(url, headers=headers, json=data)
    # Pour le test, on retourne True
    return True

# --- FONCTION GENERATION PDF ---
def generer_pdf(prenom, montant, duree, rendement_net):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Simulation Crowdfunding Immobilier - Baltis", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Simulation personnalisee pour : {prenom}", ln=True)
    pdf.cell(200, 10, txt=f"Montant investi : {montant} EUR", ln=True)
    pdf.cell(200, 10, txt=f"Duree : {duree} mois", ln=True)
    pdf.cell(200, 10, txt=f"Rendement net estime (Baltis) : {rendement_net} EUR", ln=True)
    pdf.ln(20)
    pdf.multi_cell(0, 10, txt="Avertissement : Investir comporte des risques, notamment de perte partielle ou totale du capital. Les performances passees ne prejugent pas des performances futures. Baltis est regulee par l'AMF en tant que PSFP.")
    
    return pdf.output(dest="S").encode("latin-1")

# --- TITRE PRINCIPAL ---
st.title("Simulateur de comparaison plateformes crowdfunding immobilier")
st.subheader("Calculez l'impact réel des frais, du taux de défaut et du rendement net sur votre épargne")

# ==========================================
# GESTION DU FORMULAIRE DE CAPTURE (LEAD)
# ==========================================
if not st.session_state.acces_debloque:
    st.markdown("### Obtenez vos résultats personnalisés")
    st.caption("Outil pédagogique. Résultats basés sur les données historiques publiées. Ne constitue pas un conseil en investissement.")
    
    with st.form("lead_capture_form"):
        col1, col2 = st.columns(2)
        prenom = col1.text_input("Prénom")
        nom = col2.text_input("Nom")
        email = st.text_input("Email")
        
        submitted = st.form_submit_button("Accéder à mon simulateur gratuit - Calculez votre rendement net réel selon la plateforme choisie")
        
        if submitted:
            if prenom and email:
                # Appel API GetResponse
                ajouter_contact_getresponse(prenom, nom, email)
                # Débloquer le simulateur
                st.session_state.acces_debloque = True
                st.session_state.user_prenom = prenom
                st.session_state.user_nom = nom
                st.rerun()
            else:
                st.error("Veuillez remplir au moins votre prénom et votre email.")

# ==========================================
# LE SIMULATEUR (Débloqué)
# ==========================================
else:
    st.success(f"Bienvenue {st.session_state.user_prenom}, votre simulateur est débloqué !")

    # SECTION 1 — Vos paramètres d'investissement
    st.header("1. Vos paramètres d'investissement")
    montant = st.slider("Montant que vous souhaitez investir (€)", min_value=1000, max_value=100000, value=10000, step=1000)
    duree_mois = st.selectbox("Durée d'investissement envisagée", [6, 12, 18, 24])
    reinvestissement = st.radio("Fréquence de réinvestissement", ["Une seule fois", "Réinvestissement des intérêts à chaque remboursement"])

    duree_annees = duree_mois / 12

    # SECTION 2 — Comparaison des plateformes
    st.header("2. Comparaison des plateformes sur vos chiffres")
    
    # Données fictives comparatives (à adapter selon vos vraies data)
    data = {
        "Plateforme": ["Baltis", "Plateforme A", "Plateforme B"],
        "Rendement Brut Théorique (%)": [10.0, 11.0, 9.5],
        "Frais Investisseur (%)": [0.0, 1.0, 0.0],
        "Taux de défaut historique (%)": [0.0, 4.5, 2.0]
    }
    df = pd.DataFrame(data)
    
    # Calculs dynamiques pour le tableau
    df["Rendement Brut (€)"] = df["Rendement Brut Théorique (%)"] / 100 * montant * duree_annees
    df["Impact Frais (€)"] = df["Frais Investisseur (%)"] / 100 * montant
    df["Impact Défaut (Est.) (€)"] = df["Taux de défaut historique (%)"] / 100 * montant
    df["Rendement Net Ajusté (€)"] = df["Rendement Brut (€)"] - df["Impact Frais (€)"] - df["Impact Défaut (Est.) (€)"]

    # Affichage du tableau formaté
    st.dataframe(df.style.format({
        "Rendement Brut Théorique (%)": "{:.1f}%",
        "Frais Investisseur (%)": "{:.1f}%",
        "Taux de défaut historique (%)": "{:.1f}%",
        "Rendement Brut (€)": "{:.0f} €",
        "Impact Frais (€)": "-{:.0f} €",
        "Impact Défaut (Est.) (€)": "-{:.0f} €",
        "Rendement Net Ajusté (€)": "{:.0f} €"
    }))

    # SECTION 3 — Simulation Baltis détaillée
    st.header("3. Simulation Baltis détaillée")
    gain_baltis = df.loc[df["Plateforme"] == "Baltis", "Rendement Net Ajusté (€)"].values[0]
    
    st.markdown("""
    **Exemple de projet type correspondant à votre profil :**
    * **Durée :** {} mois
    * **Rendement cible :** 10% annuel
    * **Type de garantie :** Hypothèque de 1er rang
    * **Secteur :** Île-de-France
    * **Profil promoteur :** Historique positif, 15 projets réalisés
    """.format(duree_mois))

    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Investi", f"{montant} €")
    col2.metric("Intérêts Générés (Avant Impôts)", f"+{gain_baltis:.0f} €")
    col3.metric("Capital Récupéré", f"{montant + gain_baltis:.0f} €")

    # BOUTON EXPORT PDF
    pdf_bytes = generer_pdf(st.session_state.user_prenom, montant, duree_mois, gain_baltis)
    st.download_button(
        label="📄 Télécharger ma simulation en PDF",
        data=pdf_bytes,
        file_name="Simulation_Baltis.pdf",
        mime="application/pdf"
    )

    # SECTION 4 — Avertissement
    st.header("4. Avertissements et limites")
    st.warning("""
    **Attention :** Les résultats ci-dessus sont des projections basées sur des données historiques. 
    Le taux de défaut à 0% constaté chez Baltis depuis 2016 ne constitue pas une garantie pour les opérations futures. 
    Le risque de perte en capital est réel et doit être intégré dans toute décision d'investissement.
    """)
    st.caption("Investir comporte des risques, notamment de perte partielle ou totale du capital investi. Les performances passées ne préjugent pas des performances futures. Les rendements cibles affichés sont des objectifs et non des garanties. Baltis est immatriculée auprès de l'ORIAS sous le numéro [X] et régulée par l'Autorité des Marchés Financiers au titre du statut de Prestataire de Services de Financement Participatif (PSFP).")

    # SECTION 5 — Prochaine étape
    st.header("5. Passez à l'action")
    st.info("Rejoignez Baltis aujourd'hui pour accéder à nos projets en cours de financement. Accessible dès 100€, plateforme régulée par l'AMF.")
    st.link_button("Créer mon compte Baltis gratuitement", "https://www.baltis.com")
