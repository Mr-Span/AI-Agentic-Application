import os
import sys
from pathlib import Path

import pymupdf
import streamlit as st
from chromadb.errors import NotFoundError
from dotenv import load_dotenv
from openai import APIError, OpenAI
from pydantic import ValidationError

# Streamlit pornește fișierul direct, deci adăugăm rădăcina proiectului.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from proiect_final.agent import INSTRUCTIUNI, IntrebareRAG, raspunde
from proiect_final.indexare import COLECTIE, PROIECT, SURSE, citeste_catalog, conecteaza, incarca_model, indexeaza


@st.cache_resource
def model_local():
    # Modelul rămâne în memorie când apăsăm un buton.
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
    # Nu înlocuim un manual sau un fișier încărcat deja.
    with (SURSE / nume).open("xb") as destinatie:
        destinatie.write(date)
    return nume


def incepe_conversatia(descriere):
    st.session_state.mesaje = [{"role": "system", "content": INSTRUCTIUNI + "\n" + descriere}]


def main():
    st.set_page_config(page_title="Dosarul aparatelor", layout="wide")
    st.html("<style>button {min-height: 44px !important;} .stMainBlockContainer {padding-top: 2rem;}</style>")
    st.title("Dosarul aparatelor")
    st.caption("Manuale și garanții, într-un singur loc. Încarcă, indexează și întreabă.")
    catalog = citeste_catalog()
    baza, collection, problema = None, None, None
    try:
        baza = conecteaza()
        collection = baza.get_collection(COLECTIE, embedding_function=None)
    except NotFoundError:
        pass  # Prima indexare va crea colecția.
    except ConnectionError as eroare:
        problema = str(eroare)
    except Exception:
        problema = "Nu pot citi indexul. Verifică serverul Chroma și reîncarcă pagina."

    biblioteca, chat = st.columns([1, 1.5], gap="large")
    with biblioteca:
        st.header("Biblioteca de documente")
        with st.expander("Încarcă documente"):
            fisiere_noi = st.file_uploader("Fișiere PDF sau TXT", type=["pdf", "txt"], accept_multiple_files=True)
            if st.button("Salvează fișierele", disabled=not fisiere_noi, width="stretch"):
                for fisier in fisiere_noi:
                    try:
                        nume = salveaza(fisier)
                        st.success(f"Salvat: {nume}. Apasă «Indexează documentele».")
                    except FileExistsError:
                        st.warning(f"{fisier.name}: există deja. Redenumește fișierul nou.")
                    except (ValueError, OSError, RuntimeError):
                        st.error(f"{fisier.name}: nu pot salva fișierul. Verifică formatul PDF/TXT, codarea UTF-8 și limita de 50 MB.")

        if problema:
            st.warning(problema)
            st.code("uv run --extra semantic-search chroma run --path proiect_final/chroma_data --port 8000", language="powershell")
        if st.button("Indexează documentele", type="primary", disabled=baza is None, width="stretch"):
            try:
                with st.spinner("Indexez documentele. Prima rulare poate dura câteva minute."):
                    model = model_local()
                    collection = baza.get_or_create_collection(
                        COLECTIE, embedding_function=None, configuration={"hnsw": {"space": "cosine"}},
                    )
                    total = indexeaza(collection, model)
                st.session_state.pop("selectie", None)
                st.success(f"Indexare terminată: {total} fragmente.")
            except Exception:
                st.error("Indexarea nu s-a terminat. Verifică documentele și serverul Chroma, apoi încearcă din nou.")
                collection = None

        fisiere = sorted(cale for cale in SURSE.glob("*") if cale.is_file() and cale.suffix.lower() in {".pdf", ".txt"})
        surse_indexate = set()
        try:
            if collection is not None:
                surse_indexate = {meta["source"] for meta in collection.get(include=["metadatas"])["metadatas"]}
        except Exception:
            st.warning("Nu pot verifica starea indexului. Reîncarcă pagina după pornirea serverului.")
        stare_index = f"{len(surse_indexate)} surse indexate" if problema is None else "index indisponibil"
        st.caption(f"{len(fisiere)} documente · {stare_index}")
        if fisiere:
            st.dataframe([
                {"Document": cale.name, "Mărime": f"{cale.stat().st_size / 1024:.0f} KB",
                 "Stare": "Neverificat" if problema else "Indexat" if cale.name in surse_indexate else "De indexat"}
                for cale in fisiere
            ], hide_index=True, width="stretch", height=350)
            with st.expander("Deschide un document"):
                ales = st.selectbox("Document de descărcat", fisiere, format_func=lambda cale: cale.name)
                st.download_button("Descarcă documentul", ales.read_bytes(), file_name=ales.name, width="stretch")
        else:
            st.info("Biblioteca este goală. Încarcă documente sau descarcă exemplele din catalog.")
        st.caption("PDF-urile scanate ca imagini au nevoie de OCR. Reindexarea reface indexul tuturor documentelor.")

    with chat:
        st.header("Întreabă documentele")
        aparat = st.selectbox("Unde căutăm?", [None] + catalog["aparate"],
            format_func=lambda a: "Documente alese din bibliotecă" if a is None else f"{a['categorie']} · {a['model']}")
        nume_documente = {d["id"]: d["fisier"] for d in catalog["documente"]}
        if aparat:
            surse = [nume_documente[aparat["manual"]], nume_documente[aparat["garantie"]]]
            descriere = f"Aparatul ales: {aparat['categorie']}, {aparat['producator']}, {aparat['model']}. Piața: România."
            for camp in ("model_alias", "familie", "note"):
                if aparat.get(camp):
                    descriere += f" {camp}: {aparat[camp]}."
            st.caption("Caut în manualul și garanția acestui aparat.")
        else:
            surse = st.multiselect("Documente pentru întrebare", [cale.name for cale in fisiere],
                placeholder="Alege documentele...",
                help="Alege documentele aparatului despre care întrebi, inclusiv fișierele încărcate de tine.")
            descriere = "Folosește doar documentele selectate. Nu aplica automat condițiile unui aparat altui model. Piața: România."

        selectie = (aparat["id"] if aparat else "documente", tuple(surse))
        if st.session_state.get("selectie") != selectie:
            incepe_conversatia(descriere)
            st.session_state.selectie = selectie
        if st.button("Conversație nouă"):
            incepe_conversatia(descriere)

        # În chat arătăm doar întrebările și răspunsurile, fără mesajele uneltei.
        istoric = st.container(height=320)
        with istoric:
            for mesaj in st.session_state.mesaje:
                if mesaj["role"] in {"user", "assistant"} and mesaj.get("content"):
                    with st.chat_message(mesaj["role"]):
                        st.markdown(mesaj["content"])
            if len(st.session_state.mesaje) == 1:
                st.info("Alege un aparat sau documentele din bibliotecă, apoi scrie întrebarea.")

        pregatit = bool(surse) and all(nume in surse_indexate for nume in surse)
        if surse and not pregatit:
            st.info("Indexează mai întâi documentele selectate.")
        with st.form("intrebare", clear_on_submit=False):
            text = st.text_input("Întrebarea ta", placeholder="Ce documente sunt necesare pentru garanție?")
            trimite = st.form_submit_button("Întreabă", type="primary", disabled=not pregatit, width="stretch")
        if trimite:
            try:
                intrebare = IntrebareRAG(question=text)
                load_dotenv(PROIECT / ".env")
                cheie = os.getenv("API_KEY") or os.getenv("OPEN_ROUTER_API_KEY")
                if not cheie:
                    st.error("Completează API_KEY în fișierul .env al proiectului.")
                    return
                model_llm = os.getenv("MODEL") or os.getenv("OPEN_ROUTER_MODEL_NAME") or "cohere/north-mini-code:free"
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=cheie, timeout=60, max_retries=0)
                # Copia păstrează conversația intactă dacă serviciul nu răspunde.
                mesaje = st.session_state.mesaje + [{"role": "user", "content": intrebare.question}]
                with st.spinner("Caut în documente și pregătesc răspunsul..."):
                    raspunde(client, model_llm, mesaje, collection, model_local(), surse)
                st.session_state.mesaje = mesaje
                st.rerun()
            except ValidationError:
                st.error("Scrie o întrebare care să nu fie goală.")
            except APIError as eroare:
                st.error(f"OpenRouter: {type(eroare).__name__}. Verifică cheia, modelul și creditul.")
            except Exception:
                st.error("Nu pot obține răspunsul. Verifică serverul Chroma și modelul ales, apoi încearcă din nou.")
        st.caption("Răspunsul include fișierul și pagina. Verifică pasajul citat. Fragmentele găsite sunt trimise către OpenRouter.")


if __name__ == "__main__":
    main()
