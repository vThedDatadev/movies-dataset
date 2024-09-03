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

st.title("Comparaison de Facture et Certificat")

api_key = st.text_input("Entrez votre clé API OpenAI", type="password")

if not api_key:
    st.warning("Veuillez entrer votre clé API OpenAI pour continuer.")
    st.stop()

facture_file = st.file_uploader("Télécharger la facture (PDF)", type="pdf")
certificat_file = st.file_uploader("Télécharger le certificat (PDF)", type="pdf")

if st.button("Analyser les documents"):
    if facture_file and certificat_file:
        try:
            facture_images = convert_pdf_to_images(facture_file)
            certificat_images = convert_pdf_to_images(certificat_file)

            facture_image_base64 = encode_image(facture_images[0])
            certificat_image_base64 = encode_image(certificat_images[0])

            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Compare les deux documents. Dis-moi si les informations de l'émetteur de la facture correspondent aux informations contenues dans le certificat. Vérifie aussi que la période de validité du certificat couvre les dates de la facture, c'est-à-dire de la date d'enlèvement jusqu'à la date d'échéance de la facture. Pour finir analyse la correspondance des descriptions produits de la facture avec la section 'II.1 Répertoire des produits' du certificat: Si pour une description produit de la facture il n'y a pas de correspondance dans le certificat, les documents sont refusés",
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
                max_tokens=500,
            )

            st.write("Résultat de l'analyse:")
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Une erreur s'est produite lors de l'analyse : {str(e)}")
    else:
        st.error("Veuillez télécharger les deux fichiers avant de lancer l'analyse.")

st.info("Note : Votre clé API est traitée de manière sécurisée et n'est pas stockée après la fermeture de l'application.")
