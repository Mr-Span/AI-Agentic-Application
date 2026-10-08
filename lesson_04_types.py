if __name__ == "__main__":
    nume = "Vicentiu"
    varsta = 25
    print(type(nume))
    print(type(varsta))

    # type îmi arată tipul. Cu isinstance întreb dacă valoarea are acel tip.
    if isinstance(nume, str):
        print("Numele este un text.")

    # : int este un indiciu pentru editor; singur nu verifică valoarea la rulare.
    numar: int = 10
    print(numar)
