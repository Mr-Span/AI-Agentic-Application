import json
import sys
from pathlib import Path

from pydantic import BaseModel, EmailStr, Field


class StudentValidator(BaseModel):
    nume: str
    varsta: int = Field(gt=0, strict=True)  # Acceptăm doar numere întregi pozitive.
    email: EmailStr


Student = StudentValidator  # În enunț, aceeași clasă apare sub ambele nume.


def citeste_student(cale: Path) -> StudentValidator:
    with cale.open(encoding="utf-8") as fisier:
        date = json.load(fisier)
    return Student(**date)  # **date trimite separat câmpurile dicționarului la validare.


if __name__ == "__main__":
    # Dacă dau un fișier în comandă, îl citesc pe acela. Altfel folosesc student.json.
    cale = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("student.json")
    student = citeste_student(cale)
    print(f"{student.nume}, {student.varsta} ani, {student.email}")
