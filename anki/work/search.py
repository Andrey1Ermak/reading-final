import json,sys,time,urllib.request,urllib.parse
E="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
def get(u):
    import subprocess
    for i in range(4):
        r=subprocess.run(["curl","-s","--max-time","30",u],capture_output=True)
        if r.returncode==0 and r.stdout.strip().startswith(b"{"): return r.stdout
        time.sleep(2)
    return b'{"esearchresult":{"idlist":[]}}' 
def search(q,n=3):
    r=json.loads(get(E+"esearch.fcgi?db=pubmed&retmode=json&retmax=%d&term="%n+urllib.parse.quote(q)))
    ids=r["esearchresult"]["idlist"]
    if not ids: return []
    s=json.loads(get(E+"esummary.fcgi?db=pubmed&retmode=json&id="+",".join(ids)))["result"]
    return [(i,s[i]["pubdate"][:4],s[i]["source"],(s[i]["authors"] or [{"name":"?"}])[0]["name"],s[i]["title"][:150]) for i in ids]
for line in open(sys.argv[1]):
    if "|" not in line: continue
    k,q=line.strip().split("|",1)
    res=search(q)
    print(f"## {k}  [{q}]")
    for r in res: print("   ",*r,sep=" | ")
    if not res: print("    NONE")
    time.sleep(0.4)
