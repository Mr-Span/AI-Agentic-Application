import sys
from pathlib import Path


if __name__ == "__main__":
    # Pe Windows, UTF-8 ne lasă să afișăm și diacriticele din fișierul citit.
    sys.stdout.reconfigure(encoding="utf-8")
    mesaj = "LLM Agents are agents that usually process strings as tokens."
    print("Numar de caractere:", len(mesaj))
    print("Al cincilea caracter de la final:", mesaj[-5])
    # in dă True sau False; find dă poziția primei apariții, ori -1 dacă lipsește.
    print("Exista ken in mesaj?", "ken" in mesaj)
    print("Pozitia lui tok:", mesaj.find("tok"))
    print("Primele 10 caractere:", mesaj[:10])

    # lower() face un text nou cu litere mici. Mesajul inițial rămâne la fel.
    print("Cu litere mici:", mesaj.lower())
    print("Mesajul initial:", mesaj)
    numere = [3, 10, 20]
    numere[0] = 300  # În listă pot înlocui direct un element.
    print(numere)

    # split() rupe textul după spații; join() lipește elementele cu separatorul ales.
    cuvinte = mesaj.split()
    print("Cuvintele separate:", cuvinte)
    print("Cuvintele lipite cu -:", "-".join(cuvinte))
    print("Aparitii pentru agents:", mesaj.lower().count("agents"))

    cale = Path(__file__).with_name("lesson_05_json_data.py")
    with open(cale, encoding="utf-8") as fisier:
        continut = fisier.read()
    print(continut)
    print(f"Fisierul are {len(continut)} caractere.")
    print(f"Textul json apare de {continut.lower().count('json')} ori.")
