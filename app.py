import streamlit as st
import os
import json
from datetime import datetime
from transformers import pipeline
import pandas as pd

# Modules pour extraire le texte depuis différents formats
import PyPDF2
import docx
from pptx import Presentation

# ---------------------------------------
# Définition des fichiers de stockage persistants, etc.
COURSES_DB_FILE = "courses_db.json"
EXAMS_DB_FILE = "exams_db.json"
FEEDBACK_DB_FILE = "feedback_history.json"

# Fonctions de stockage (pour cours, annales et feedback) … (identiques aux versions précédentes)
def load_courses_db():
    if os.path.exists(COURSES_DB_FILE):
        try:
            with open(COURSES_DB_FILE, "r") as f:
                courses = json.load(f)
        except Exception as e:
            st.error("Erreur lors du chargement de la base de cours.")
            courses = []
    else:
        courses = []
    return courses

def save_courses_db(courses):
    with open(COURSES_DB_FILE, "w") as f:
        json.dump(courses, f, ensure_ascii=False, indent=4)

def load_exams_db():
    if os.path.exists(EXAMS_DB_FILE):
        try:
            with open(EXAMS_DB_FILE, "r") as f:
                exams = json.load(f)
        except Exception as e:
            st.error("Erreur lors du chargement de la base de sujets d'annales.")
            exams = []
    else:
        exams = []
    return exams

def save_exams_db(exams):
    with open(EXAMS_DB_FILE, "w") as f:
        json.dump(exams, f, ensure_ascii=False, indent=4)

def load_feedback_history():
    if os.path.exists(FEEDBACK_DB_FILE):
        try:
            with open(FEEDBACK_DB_FILE, "r") as f:
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
    with open(FEEDBACK_DB_FILE, "w") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# ---------------------------------------
# Fonction d'extraction de texte depuis différents formats
def extract_text_from_file(uploaded_file):
    """
    Extrait le texte d'un fichier en fonction de son extension.
    Formats supportés : .txt, .pdf, .docx, .pptx, .xls et .xlsx.
    Pour les PDF, chaque page sera préfixée par une annotation indiquant le numéro de page et le nom du fichier.
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
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"Page {idx+1} de '{uploaded_file.name}':\n" + page_text + "\n\n"
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

# ---------------------------------------
# Initialisation du générateur de questions (ici T5-base)
generator = pipeline("text2text-generation", model="t5-base")

st.title("Générateur de Questions Type Annales")

# (La gestion de dépôt persistant des cours et annales est inchangée par rapport à la version précédente)
tabs = st.tabs(["Cours", "Sujets d'annales", "Générer les questions", "Feedback", "Historique Feedback"])

# [...] (Les onglets 1 et 2 restent identiques à la version précédente où l'on dépose et sauvegarde cours et annales avec leur année)

# -------------------- Onglet 3 : Générer les questions --------------------
with tabs[2]:
    st.header("Générer les questions")
    
    # Sélection d'une plage d'années pour filtrer cours et annales
    st.subheader("Filtrer par année")
    start_year = st.number_input("Année de début", value=2000, step=1, key="start_year")
    end_year = st.number_input("Année de fin", value=2025, step=1, key="end_year")
    
    # Chargement et filtrage des cours
    courses_db = load_courses_db()
    filtered_courses = [course for course in courses_db if start_year <= course["year"] <= end_year]
    course_options = {}
    for course in filtered_courses:
        display_title = f"{course['title']} ({course['year']})"
        course_options[display_title] = course["text"]
    selected_courses = st.multiselect("Sélectionnez les cours à utiliser", options=list(course_options.keys()), key="selected_courses_gen")
    course_content = ""
    for course in selected_courses:
        course_content += f"Cours : {course}\n{course_options[course]}\n\n"
    
    # Chargement et filtrage des sujets d'annales
    exams_db = load_exams_db()
    filtered_exams = [exam for exam in exams_db if start_year <= exam["year"] <= end_year]
    exam_options = {}
    for exam in filtered_exams:
        display_title = f"{exam['title']} ({exam['year']})"
        exam_options[display_title] = exam["text"]
    selected_exams = st.multiselect("Sélectionnez les sujets d'annales à utiliser", options=list(exam_options.keys()), key="selected_exams_gen")
    exam_content = ""
    for exam in selected_exams:
        exam_content += f"Sujet d'annale : {exam}\n{exam_options[exam]}\n\n"
    
    if not course_content or not exam_content:
        st.info("Veuillez sélectionner au moins un cours et un sujet d'annale dans la plage d'années spécifiée.")
    else:
        generation_mode = st.radio("Choisissez le mode de génération :", ["Une Question", "Annales Complète"], key="generation_mode")
        base_prompt = "Génère des questions d'examen basées sur le contenu suivant :\n\n"
        base_prompt += f"{course_content}\n"
        base_prompt += f"{exam_content}\n"
        # L'instruction suivante précise que la réponse doit contenir également la provenance (nom du pdf et numéro de page)
        if generation_mode == "Une Question":
            base_prompt += "\nVeuillez générer une seule question d'examen. Pour cette question, indiquez la réponse ainsi que la provenance sous la forme 'Page X de \"Nom du document\"'."
            max_len = 128
        else:
            base_prompt += "\nVeuillez générer une annale complète composée de plusieurs questions. Pour chacune, indiquez la réponse ainsi que la provenance sous la forme 'Page X de \"Nom du document\"'."
            max_len = 256
        
        st.write("Prompt généré automatiquement (modifiable) :")
        st.text_area("Prompt (modifiable)", value=base_prompt, key="custom_prompt", height=150)
        
        if st.button("Générer"):
            prompt_to_use = st.session_state.custom_prompt
            st.write("Génération en cours...")
            with st.spinner("Veuillez patienter..."):
                try:
                    output = generator(prompt_to_use, max_length=max_len, num_return_sequences=1)
                    generated_questions = output[0]["generated_text"]
                    st.subheader("Questions générées")
                    st.write(generated_questions)
                    st.session_state.generated_questions = generated_questions
                    # La liste des intitulés (sans l'année) utilisés pour la génération est sauvegardée
                    used_courses = [c.split(" (")[0] for c in selected_courses]
                    st.session_state.generated_questions_courses = used_courses
                    if not selected_courses and course_options:
                        st.session_state.generated_questions_courses = []
                except Exception as e:
                    st.error(f"Une erreur est survenue lors de la génération : {e}")

# -------------------- Onglet 4 et Onglet 5 (Feedback et Historique) --------------------
# [La gestion du feedback et de l'historique reste identique à la version précédente]

# (Le reste du code reste inchangé)
