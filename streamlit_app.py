import streamlit as st
import os
from openai import OpenAI
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

# Configuration de la page Streamlit (doit être la première commande Streamlit)
st.set_page_config(page_title="Comparaison de Facture et Certificats bio.", layout="wide")

# Fonction pour vérifier le mot de passe
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Veuillez entrer le mot de passe", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error.
        st.text_input(
            "Veuillez entrer le mot de passe", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Mot de passe incorrect")
        return False
    else:
        # Password correct.
        return True

# Vérification du mot de passe avant d'afficher le contenu principal
if check_password():
    def convert_pdf_to_images(pdf_file):
        return convert_from_bytes(pdf_file.getvalue())

    def encode_image(image):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    st.title("Comparaison de Facture et Certificats bio")

    # Récupérer la clé API depuis les secrets de Streamlit
    api_key = st.secrets["OAIK"]

    with st.sidebar:
        st.header("Paramètres")
        max_tokens = st.slider("Nombre maximum de tokens pour la réponse", 100, 2000, 1000)

    col1, col2 = st.columns(2)

    with col1:
        facture_file = st.file_uploader("Télécharger la facture (PDF)", type="pdf")
        if facture_file:
            st.success("Facture téléchargée avec succès")

    with col2:
        certificat_file = st.file_uploader("Télécharger le certificat (PDF)", type="pdf")
        if certificat_file:
            st.success("Certificat téléchargé avec succès")

    if st.button("Analyser les documents"):
        if facture_file and certificat_file:
            with st.spinner("Conversion et analyse des documents en cours..."):
                try:
                    facture_images = convert_pdf_to_images(facture_file)
                    certificat_images = convert_pdf_to_images(certificat_file)

                    # Encoder toutes les pages
                    facture_images_base64 = [encode_image(img) for img in facture_images]
                    certificat_images_base64 = [encode_image(img) for img in certificat_images]

                    client = OpenAI(api_key=api_key)

                    # Préparer le contenu du message
                    content = [
                        {
                            "type": "text",
                            "text": "Analysez les documents suivants (facture et certificat) et fournissez un rapport détaillé sur :\n"
                                    "1. La correspondance des informations de l'émetteur entre la facture et le certificat.\n"
                                    "2. La vérification que la période de validité du certificat couvre les dates de la facture (de la date d'enlèvement à la date d'échéance).\n"
                                    "3. La correspondance des descriptions de produits de la facture avec la section 'II.1 Répertoire des produits' du certificat. Exemple: sur la facture 'CREME BRULEE 130G BBC' correspond à 'Yaourts et desserts: Crème brûlée' dans le certificat mais soyez rigoureux car  'ALSA PREPA POUR MOELL CIT 435G C7' ne correspond pas du tout à 'Desserts végétaux : Préparation en poudre pour clafoutis BIO ALSA (FOODSO)' . Si tu ne trouves pas de correspondance pour un produit il faut retourner l'EAN concerné.\n"
                                    "4. Pour tout produit sans correspondance, listez l'EAN concerné sous forme de tableau sans rien omettre.\n\n"
                                    "Présentez les résultats de manière structurée et facile à lire. Assurez-vous d'examiner toutes les pages des documents."
                        }
                    ]

                    # Ajouter toutes les pages de la facture
                    for i, img_base64 in enumerate(facture_images_base64):
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                            }
                        })

                    # Ajouter toutes les pages du certificat
                    for i, img_base64 in enumerate(certificat_images_base64):
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}",
                            }
                        })

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": content}],
                        max_tokens=max_tokens,
                    )

                    st.subheader("Résultat de l'analyse:")
                    st.markdown(response.choices[0].message.content)

                    # Affichage des aperçus
                    st.subheader("Aperçu des documents")
                    
                    with st.expander("Aperçu de la facture"):
                        for i, img in enumerate(facture_images):
                            st.image(img, caption=f"Facture - Page {i+1}", use_column_width=True)
                    
                    with st.expander("Aperçu du certificat"):
                        for i, img in enumerate(certificat_images):
                            st.image(img, caption=f"Certificat - Page {i+1}", use_column_width=True)

                except Exception as e:
                    st.error(f"Une erreur s'est produite lors de l'analyse : {str(e)}")
        else:
            st.error("Veuillez télécharger les deux fichiers avant de lancer l'analyse.")
