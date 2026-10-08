import re
from pathlib import Path


def imparte_cuvinte(text):
    # Facem literele mici și separăm cuvintele de punctuație.
    # Astfel, Marcus, marcus și marcus, se numără la fel.
    return re.findall(r"\b\w+\b", text.casefold())


def raport_cautare(cuvant, cale=None):
    if not cuvant.strip():
        raise ValueError("Scrie un cuvant de cautat.")
    if cale is None:
        cale = Path(__file__).with_name("paragraphs.txt")
    with open(cale, encoding="utf-8") as fisier:
        cuvinte = imparte_cuvinte(fisier.read())
    # count pe listă numără cuvinte întregi; marcus123 nu intră la marcus.
    aparitii = cuvinte.count(cuvant.strip().casefold())
    return (
        "Word Search Report:\n\n"
        f'Word lookup: "{cuvant}"\n'
        f"Word found : {aparitii} times\n"
        f"File total word count: {len(cuvinte)} words."
    )


if __name__ == "__main__":
    print(raport_cautare("marcus"))
