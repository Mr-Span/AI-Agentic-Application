# Continuăm prima temă și păstrăm doar fragmentele suficient de apropiate.
from tema_3_1 import afiseaza_raspuns, cauta, cere_intrebare, pregateste

DISTANTA_MAXIMA = 0.5


def filtreaza_distanta(rezultate):
    # Distanța mai mică este mai bună. Valoarea 0.5 este încă acceptată.
    return [rezultat for rezultat in rezultate if rezultat["distance"] <= DISTANTA_MAXIMA]


def main():
    collection, model, client = pregateste()
    while True:
        cerere = cere_intrebare()
        if cerere is None:
            break
        sursa, intrebare = cerere
        rezultate = cauta(collection, model, sursa, intrebare)
        rezultate = filtreaza_distanta(rezultate)
        afiseaza_raspuns(client, intrebare, rezultate)


if __name__ == "__main__":
    main()
