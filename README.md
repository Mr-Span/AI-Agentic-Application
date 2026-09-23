# AI Agentic Application

Repository separat pentru temele de la curs. Codul și explicațiile sunt scrise
pentru începători. Proiectul este inițializat cu **uv**, iar testele folosesc **pytest**.

## Tema 1 — Citire JSON și validare Pydantic

Scopul: citim datele unui student cu modulul Python `json`, apoi folosim Pydantic
pentru a verifica numele, vârsta și adresa de email.

Fișierul `student.json` conține:

```json
{
  "nume": "Ana Popescu",
  "varsta": 20,
  "email": "ana.popescu@example.com"
}
```

## Fișierele proiectului

```text
AI-Agentic-Application/
├── student.json          # Datele de intrare
├── tema_1.py             # Citirea și validarea datelor
├── tests/
│   └── test_tema_1.py     # Teste pentru date corecte și erori
├── pyproject.toml        # Configurația proiectului și dependențele
├── uv.lock               # Versiunile exacte ale dependențelor
├── .python-version       # Versiunea Python folosită: 3.12
├── .gitignore            # Fișiere locale care nu se publică
└── README.md             # Ghidul pe care îl citești
```

Temele viitoare pot fi adăugate ca `tema_2.py`, `tema_3.py` și teste separate.

## Instalare și rulare pe Windows

Ai nevoie de Git și uv. Dacă nu ai uv, folosește instrucțiunile oficiale:
[instalare uv](https://docs.astral.sh/uv/getting-started/installation/).
Comanda oficială pentru PowerShell este:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Deschide un terminal nou după instalare, apoi rulează comenzile pe rând:

```powershell
git clone https://github.com/Mr-Span/AI-Agentic-Application.git
cd AI-Agentic-Application
uv sync --locked
uv run python tema_1.py
uv run python -m pytest
```

`uv sync --locked` instalează dependențele din `uv.lock` în mediul local `.venv`.
uv descarcă Python 3.12 dacă nu îl găsește. `uv run` folosește mediul proiectului,
deci nu trebuie să activezi manual `.venv`.

Rezultatul scriptului:

```text
Student validat cu succes:
Nume: Ana Popescu
Varsta: 20
Email: ana.popescu@example.com
```

## Cum funcționează, pas cu pas

1. `Path` reprezintă calea către fișier. În script, calea pornește de la locația
   lui `tema_1.py`, astfel încât JSON-ul să fie găsit și din alt folder.
2. `with cale.open(..., encoding="utf-8")` deschide fișierul și îl închide automat.
3. `json.load(fisier)` transformă textul JSON într-un dicționar Python. Citirea
   JSON-ului nu verifică dacă emailul este valid sau vârsta este pozitivă.
4. `StudentValidator` moștenește `BaseModel`, clasa Pydantic care validează câmpurile.
5. `Student(**date)` trimite valorile dicționarului către model. De exemplu,
   cheia `nume` devine argumentul `nume="Ana Popescu"`.
6. Dacă datele respectă regulile, funcția întoarce un obiect cu atribute precum
   `student.nume`. Altfel, Pydantic ridică `ValidationError`.

Enunțul folosește atât `StudentValidator`, cât și `Student`. Linia
`Student = StudentValidator` definește un alias: cele două nume indică aceeași
clasă. Nu avem două modele diferite.

| Câmp | Regulă | Exemplu respins |
| --- | --- | --- |
| `nume` | Text obligatoriu (`str`) | `123` |
| `varsta` | Întreg obligatoriu, strict mai mare decât 0 | `0`, `-1`, `"20"`, `20.0`, `true` |
| `email` | Adresă cu format valid (`EmailStr`) | `"email-invalid"` |

`gt=0` înseamnă „greater than zero”, adică mai mare decât zero. `strict=True`
împiedică transformarea automată a textului sau altor tipuri în numere întregi.
Toate câmpurile sunt obligatorii deoarece nu au valori implicite.

`EmailStr` folosește pachetul `email-validator`, instalat prin `pydantic[email]`.
Verificarea formatului nu confirmă existența căsuței poștale și nu trimite emailuri.

Blocul `if __name__ == "__main__":` afișează rezultatul doar când rulăm scriptul.
Importarea funcției în teste nu execută acel bloc.

## Ce verifică testele

pytest descoperă fișierele și funcțiile al căror nume începe cu `test_`.
`assert` verifică rezultatul, iar `pytest.raises(...)` verifică o eroare așteptată.
`@pytest.mark.parametrize` rulează aceeași funcție cu mai multe exemple.

- Fișierul real produce un student valid, cu toate cele trei valori așteptate.
- Emailul invalid, vârstele nepermise și numele cu tip greșit sunt respinse.
- Lipsa oricăruia dintre cele trei câmpuri produce o eroare de validare.
- JSON-ul incomplet produce `json.JSONDecodeError`.
- Un fișier inexistent produce `FileNotFoundError`.

Testele pentru erori creează fișiere în `tmp_path`, un folder temporar oferit de
pytest. Fișierul original `student.json` rămâne disponibil pentru tema predată.
Sunt 13 cazuri de test în total. Pentru numele fiecărui caz:

```powershell
uv run python -m pytest -v
```

Funcția nu ascunde excepțiile: apelantul poate vedea dacă problema ține de fișier,
de sintaxa JSON sau de regulile studentului. Dacă modifici temporar emailul în
`student.json` în `"gresit"`, scriptul va afișa un traceback cu `ValidationError`
pentru câmpul `email`. Restabilește datele inițiale înainte de a rula testele.

## Cum a fost inițializat proiectul

Comenzile de mai jos explică procesul de creare; nu trebuie repetate după clonare:

```powershell
uv init AI-Agentic-Application --python 3.12
cd AI-Agentic-Application
uv add "pydantic[email]>=2,<3"
uv add --dev pytest
```

Fișierele demonstrative generate de uv au fost înlocuite cu tema. Proiectul
folosește scripturi simple, fără configurarea unui pachet distribuibil.
`pytest` este o dependență de dezvoltare: îl folosim pentru verificări.
`uv.lock` este inclus în Git; `.venv`, `__pycache__` și `.pytest_cache` sunt excluse.

Documentație: [uv](https://docs.astral.sh/uv/guides/projects/),
[Pydantic](https://docs.pydantic.dev/latest/),
[pytest](https://docs.pytest.org/en/stable/).
