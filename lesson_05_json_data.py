import json
from pathlib import Path

from lesson_03_data_validation import UserValidator


def citeste_user(cale):
    with open(cale, encoding="utf-8") as fisier:
        # load citește JSON-ul din fișier; loads ar citi dintr-un text deja încărcat.
        date = json.load(fisier)
    return UserValidator.model_validate(date, strict=True)


if __name__ == "__main__":
    cale = Path(__file__).with_name("user_data.json")
    print(citeste_user(cale))
