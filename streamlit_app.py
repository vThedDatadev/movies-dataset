import streamlit as st
import os
from openai import OpenAI
import base64

# Fonction pour encoder le fichier en base64
def encode_file(file):
    return base64.b64encode(file.getvalue()).decode()

# Initialisation de l'application Streamlit
st.title("Comparaison de Facture et Certificat")

# Champs pour télécharger les fichiers
facture_file = st.file_uploader("Télécharger la facture (PDF)", type="pdf")
certificat_file = st.file_uploader("Télécharger le certificat (PDF)", type="pdf")

# Bouton pour lancer l'analyse
if st.button("Analyser les documents"):
    if facture_file and certificat_file:
        # Encodage des fichiers en base64
        facture_base64 = encode_file(facture_file)
        certificat_base64 = encode_file(certificat_file)

        # Initialisation du client OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        # Création de la requête
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Compare les deux documents. Dis-moi si les informations de l'émetteur de la facture correspondent aux informations contenues dans le certificat. Vérifie aussi que la période de validité du certificat couvre les dates de la facture, c'est-à-dire de la date d'enlèvement à la date d'échéance de la facture.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{facture_base64}",
                            },
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{certificat_base64}",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
        )

        # Affichage du résultat
        st.write("Résultat de l'analyse:")
        st.write(response.choices[0].message.content)
    else:
        st.error("Veuillez télécharger les deux fichiers avant de lancer l'analyse.")

# Message d'information pour la clé API
st.info("Assurez-vous d'avoir défini la variable d'environnement OPENAI_API_KEY avec votre clé API OpenAI avant d'exécuter cette application.")
