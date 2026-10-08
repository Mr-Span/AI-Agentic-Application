from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class Address(BaseModel):
    city: str
    street: str


class UserValidator(BaseModel):
    # Numele trebuie să aibă 2–10 caractere, iar vârsta să fie între 0 și 120.
    name: str = Field(min_length=2, max_length=10)
    age: int = Field(ge=0, le=120, default=18)
    nationality: Literal["Romanian", "Moldovean"] = "Moldovean"
    external: bool | None = None
    address: Address


received_user = {
    "name": "Vicentiu",
    "age": 25,
    "nationality": "Romanian",
    "address": {"city": "Brasso", "street": "Principala"},
}


def function2():
    numar = 10
    numar += 20
    # Am calculat numărul, dar fără return funcția întoarce None.


if __name__ == "__main__":
    try:
        # Cu strict=True, "25" ca text nu este acceptat în loc de numărul 25.
        user = UserValidator.model_validate(received_user, strict=True)
        print(user.name)
        print(user)
    except ValidationError as eroare:
        print(eroare.errors())
    finally:
        print("Am terminat validarea.")
    print(function2())
