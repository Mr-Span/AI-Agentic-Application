# Exemple de la curs: variabile, liste, funcții și bucle.


def add(a, b):
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b


if __name__ == "__main__":
    var1 = 10
    var1 = var1 + 30
    print(var1 + 60)

    # Primul element e la poziția 0. În listă pot pune și numere, și texte.
    arr = [30, 40, 100, 99, -1, "Harry Potter"]
    print(arr[0])
    print(arr)
    user = {"name": "Adrian", "age": 33}
    print(user["name"])
    print(add(4, 10))
    print(multiply(2, 5))
    print("hello" + "world")

    # int = întreg, float = zecimal, bool = True/False, str = text.
    offer_letter = True
    if offer_letter:
        print("Am primit oferta.")
    else:
        print("Inca astept oferta.")

    # range(10) dă numerele de la 0 la 9; 10 nu intră în interval.
    for i in range(10):
        print(i)
    for numar in [10, 20, 33]:
        print(numar)

    i = 0
    while i <= 30:
        print(i)
        i += 1

    # Scriu q ca să ies. Orice alt mesaj este afișat înapoi.
    while True:
        mesaj = input("tu> ")
        if mesaj == "q":
            break
        print(mesaj)
