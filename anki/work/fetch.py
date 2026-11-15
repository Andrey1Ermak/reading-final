import subprocess,json,re,time,xml.etree.ElementTree as ET
ids=[];topic={}
for l in open('pmids.txt'):
    p=l.split()
    for i in p[1:]:
        if i not in topic: ids.append(i); topic[i]=p[0]
out={}
for k in range(0,len(ids),40):
    chunk=ids[k:k+40]
    x=subprocess.run(["curl","-s","https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id="+",".join(chunk)],capture_output=True).stdout
    root=ET.fromstring(x)
    for a in root.findall('.//PubmedArticle'):
        pmid=a.findtext('.//PMID')
        art=a.find('.//Article')
        title="".join(art.find('ArticleTitle').itertext())
        ab="\n".join(((t.get('Label')+': ') if t.get('Label') else '')+"".join(t.itertext()) for t in art.findall('.//AbstractText'))
        auths=art.findall('.//Author')
        fa=(auths[0].findtext('LastName') or auths[0].findtext('CollectiveName') or '?') if auths else '?'
        ini=(auths[0].findtext('Initials') or '') if auths else ''
        j=a.findtext('.//Journal/ISOAbbreviation')
        y=a.findtext('.//JournalIssue/PubDate/Year') or (a.findtext('.//JournalIssue/PubDate/MedlineDate') or '')[:4]
        doi=None
        for e in a.findall('PubmedData/ArticleIdList/ArticleId'):  # not './/': that also matches the reference list
            if e.get('IdType')=='doi': doi=e.text
        out[pmid]=dict(pmid=pmid,topic=topic[pmid],title=title,first=f"{fa} {ini}".strip(),etal=len(auths)>1,journal=j,year=y,doi=doi,abstract=ab)
    time.sleep(0.5)
json.dump(out,open('abstracts.json','w'),indent=1,ensure_ascii=False)
missing=[i for i in ids if i not in out]
print(len(out),"fetched; missing:",missing)
for i in ids:
    if i in out and len(out[i]['abstract'])<200: print("short abstract:",i,out[i]['title'][:80])
