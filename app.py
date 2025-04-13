import streamlit as st
import os
import json
from datetime import datetime
from transformers import pipeline
import pandas as pd

# Modules pour l'extraction de texte depuis différents formats
import PyPDF2
import docx
from pptx import Presentation

# --- Fonction d'extraction de texte selon le format ---
def extract_text_from_file(uploaded_file):
    """
    Extrait le texte d'un fichier selon son extension.
    Formats supportés : .txt, .pdf, .docx, .pptx, .xls, .xlsx
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    text = ""
    if file_extension == ".txt":
        try:
            text = uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            text = "Erreur lors de la lecture du fichier texte."
    elif file_extension == ".pdf":
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            text = "Erreur lors de l'extraction du PDF."
    elif file_extension == ".docx":
        try:
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            text = "Erreur lors de l'extraction du document Word."
    elif file_extension == ".pptx":
        try:
            presentation = Presentation(uploaded_file)
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
        except Exception as e:
            text = "Erreur lors de l'extraction du PowerPoint."
    elif file_extension in [".xls", ".xlsx"]:
        try:
            df = pd.read_excel(uploaded_file)
            text = df.to_string(index=False)
        except Exception as e:
            text = "Erreur lors de l'extraction du fichier Excel."
    else:
        text = "Format de fichier non supporté."
    return text

# --- Fonctions pour gérer l'historique des feedbacks ---
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

# --- Initialisation du générateur de questions ---
generator = pipeline("text2text-generation", model="t5-base")

st.title("Générateur de Questions Type Annales")
tabs = st.tabs(["Cours", "Sujets d'annales", "Générer les questions", "Feedback", "Historique Feedback"])

# -------------------- Onglet 1 : Déposer un cours --------------------
with tabs[0]:
    st.header("Déposer un cours")
    mode_course = st.radio("Sélectionnez le mode de dépôt du cours :", 
                           ("Téléverser des fichiers", "Saisie manuelle"), key="mode_course")
    
    if mode_course == "Téléverser des fichiers":
        common_title_course = st.text_input("Titre commun du cours (optionnel)", key="common_course_title")
        uploaded_course_files = st.file_uploader("Téléversez un ou plusieurs fichiers de cours",
                                                 type=["txt", "pdf", "docx", "pptx", "xls", "xlsx"],
                                                 accept_multiple_files=True,
                                                 key="uploaded_course_files")
        if uploaded_course_files:
            courses_dict = {}
            if common_title_course:
                # Tous les fichiers font partie d'un même cours
                combined_text = ""
                for file in uploaded_course_files:
                    text = extract_text_from_file(file)
                    if text.startswith("Erreur") or text.startswith("Format"):
                        st.error(f"{file.name} : {text}")
                    else:
                        combined_text += f"{text}\n"
                if combined_text:
                    courses_dict[common_title_course] = combined_text
            else:
                # Chaque fichier constitue un cours distinct
                for file in uploaded_course_files:
                    text = extract_text_from_file(file)
                    if text.startswith("Erreur") or text.startswith("Format"):
                        st.error(f"{file.name} : {text}")
                    else:
                        courses_dict[file.name] = text
            if courses_dict:
                st.success(f"{len(courses_dict)} cours téléversés avec succès !")
                st.session_state.uploaded_courses = courses_dict
    else:
        # Saisie manuelle du cours
        chapter = st.text_input("Titre du cours ou chapitre", key="manual_course_title")
        manual_course_text = st.text_area("Collez ici le contenu du cours", height=300, key="manual_course_text")
        if manual_course_text:
            st.session_state.manual_course = {"title": chapter if chapter else "Cours manuel",
                                                "text": manual_course_text}
            st.success("Cours saisi manuellement sauvegardé.")

# -------------------- Onglet 2 : Déposer un sujet d'annale --------------------
with tabs[1]:
    st.header("Déposer un sujet d'annale")
    mode_exam = st.radio("Sélectionnez le mode de dépôt du sujet d'annale :", 
                         ("Téléverser des fichiers", "Saisie manuelle"), key="mode_exam")
    if mode_exam == "Téléverser des fichiers":
        common_title_exam = st.text_input("Titre commun du sujet d'annale (optionnel)", key="common_exam_title")
        uploaded_exam_files = st.file_uploader("Téléversez un ou plusieurs fichiers de sujets d'annales",
                                               type=["txt", "pdf", "docx", "pptx", "xls", "xlsx"],
                                               accept_multiple_files=True,
                                               key="uploaded_exam_files")
        if uploaded_exam_files:
            exam_dict = {}
            if common_title_exam:
                # Tous les fichiers font partie du même sujet d'annale
                combined_text = ""
                for file in uploaded_exam_files:
                    text = extract_text_from_file(file)
                    if text.startswith("Erreur") or text.startswith("Format"):
                        st.error(f"{file.name} : {text}")
                    else:
                        combined_text += f"{text}\n"
                if combined_text:
                    exam_dict[common_title_exam] = combined_text
            else:
                # Chaque fichier constitue un sujet d'annale distinct
                for file in uploaded_exam_files:
                    text = extract_text_from_file(file)
                    if text.startswith("Erreur") or text.startswith("Format"):
                        st.error(f"{file.name} : {text}")
                    else:
                        exam_dict[file.name] = text
            if exam_dict:
                st.success(f"{len(exam_dict)} sujets d'annales téléversés avec succès !")
                st.session_state.uploaded_exams = exam_dict
    else:
        # Saisie manuelle du sujet d'annale
        exam_title = st.text_input("Titre du sujet d'annale", key="manual_exam_title")
        manual_exam_text = st.text_area("Collez ici le contenu du sujet d'annale", height=200, key="manual_exam_text")
        if manual_exam_text:
            st.session_state.manual_exam = {"title": exam_title if exam_title else "Sujet manuel",
                                              "text": manual_exam_text}
            st.success("Sujet d'annale saisi manuellement sauvegardé.")

# -------------------- Onglet 3 : Générer les questions --------------------
with tabs[2]:
    st.header("Générer les questions")
    # Constitution de la source des cours
    course_options = {}
    if "uploaded_courses" in st.session_state:
        course_options.update(st.session_state.uploaded_courses)
    if "manual_course" in st.session_state:
        course_options[st.session_state.manual_course["title"]] = st.session_state.manual_course["text"]
    
    course_content = ""
    if course_options:
        selected_courses = st.multiselect("Sélectionnez les cours à utiliser",
                                          options=list(course_options.keys()),
                                          key="selected_courses")
        for course in selected_courses:
            course_content += f"Cours : {course}\n{course_options[course]}\n\n"
    else:
        st.info("Veuillez déposer au moins un cours dans l'onglet 'Cours'.")

    # Constitution de la source des sujets d'annales
    exam_options = {}
    if "uploaded_exams" in st.session_state:
        exam_options.update(st.session_state.uploaded_exams)
    if "manual_exam" in st.session_state:
        exam_options[st.session_state.manual_exam["title"]] = st.session_state.manual_exam["text"]
    
    exam_content = ""
    if exam_options:
        selected_exams = st.multiselect("Sélectionnez les sujets d'annales à utiliser",
                                        options=list(exam_options.keys()),
                                        key="selected_exams")
        for exam in selected_exams:
            exam_content += f"Sujet d'annale : {exam}\n{exam_options[exam]}\n\n"
    else:
        st.info("Veuillez déposer au moins un sujet d'annale dans l'onglet 'Sujets d'annales'.")
    
    if not course_content or not exam_content:
        st.info("Merci de déposer à la fois un cours et un sujet d'annale.")
    else:
        base_prompt = "Génère des questions d'examen basées sur le contenu suivant :\n\n"
        base_prompt += f"{course_content}\n"
        base_prompt += f"{exam_content}\n"
        base_prompt += "Les questions doivent correspondre à des sujets d'examen type annales."
        
        st.write("Prompt généré automatiquement (modifiable) :")
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
                    st.session_state.generated_questions = generated_questions
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de la génération : {e}")

# -------------------- Onglet 4 : Feedback --------------------
with tabs[3]:
    st.header("Donner votre avis sur la qualité des questions")
    if "generated_questions" not in st.session_state:
        st.info("Veuillez d'abord générer des questions dans l'onglet 'Générer les questions'.")
    else:
        st.write("Notez chaque question individuellement :")
        questions_list = [q.strip() for q in st.session_state.generated_questions.split("\n") if q.strip() != ""]
        question_ratings = {}
        for i, question in enumerate(questions_list):
            st.markdown(f"**Question {i+1}** : {question}")
            rating = st.slider(
                f"Votre note pour la question {i+1} (1 = Médiocre, 5 = Excellent)",
                min_value=1, max_value=5, value=3, step=1,
                key=f"rating_{i}"
            )
            question_ratings[f"Question {i+1}"] = {"question": question, "rating": rating}
        
        overall_rating = st.slider("Note globale pour l'ensemble des questions (1 = Médiocre, 5 = Excellent)",
                                   min_value=1, max_value=5, value=3, step=1, key="overall_rating")
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

# -------------------- Onglet 5 : Historique des feedbacks --------------------
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
