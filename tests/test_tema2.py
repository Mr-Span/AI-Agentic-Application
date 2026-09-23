from tema2 import cauta_cuvant


def test_cautare_pytest():
    rezultat = cauta_cuvant()
    assert "pyproject.toml" in rezultat
