import streamlit as st
from transformers import pipeline
import json
import os
from datetime import datetime

# Fonctions pour charger et sauvegarder l'historique du feedback
def load_feedback_history():
    if os.path.exists("feedback_history.json"):
        try:
            with open("feedback_history.json", "r") as f:
                history = json.load(f)
        except Exception as e:
            st.error("Erreur lors du chargement de l'historique des feedbacks.")
            history = []
    else:
        history = []
    return history

def save_feedback_entry(entry):
    history = load_feedback_history()
    history.append(entry)
    with open("feedback_history.json", "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# Initialisation du générateur de questions avec le modèle T5
generator = pipeline("text2text-generation", model="t5-base")

st.title("Générateur de Questions Type Annales")

# Définition des onglets : 
#  1. Cours
#  2. Sujets d'annales
#  3. Générer les questions
#  4. Feedback (notation individuelle & globale)
#  5. Historique des feedbacks
tabs = st.tabs(["Cours", "Sujets d'annales", "Générer les questions", "Feedback", "Historique Feedback"])

# Onglet 1 : Cours
with tabs[0]:
    st.header("Déposer un cours")
    # Choix du chapitre (optionnel)
    chapter = st.text_input("Titre du chapitre (optionnel)")
    # Zone de texte pour le contenu du cours
    course_text = st.text_area("Colle ici le contenu du cours", height=300)
    # Option de téléversement de fichier (txt, pdf)
    uploaded_course = st.file_uploader("Ou téléverse un fichier de cours", type=["txt", "pdf"])
    if uploaded_course is not None:
        try:
            course_text = uploaded_course.getvalue().decode("utf-8")
        except Exception as e:
            st.error("Le fichier n'a pas pu être lu correctement.")

# Onglet 2 : Sujets d'annales
with tabs[1]:
    st.header("Déposer un sujet d'annale")
    exam_text = st.text_area("Colle ici le sujet d'examen", height=200)

# Onglet 3 : Générer les questions
with tabs[2]:
    st.header("Générer les questions")
    if not course_text or not exam_text:
        st.info("Merci de déposer à la fois un cours et un sujet d'annale dans les onglets dédiés.")
    else:
        # Construction automatique du prompt de génération
        base_prompt = "Génère des questions d'examen basées sur le contenu suivant :\n\n"
        if chapter:
            base_prompt += f"Chapitre : {chapter}\n\n"
        base_prompt += f"Cours :\n{course_text}\n\nSujet d'annale :\n{exam_text}\n\n"
        base_prompt += "Les questions doivent correspondre à des sujets d'examen type annales."
        
        st.write("Prompt généré automatiquement (modifiable) :")
        # Zone de texte avec le prompt, permettant à l'utilisateur de le modifier si besoin
        st.text_area("Prompt (modifiable)", value=base_prompt, key="custom_prompt", height=150)
        
        if st.button("Générer"):
            prompt_to_use = st.session_state.custom_prompt
            st.write("Génération en cours...")
            with st.spinner("Veuillez patienter..."):
                try:
                    output = generator(prompt_to_use, max_length=256, num_return_sequences=1)
                    generated_questions = output[0]["generated_text"]
                    st.subheader("Questions générées")
                    st.write(generated_questions)
                    # Stockage temporaire des questions générées pour la notation
                    st.session_state.generated_questions = generated_questions
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de la génération : {e}")

# Onglet 4 : Feedback
with tabs[3]:
    st.header("Donnez votre avis sur la qualité des questions")
    if "generated_questions" not in st.session_state:
        st.info("Veuillez d'abord générer des questions dans l'onglet 'Générer les questions'.")
    else:
        st.write("Notez chaque question individuellement :")
        # On découpe le texte généré en différentes questions (en supprimant les lignes vides)
        questions_list = [q.strip() for q in st.session_state.generated_questions.split("\n") if q.strip() != ""]
        question_ratings = {}
        for i, question in enumerate(questions_list):
            st.markdown(f"**Question {i+1}** : {question}")
            rating = st.slider(
                f"Votre note pour la question {i+1} (1 = Médiocre, 5 = Excellent)",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                key=f"rating_{i}"
            )
            question_ratings[f"Question {i+1}"] = {"question": question, "rating": rating}
        
        # Une note globale pour l'ensemble des questions
        overall_rating = st.slider("Note Globale pour l'ensemble des questions (1 = Médiocre, 5 = Excellent)", min_value=1, max_value=5, value=3, step=1, key="overall_rating")
        if st.button("Envoyer votre feedback"):
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "generated_questions": st.session_state.generated_questions,
                "question_ratings": question_ratings,
                "overall_rating": overall_rating
            }
            save_feedback_entry(feedback_entry)
            st.success("Merci pour votre feedback !")
            st.session_state.last_feedback = feedback_entry

# Onglet 5 : Historique des feedbacks
with tabs[4]:
    st.header("Historique des feedbacks")
    history = load_feedback_history()
    if not history:
        st.info("Aucun feedback enregistré pour le moment.")
    else:
        for entry in history:
            st.markdown(f"**Date et heure :** {entry.get('timestamp', 'Inconnue')}")
            st.markdown(f"**Note Globale :** {entry.get('overall_rating', 'N/A')}")
            qr = entry.get("question_ratings", {})
            if qr:
                st.markdown("**Notes par question :**")
                for key, val in qr.items():
                    st.markdown(f"- {key} : {val.get('rating', 'N/A')} (Question : {val.get('question', '')})")
            st.markdown("---")
