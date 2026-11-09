"""Descarcare o singura data a documentelor publice din catalog."""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

import pymupdf

FOLDER = Path(__file__).resolve().parent
DOCUMENTE = FOLDER / "documente"


class TextDinPagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignora = 0
        self.in_main = False
        self.text = []
        self.text_main = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "head"}:
            self.ignora += 1
        if tag == "main":
            self.in_main = True
        if tag in {"p", "li", "div", "h1", "h2", "h3", "section", "br"}:
            self.text.append("\n")
            if self.in_main:
                self.text_main.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "head"}:
            self.ignora = max(0, self.ignora - 1)
        if tag == "main":
            self.in_main = False

    def handle_data(self, data):
        if not self.ignora and data.strip():
            self.text.append(data.strip() + " ")
            if self.in_main:
                self.text_main.append(data.strip() + " ")


def descarca(document):
    cale = DOCUMENTE / document["fisier"]
    if cale.exists():
        return cale
    with urlopen(document["url"], timeout=90) as raspuns:
        continut = raspuns.read()
        url_final = raspuns.url
    if document.get("format_sursa") == "html":
        parser = TextDinPagina()
        parser.feed(continut.decode("utf-8"))
        text = "".join(parser.text_main or parser.text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        if len(text) < 500 or "garan" not in text.lower():
            raise ValueError("Pagina nu contine textul conditiilor de garantie.")
        antet = f"Sursa: {url_final}\nPiata: Romania\nVerificat: 2026-11-09\nFormat original: HTML\n\n"
        continut = (antet + text).encode("utf-8")
    else:
        if not continut.startswith(b"%PDF"):
            raise ValueError("Serverul nu a returnat un PDF.")
    # Salvăm doar după primirea completă a documentului.
    cale.write_bytes(continut)
    return cale


def verifica(cale, document):
    continut = cale.read_bytes()
    if cale.suffix == ".pdf":
        with pymupdf.open(cale) as pdf:
            pagini = [p.get_text() for p in pdf]
            if pdf.is_encrypted or not pagini or sum(len(p.strip()) for p in pagini) < 500:
                raise ValueError("PDF-ul nu are suficient text extractibil pentru RAG.")
    else:
        pagini = [continut.decode("utf-8")]
    text = "\n".join(pagini)
    marker = document.get("dovada_model", "")
    if marker and marker not in text:
        raise ValueError(f"Familia/modelul {marker} nu apare in textul manualului.")
    amprenta = hashlib.sha256(continut).hexdigest()
    if document.get("sha256") and amprenta != document["sha256"]:
        raise ValueError("Documentul s-a schimbat fata de versiunea verificata. Verifica din nou catalogul.")
    return {
        "id": document["id"], "fisier": cale.name, "url": document["url"],
        "octeti": len(continut), "sha256": amprenta,
        "pagini": len(pagini), "pagini_cu_text": sum(bool(p.strip()) for p in pagini),
        "caractere": len(text),
        "marker_model_in_text": marker in text if marker else None,
    }


def main():
    catalog = json.loads((FOLDER / "catalog.json").read_text(encoding="utf-8"))
    DOCUMENTE.mkdir(exist_ok=True)
    rezultate = []
    erori = []
    for document in catalog["documente"]:
        try:
            cale = descarca(document)
            rezultat = verifica(cale, document)
            rezultate.append(rezultat)
            print(f"OK {cale.name}: {rezultat['pagini']} pagini, {rezultat['caractere']} caractere", flush=True)
        except (OSError, ValueError, RuntimeError) as eroare:
            erori.append({"id": document["id"], "eroare": str(eroare)})
            print(f"EROARE {document['id']}: {eroare}", flush=True)
    raport = {"verificat_la": catalog["verificat_la"], "documente": rezultate, "erori": erori}
    (FOLDER / "verificare_locala.json").write_text(json.dumps(raport, ensure_ascii=False, indent=2), encoding="utf-8")
    if erori:
        raise SystemExit("Unele documente nu au fost descarcate sau validate. Vezi verificare_locala.json.")
    print(f"Gata: {len(catalog['aparate'])} aparate, {len(rezultate)} documente unice.")


if __name__ == "__main__":
    main()
