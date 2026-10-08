import re
from pathlib import Path


def find_exact_word_in_file(file_path, target_word):
    # \b cere un cuvânt întreg. escape tratează semnele căutate ca text obișnuit.
    pattern = rf"\b{re.escape(target_word)}\b"
    with open(file_path, encoding="utf-8") as fisier:
        for linie in fisier:
            if re.search(pattern, linie, re.IGNORECASE):
                print(linie.strip())


if __name__ == "__main__":
    find_exact_word_in_file(Path(__file__).with_name("paragraphs.txt"), "marcus")
