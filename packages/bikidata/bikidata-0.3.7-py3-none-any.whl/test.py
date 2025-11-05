import bikidata
import pytest


def test_build():
    d = bikidata.build(["starwars-data.nt.gz"])
    assert d is not None


if __name__ == "__main__":
    pytest.main()
