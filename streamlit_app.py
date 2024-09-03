import streamlit as st
import os
from openai import OpenAI
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

def convert_pdf_to_images(pdf_file):
    images = convert_from_bytes(pdf_file.getvalue())
    return images

def encode_image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

st.set_page_config(page_title="Comparaison de Facture et Certificat", layout="wide")

st.title("Comparaison de Facture et Certificat")

# Sidebar pour les paramètres
with st.sidebar:
    st.header("Paramètres")
    api_key = st.text_input("Entrez votre clé API OpenAI", type="password")
    max_tokens = st.slider("Nombre maximum de tokens pour la réponse", 100, 1000, 500)

if not api_key:
    st.warning("Veuillez entrer votre clé API OpenAI dans la barre latérale pour continuer.")
    st.stop()

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
        with st.spinner("Analyse en cours..."):
            try:
                facture_images = convert_pdf_to_images(facture_file)
                certificat_images = convert_pdf_to_images(certificat_file)

                facture_image_base64 = encode_image(facture_images[0])
                certificat_image_base64 = encode_image(certificat_images[0])

                client = OpenAI(api_key=api_key)

                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analysez les documents suivants et fournissez un rapport détaillé sur :\n"
                                            "1. La correspondance des informations de l'émetteur entre la facture et le certificat.\n"
                                            "2. La vérification que la période de validité du certificat couvre les dates de la facture (de la date d'enlèvement à la date d'échéance).\n"
                                            "3. La correspondance des descriptions de produits de la facture avec la section 'II.1 Répertoire des produits' du certificat.\n"
                                            "4. Pour tout produit sans correspondance, listez l'EAN concerné.\n\n"
                                            "Présentez les résultats de manière structurée et facile à lire.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{facture_image_base64}",
                                    },
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{certificat_image_base64}",
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=max_tokens,
                )

                st.subheader("Résultat de l'analyse:")
                st.markdown(response.choices[0].message.content)

                # Affichage des images
                st.subheader("Aperçu des documents")
                col1, col2 = st.columns(2)
                with col1:
                    st.image(facture_images[0], caption="Facture", use_column_width=True)
                with col2:
                    st.image(certificat_images[0], caption="Certificat", use_column_width=True)

            except Exception as e:
                st.error(f"Une erreur s'est produite lors de l'analyse : {str(e)}")
    else:
        st.error("Veuillez télécharger les deux fichiers avant de lancer l'analyse.")

st.info("Note : Votre clé API est traitée de manière sécurisée et n'est pas stockée après la fermeture de l'application.")
