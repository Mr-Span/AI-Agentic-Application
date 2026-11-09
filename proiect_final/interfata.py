import os
import sys
from pathlib import Path

import pymupdf
import streamlit as st
from chromadb.errors import NotFoundError
from dotenv import load_dotenv
from openai import APIError, OpenAI
from pydantic import ValidationError

# Streamlit pornește fișierul direct.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proiect_final.agent import INSTRUCTIUNI, IntrebareRAG, raspunde
from proiect_final.indexare import COLECTIE, PROIECT, SURSE, citeste_catalog, conecteaza, incarca_model, indexeaza


@st.cache_resource
def model_local():
    # Nu încărcăm modelul din nou la fiecare întrebare.
    return incarca_model()


def salveaza(fisier):
    nume = Path(fisier.name).name
    if not nume or any(semn in nume for semn in '<>:"/\\|?*') or nume.endswith((" ", ".")):
        raise ValueError("Numele fișierului nu este valid.")
    date = fisier.getvalue()
    if not date or len(date) > 50 * 1024 * 1024:
        raise ValueError("Alege un fișier nevid, de cel mult 50 MB.")
    extensie = Path(nume).suffix.lower()
    if extensie == ".txt":
        if not date.decode("utf-8-sig").strip():
            raise ValueError("Fișierul TXT nu conține text.")
    elif extensie == ".pdf":
        with pymupdf.open(stream=date, filetype="pdf") as pdf:
            if pdf.needs_pass or not pdf.page_count:
                raise ValueError("PDF-ul este gol sau protejat cu parolă.")
    else:
        raise ValueError("Sunt acceptate doar fișiere PDF și TXT.")
    SURSE.mkdir(parents=True, exist_ok=True)
    # Păstrăm fișierele existente.
    with (SURSE / nume).open("xb") as destinatie:
        destinatie.write(date)
    return nume


def main():
    st.set_page_config(page_title="Manuale și garanții")
    st.title("Manuale și garanții")
    baza, collection = None, None
    try:
        baza = conecteaza()
        collection = baza.get_collection(COLECTIE, embedding_function=None)
    except NotFoundError:
        pass  # Colecția se creează la prima indexare.
    except ConnectionError:
        st.error("Serverul Chroma nu este pornit pe portul 8000.")

    with st.sidebar:
        st.header("Documente")
        fisiere_noi = st.file_uploader("Încarcă PDF sau TXT", type=["pdf", "txt"], accept_multiple_files=True)
        if st.button("Salvează", disabled=not fisiere_noi):
            for fisier in fisiere_noi:
                try:
                    st.success(f"Salvat: {salveaza(fisier)}")
                except FileExistsError:
                    st.warning(f"{fisier.name}: există deja.")
                except (ValueError, OSError, RuntimeError):
                    st.error(f"{fisier.name}: fișier invalid (PDF/TXT UTF-8, maximum 50 MB).")

        if st.button("Indexează", disabled=baza is None):
            try:
                with st.spinner("Indexez..."):
                    model = model_local()
                    collection = baza.get_or_create_collection(
                        COLECTIE, embedding_function=None, configuration={"hnsw": {"space": "cosine"}},
                    )
                    total = indexeaza(collection, model)
                st.session_state.pop("aparat_chat", None)
                st.success(f"{total} fragmente indexate.")
            except Exception:
                collection = None
                st.error("Indexarea a eșuat. Verifică serverul și documentele.")

        fisiere = sorted(cale for cale in SURSE.glob("*") if cale.is_file() and cale.suffix.lower() in {".pdf", ".txt"})
        with st.expander(f"Fișiere ({len(fisiere)})"):
            for cale in fisiere:
                st.download_button(cale.name, cale.read_bytes(), file_name=cale.name, key=cale.name)

    aparat = st.selectbox("Electrocasnic", citeste_catalog()["aparate"],
        format_func=lambda a: f"{a['categorie']} — {a['producator']} {a['model']}")
    if st.session_state.get("aparat_chat") != aparat["id"]:
        descriere = f"Aparatul ales: {aparat['categorie']}, {aparat['producator']}, model {aparat['model']}. Piața: România."
        for camp in ("model_alias", "familie", "note"):
            if aparat.get(camp):
                descriere += f" {camp}: {aparat[camp]}."
        descriere += " Caută în toate documentele. Include producătorul și modelul aparatului în întrebarea trimisă la rag_search. Nu aplica acestui aparat condițiile altui producător sau model."
        st.session_state.mesaje = [{"role": "system", "content": INSTRUCTIUNI + "\n" + descriere}]
        st.session_state.aparat_chat = aparat["id"]
    if st.button("Șterge chatul"):
        st.session_state.mesaje = st.session_state.mesaje[:1]

    pregatit = False
    if collection is not None:
        try:
            pregatit = collection.count() > 0
        except Exception:
            st.error("Nu pot citi indexul Chroma. Reîncarcă pagina după pornirea serverului.")
    if baza is not None and not pregatit:
        st.warning("Indexează documentele.")

    with st.form("intrebare"):
        text = st.text_input("Întrebare")
        trimite = st.form_submit_button("Întreabă", disabled=not pregatit)
    if trimite:
        try:
            intrebare = IntrebareRAG(question=text)
            load_dotenv(PROIECT / ".env")
            cheie = os.getenv("API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
            if not cheie:
                st.error("Lipsește API_KEY din .env.")
                return
            model_llm = os.getenv("MODEL") or os.getenv("OPEN_ROUTER_MODEL_NAME") or "cohere/north-mini-code:free"
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=cheie, timeout=60, max_retries=0)
            mesaje = st.session_state.mesaje + [{"role": "user", "content": intrebare.question}]
            with st.spinner("Caut..."):
                # Fără filtru de fișier: căutăm în întreaga colecție.
                raspunde(client, model_llm, mesaje, collection, model_local())
            st.session_state.mesaje = mesaje
        except ValidationError:
            st.error("Scrie o întrebare.")
        except APIError as eroare:
            st.error(f"OpenRouter: {type(eroare).__name__}. Verifică cheia, modelul și creditul.")
        except ValueError as eroare:
            st.error(str(eroare))
        except Exception:
            st.error("Căutarea a eșuat. Verifică serverul Chroma și conexiunea.")

    for mesaj in st.session_state.mesaje:
        if mesaj["role"] in {"user", "assistant"} and mesaj.get("content") and not mesaj.get("tool_calls"):
            with st.chat_message(mesaj["role"]):
                st.markdown(mesaj["content"])


if __name__ == "__main__":
    main()
