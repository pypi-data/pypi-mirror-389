import bikidata

r = bikidata.query(
    {
        "filters": [{"p": "<https://nfdi4culture.de/ontology/CTO_0001007> 1"}],
        "size": 10,
    }
)

print(r["total"])

print(r["results"].keys())
print("#" * 80)

r = bikidata.query(
    {
        "filters": [{"p": "<https://nfdi4culture.de/ontology/CTO_0001007>"}],
        "size": 10,
    }
)

print(r["total"])

print(r["results"].keys())
