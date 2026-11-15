import json,sys
d=json.load(open('abstracts.json'))
T=sys.argv[1:]
for p,v in d.items():
    if v['topic'] in T:
        print(f"=== {p} | {v['first']} | {v['journal']} {v['year']} | {v['title']}\n{v['abstract']}\n")
