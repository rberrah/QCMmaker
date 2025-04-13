import streamlit as st
import os
import json
from datetime import datetime
from transformers import pipeline
import pandas as pd

# Modules d'extraction pour divers formats
import PyPDF2
import docx
from pptx import Presentation

# === Définition des chemins pour la persistance ===
COURSES_DB_FILE = "courses_db.json"
EXAMS_DB_FILE = "exams_db.json"
FEEDBACK_DB_FILE = "feedback_history.json"

# === Fonctions de persistance JSON ===
def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur lors du chargement de {file_path} : {e}")
            return []
    else:
        return []

def save_json(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de {file_path} : {e}")

def load_courses():
    return load_json(COURSES_DB_FILE)

def save_courses(courses):
    save_json(COURSES_DB_FILE, courses)

def load_exams():
    return load_json(EXAMS_DB_FILE)

def save_exams(exams):
    save_json(EXAMS_DB_FILE, exams)

def load_feedback():
    return load_json(FEEDBACK_DB_FILE)

def save_feedback(feedback):
    save_json(FEEDBACK_DB_FILE, feedback)

# === Fonction d'extraction de texte depuis un fichier ===
def extract_text(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext == ".txt":
        try:
            return uploaded_file.getvalue().decode("utf-8")
        except Exception as e:
            return f"Erreur lecture TXT: {e}"
    elif ext == ".pdf":
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"Page {idx+1} de '{uploaded_file.name}':\n{page_text}\n\n"
            return text
        except Exception as e:
            return f"Erreur extraction PDF: {e}"
    elif ext == ".docx":
        try:
            doc = docx.Document(uploaded_file)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"Erreur extraction DOCX: {e}"
    elif ext == ".pptx":
        try:
            prs = Presentation(uploaded_file)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text
        except Exception as e:
            return f"Erreur extraction PPTX: {e}"
    elif ext in [".xls", ".xlsx"]:
        try:
            df = pd.read_excel(uploaded_file)
            return df.to_string(index=False)
        except Exception as e:
            return f"Erreur extraction Excel: {e}"
    else:
        return "Format non supporté."

# === Initialisation du générateur ===
try:
    generator = pipeline("text2text-generation", model="t5-base")
except Exception as e:
    st.error(f"Erreur lors du chargement du modèle de génération : {e}")
    generator = None

# === Interface principale ===
st.title("Générateur de Questions Type Annales")

# Utilisation d'onglets pour organiser l'application
tabs = st.tabs(["Cours", "Sujets d'annales", "Générer", "Feedback", "Historique"])

# --------- Onglet 1 : Déposer des Cours ---------
with tabs[0]:
    st.header("Déposer des Cours")
    deposit_mode = st.radio("Mode de dépôt", ["Téléverser", "Saisie manuelle"], key="course_mode")
    course_year = st.number_input("Année du cours", value=2025, step=1, key="course_year")
    
    if deposit_mode == "Téléverser":
        common_title = st.text_input("Titre commun (optionnel)", key="course_common_title")
        files = st.file_uploader("Choisissez un ou plusieurs fichiers", type=["txt", "pdf", "docx", "pptx", "xls", "xlsx"], 
                                 key="course_files", accept_multiple_files=True)
        if st.button("Enregistrer les cours"):
            if files:
                new_courses = []
                if common_title:
                    combined = ""
                    for f in files:
                        txt = extract_text(f)
                        combined += txt + "\n"
                    new_courses.append({"title": common_title, "year": int(course_year), "text": combined})
                else:
                    for f in files:
                        txt = extract_text(f)
                        new_courses.append({"title": f.name, "year": int(course_year), "text": txt})
                courses = load_courses()
                courses.extend(new_courses)
                save_courses(courses)
                st.success(f"{len(new_courses)} cours enregistrés.")
            else:
                st.warning("Aucun fichier sélectionné.")
    else:
        manual_title = st.text_input("Titre du cours", key="manual_course_title")
        manual_text = st.text_area("Entrez le contenu du cours", key="manual_course_text")
        if st.button("Enregistrer le cours"):
            if manual_text:
                new_course = {"title": manual_title if manual_title else "Cours manuel", "year": int(course_year), "text": manual_text}
                courses = load_courses()
                courses.append(new_course)
                save_courses(courses)
                st.success("Cours enregistré.")
            else:
                st.warning("Le contenu du cours est vide.")

# --------- Onglet 2 : Déposer des Sujets d'annales ---------
with tabs[1]:
    st.header("Déposer des Sujets d'annales")
    deposit_mode = st.radio("Mode", ["Téléverser", "Saisie manuelle"], key="exam_mode")
    exam_year = st.number_input("Année du sujet", value=2025, step=1, key="exam_year")
    
    if deposit_mode == "Téléverser":
        common_title = st.text_input("Titre commun (optionnel)", key="exam_common_title")
        files = st.file_uploader("Choisissez un ou plusieurs fichiers", type=["txt", "pdf", "docx", "pptx", "xls", "xlsx"], 
                                 key="exam_files", accept_multiple_files=True)
        if st.button("Enregistrer les sujets"):
            if files:
                new_exams = []
                if common_title:
                    combined = ""
                    for f in files:
                        txt = extract_text(f)
                        combined += txt + "\n"
                    new_exams.append({"title": common_title, "year": int(exam_year), "text": combined})
                else:
                    for f in files:
                        txt = extract_text(f)
                        new_exams.append({"title": f.name, "year": int(exam_year), "text": txt})
                exams = load_exams()
                exams.extend(new_exams)
                save_exams(exams)
                st.success(f"{len(new_exams)} sujets enregistrés.")
            else:
                st.warning("Aucun fichier sélectionné.")
    else:
        manual_title = st.text_input("Titre du sujet", key="manual_exam_title")
        manual_text = st.text_area("Entrez le contenu du sujet", key="manual_exam_text")
        if st.button("Enregistrer le sujet"):
            if manual_text:
                new_exam = {"title": manual_title if manual_title else "Sujet manuel", "year": int(exam_year), "text": manual_text}
                exams = load_exams()
                exams.append(new_exam)
                save_exams(exams)
                st.success("Sujet enregistré.")
            else:
                st.warning("Le contenu du sujet est vide.")

# --------- Onglet 3 : Générer des Questions ---------
with tabs[2]:
    st.header("Générer des Questions")
    st.subheader("Filtrer par Année")
    start_year = st.number_input("Année de début", value=2000, step=1, key="gen_start_year")
    end_year = st.number_input("Année de fin", value=2025, step=1, key="gen_end_year")
    
    # Filtrer les cours et sujets enregistrés
    courses = load_courses()
    exams = load_exams()
    filtered_courses = [c for c in courses if start_year <= c["year"] <= end_year]
    filtered_exams = [e for e in exams if start_year <= e["year"] <= end_year]
    
    course_opts = {f"{c['title']} ({c['year']})": c["text"] for c in filtered_courses}
    exam_opts = {f"{e['title']} ({e['year']})": e["text"] for e in filtered_exams}
    
    sel_courses = st.multiselect("Sélectionnez les cours", list(course_opts.keys()), key="gen_sel_courses")
    sel_exams = st.multiselect("Sélectionnez les sujets", list(exam_opts.keys()), key="gen_sel_exams")
    
    if sel_courses and sel_exams:
        # Concaténer les contenus
        cont_courses = "\n".join([f"Cours : {title}\n{course_opts[title]}" for title in sel_courses])
        cont_exams   = "\n".join([f"Sujet : {title}\n{exam_opts[title]}" for title in sel_exams])
        
        gen_mode = st.radio("Mode de génération", ["Une Question", "Annales Complète"], key="gen_mode")
        prompt = "Génère des questions d'examen basées sur le contenu suivant :\n\n" + cont_courses + "\n" + cont_exams + "\n"
        if gen_mode == "Une Question":
            prompt += "Veuillez générer une seule question d'examen. Pour la réponse, mentionnez la provenance sous la forme 'Page X de \"Nom du document\"'."
            max_len = 128
        else:
            prompt += "Veuillez générer une annale complète composée de plusieurs questions. Pour chacune, indiquez la réponse et la provenance (ex: Page X de \"Nom du document\")."
            max_len = 256
        
        # Laisser la possibilité de modifier le prompt
        prompt = st.text_area("Prompt généré (modifiable)", value=prompt, height=150, key="gen_prompt")
        if st.button("Générer"):
            if generator is None:
                st.error("Le générateur n'est pas correctement initialisé.")
            else:
                st.write("Génération en cours...")
                try:
                    out = generator(prompt, max_length=max_len, num_return_sequences=1)
                    result = out[0]["generated_text"]
                    st.subheader("Questions Générées")
                    st.write(result)
                    st.session_state.generated_result = result
                    # On extraira le titre (sans l'année) des cours utilisés,
                    # à supposer qu'on ne sélectionne qu'un cours pour feedback.
                    titles_used = [opt.split(" (")[0] for opt in sel_courses]
                    st.session_state.gen_courses = titles_used
                except Exception as e:
                    st.error(f"Erreur lors de la génération : {e}")
    else:
        st.info("Sélectionnez au moins un cours et un sujet dans la plage d'années.")
        
# --------- Onglet 4 : Feedback ---------
with tabs[3]:
    st.header("Feedback")
    if "generated_result" not in st.session_state:
        st.info("Générez d'abord des questions.")
    elif not ("gen_courses" in st.session_state and len(set(st.session_state.gen_courses)) == 1):
        st.info("Le feedback est disponible uniquement si les questions proviennent d'un seul cours.")
    else:
        st.write("Notez chaque question générée :")
        questions = [q.strip() for q in st.session_state.generated_result.split("\n") if q.strip()]
        fb = {}
        for idx, q in enumerate(questions):
            st.markdown(f"**Question {idx+1}**: {q}")
            note = st.slider(f"Notez la question {idx+1}", 1, 5, 3, key=f"q_{idx}")
            fb[f"Question {idx+1}"] = {"question": q, "note": note}
        overall = st.slider("Note globale", 1, 5, 3, key="overall")
        if st.button("Envoyer le feedback"):
            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "generated": st.session_state.generated_result,
                "feedback": fb,
                "overall": overall,
                "course": st.session_state.gen_courses[0]
            }
            feedbacks = load_feedback()
            feedbacks.append(feedback_entry)
            save_feedback(feedbacks)
            st.success("Feedback enregistré.")

# --------- Onglet 5 : Historique ---------
with tabs[4]:
    st.header("Historique des Feedbacks")
    feedbacks = load_feedback()
    if feedbacks:
        courses_set = sorted({entry.get("course", "N/A") for entry in feedbacks})
        filt = st.selectbox("Filtrer par cours", ["Tous"] + courses_set, key="hist_filter")
        for entry in feedbacks:
            if filt != "Tous" and entry.get("course") != filt:
                continue
            st.markdown(f"**Date/Heure**: {entry.get('timestamp')}")
            st.markdown(f"**Cours**: {entry.get('course')}")
            st.markdown(f"**Note Globale**: {entry.get('overall')}")
            for q, info in entry.get("feedback", {}).items():
                st.markdown(f"- {q} : {info.get('note')} (Question: {info.get('question')})")
            st.markdown("---")
    else:
        st.info("Aucun feedback enregistré.")

if __name__ == "__main__":
    main()
