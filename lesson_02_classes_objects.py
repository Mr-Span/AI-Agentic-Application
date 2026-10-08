import json


class User:
    def __init__(self, name, age):
        # self este obiectul de acum: de exemplu, Sonia sau Dragoș.
        self.name = name
        self.age = age
        self.nationality = "Romanian"

    def say_hello(self):
        print(f"Salut, sunt {self.name}!")

    def return_attrs(self):
        return f"{self.name} {self.age}, {self.nationality}"

    def __str__(self):
        # Așa îi spun lui Python ce să afișeze când scriu print(obiect).
        return self.return_attrs()

    def to_json(self):
        date = {"name": self.name, "age": self.age, "nationality": self.nationality}
        # dumps transformă dicționarul într-un text JSON.
        return json.dumps(date)


if __name__ == "__main__":
    sonia = User("Sonia", 30)
    dragos = User("Dragos", 35)
    dragos.age = 40
    dragos.hobby = "Warhammer 40k"
    print(sonia)
    print(dragos.return_attrs())
    sonia.say_hello()
    print(dragos.hobby)
    print(dragos.to_json())

    # Într-un set, 40 apare o singură dată, chiar dacă îl adaug de două ori.
    print(set([10, 30, 40, 40]))
    date = json.loads('{"name": "Jason", "age": 25}')
    print(date["name"])
