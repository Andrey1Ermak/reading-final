"""Add one PubMed record to work/abstracts.json (used by the daily task, which cannot reach NCBI from the shell).

Usage: python3 work/add_abstract.py record.json
record.json: {"pmid","title","first","etal","journal","year","doi","abstract","topic"}
  first   = first author as on PubMed, e.g. "Schwimmer JB"
  etal    = true if more than one author
  journal = NLM ISO abbreviation, e.g. "Hepatology", "J Pediatr Gastroenterol Nutr"
Refuses to overwrite an existing PMID and refuses records with a short/missing abstract.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(HERE, "abstracts.json")
rec = json.load(open(sys.argv[1]))
need = ["pmid", "title", "first", "etal", "journal", "year", "abstract"]
miss = [k for k in need if rec.get(k) in (None, "")]
if miss:
    sys.exit(f"missing fields: {miss}")
if len(rec["abstract"]) < 400:
    sys.exit("abstract too short — do not add a study without its full abstract")
data = json.load(open(path))
if rec["pmid"] in data:
    sys.exit(f"PMID {rec['pmid']} already present")
rec.setdefault("doi", None)
rec.setdefault("topic", "added")
rec["etal"] = bool(rec["etal"])
rec["source"] = "pubmed-webfetch"
data[rec["pmid"]] = rec
json.dump(data, open(path, "w"), indent=1, ensure_ascii=False)
print("added", rec["pmid"], rec["first"], rec["journal"], rec["year"])
