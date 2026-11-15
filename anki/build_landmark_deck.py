"""Pediatric Hepatology — Landmark Studies (Anki deck builder), organised by the 26 blocks of Hepatology_Year_Plan.docx.

One fact per card: Question → one-line answer (work/answers.py), Key number (work/stats.py),
and Named trial → finding (NAMED in work/answers.py). Design/Result/citation sit under a folded "Details".

Every card is written from the PubMed abstract of the cited paper (work/abstracts.json,
fetched via NCBI E-utilities). Card text lives in work/cards_*.py; citation metadata
(authors, journal, year, DOI) is taken from PubMed, not typed by hand.

Build:  <venv>/bin/python build_landmark_deck.py      (needs: pip install genanki)
Output: Pediatric_Hepatology_Landmark_Studies.apkg + Pediatric_Hepatology_Landmark_Studies_index.csv

Note GUIDs are derived from PMID, so re-importing an updated deck keeps review history.

Daily growth (see DAILY.md):
  work/new_studies.py      NEW   — recently published studies; each dict carries its own answer/stat/named/added.
  work/extra_questions.py  EXTRA — extra Question → Answer notes on studies already in the deck
                                   (GUID = PMID + key, so each one keeps its own review history).
  Both are tagged added::YYYY-MM-DD; CHANGELOG.md is regenerated on every build.
"""
import csv
import glob
import hashlib
import html
import importlib.util
import json
import os
import re

import genanki

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
ROOT_DECK = "Pediatric Hepatology — Landmark Studies"
MODEL_ID = 1607392320

BLOCKS = {  # year-plan block number -> English sub-deck title
    1: "Hepatology toolkit", 2: "Neonatal cholestasis", 3: "Biliary atresia",
    4: "Alagille syndrome & ductopenia", 5: "PFIC & genetic cholestasis",
    6: "Alpha-1 antitrypsin deficiency", 7: "Wilson disease", 8: "Autoimmune hepatitis",
    9: "PSC & sclerosing cholangitis", 10: "Hepatitis B & D", 11: "Hepatitis C, E & other infections",
    12: "Pediatric acute liver failure", 13: "Drug-induced liver injury", 14: "Portal hypertension",
    15: "Complications of cirrhosis", 16: "Pediatric MASLD", 17: "Metabolic liver disease",
    18: "CF & fibrocystic liver disease", 19: "Intestinal failure, nutrition & gallbladder",
    20: "Vascular liver disease", 21: "Liver tumors", 22: "Liver transplant I — evaluation & surgery",
    23: "Liver transplant II — immunology", 24: "Liver transplant III — complications & outcomes",
    25: "Liver in systemic disease", 26: "Cross-cutting topics",
}
SECTIONS = [  # (first block, last block, label, css class)
    (1, 9, "Cholestasis, genetic & autoimmune", "hep"),
    (10, 13, "Infection, ALF & DILI", "inf"),
    (14, 21, "Portal hypertension, metabolic & vascular", "gi"),
    (22, 24, "Transplantation", "tx"),
    (25, 26, "Systemic & cross-cutting", "sys"),
]


def block_of(deck_field):
    return int(deck_field.split()[0])


def section_of(n):
    for a, b, label, cls in SECTIONS:
        if a <= n <= b:
            return label, cls
    raise ValueError(n)


def stable_id(s):
    return int(hashlib.sha1(s.encode()).hexdigest()[:8], 16)


def safe_html(s):
    """Escape '<' that is not part of our <b>…</b> markup (e.g. '<2 mg/dL')."""
    return re.sub(r"<(?!/?b>)", "&lt;", s)


# Population and design labels that the free-text tags don't capture reliably.
ADULT = set("""18798336 25754159 20728932 20600032 36183738 37345876 38842520 35748699 38964420
18537184 22989569 38101756 28529147 18820647 38324483 40305708 38856224 19483685 28043905 35014066
33657293 18644373 29861076 20335583 33657294 10432325 17854593 30910320 20573925 39181213 22819864
22396517 23389867 32286644 11910339 15368452 31378395 16496320 31121167 32376409 19585548 8594428
2490426 19524577 26325537 35471153 28988934 18287603 24645943 37364790""".split())
MIXED = set("""27305192 29514030 24928290 21185835 16234011 24356057 21038416 37001534 26825712
14966415 28891588 27062904 32919899 32521132 26352813 34774639 11313315 22364685 20232290
24578576 16937360 31726116 42263796 19759364 19738092 14993126""".split())
NO_POP = {"37585628", "27273869", "24614073"}  # abstract does not state the age group
DESIGN = {  # pmid -> label overriding the tag-derived one
    **{p: "Consensus" for p in "37364790 27273869 31497926 16937360 27884679".split()},
    **{p: "Case series" for p in "19797282 20601902 21616259 24645943 18287603 11910339 38733639 10512405".split()},
    **{p: "Genetic study" for p in "19483685 28043905 18820647 24614073 24578576 19738092 21038416 36996872 36996873 29167395".split()},
    **{p: "Meta-analysis" for p in "32901449 26589959 27010179 41405291 28891588 24928290 32592699".split()},
}


ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def badges(tags, pmid=""):
    """Verdict-style chips, same palette as the serif guideline decks."""
    t = set(tags.split())
    out = []
    if pmid in DESIGN:
        label = DESIGN[pmid]
        out.append((label, "c-green" if label == "Meta-analysis" else "c-slate" if label in ("Consensus", "Case series") else "c-steel"))
    elif t & {"consensus", "guideline"}:
        out.append(("Consensus", "c-slate"))
    elif "meta" in t:
        out.append(("Meta-analysis", "c-green"))
    elif "rct" in t:
        out.append(("RCT", "c-navy"))
    elif "trial" in t or "ibat" in t or "daa" in t or "sirna" in t:
        out.append(("Trial", "c-navy"))
    else:
        out.append(("Cohort", "c-steel"))
    if pmid in NO_POP:
        pass
    elif pmid in ADULT or "adult" in t:
        out.append(("Adult data", "c-grey"))
    elif pmid in MIXED or "mixed" in t:
        out.append(("Children + adults", "c-yellow"))
    else:
        out.append(("Paediatric", "c-pale"))
    if "harm" in t:
        out.append(("Harm signal", "c-red"))
    elif "negative" in t:
        out.append(("Negative", "c-amber"))
    return "".join(f'<span class="chip {c}">{n}</span>' for n, c in out)


def key_stat(result_html):
    """First short bold figure in the result -> (value, caption) for a stat card, else ('', '')."""
    for sent in re.split(r"(?<=[.!?])\s+", result_html):
        m = re.search(r"<b>(.*?)</b>", sent)
        if not m:
            continue
        val = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if len(val) > 18 or not re.search(r"\d", val):
            continue
        before = re.sub(r"<[^>]+>", "", sent[:m.start()]).strip(" :;,(—-")
        after = re.sub(r"<[^>]+>", "", sent[m.end():]).strip(" :;,.)—-")
        cap = before if len(before) >= 8 else after
        cap = cap[:90].rsplit(" ", 1)[0] + "…" if len(cap) > 90 else cap
        if cap:
            return val, cap
    return "", ""


def stat_for(c):
    """Curated headline figure (work/stats.py); value size class is chosen by length."""
    from importlib.machinery import SourceFileLoader
    global _STATS
    if "_STATS" not in globals():
        _STATS = SourceFileLoader("stats", os.path.join(WORK, "stats.py")).load_module().STATS
    v, cap = c.get("stat") or _STATS.get(c["pmid"], ("", ""))
    return html.escape(v), html.escape(cap)


FONT_FILES = {  # Abadi from the local Office cloud-font cache (fsType 8: embedding allowed)
    "_abadi-regular.ttf": "25909450846.ttf", "_abadi-bold.ttf": "25380718942.ttf",
    "_abadi-italic.ttf": "18499249641.ttf", "_abadi-bolditalic.ttf": "24503358819.ttf",
}
FONT_DIR = os.path.expanduser("~/Library/Group Containers/UBF8T346G9.Office/FontCache/4/CloudFonts/Abadi")

CSS = r"""
@font-face{font-family:"Abadi";src:url("_abadi-regular.ttf");font-weight:400;font-style:normal;}
@font-face{font-family:"Abadi";src:url("_abadi-bold.ttf");font-weight:700;font-style:normal;}
@font-face{font-family:"Abadi";src:url("_abadi-italic.ttf");font-weight:400;font-style:italic;}
@font-face{font-family:"Abadi";src:url("_abadi-bolditalic.ttf");font-weight:700;font-style:italic;}
.card{
  --ink:#1A1A1A; --navy:#1B355E; --steel:#2E5A88; --pale:#DCE6F1; --crimson:#8C1C1C;
  --grey:#5A5A5A; --band:#EFEFEF; --paper:#FFFFFF; --bg:#E9ECF1; --rule:#1A1A1A;
  --green:#1E7A33; --green-soft:#CDE7CF;
  font-family:"Abadi","Gill Sans","Segoe UI",Helvetica,Arial,sans-serif;
  font-size:17px; line-height:1.45; color:var(--ink); background:var(--bg);
  text-align:left; margin:0; padding:20px 10px;
}
.nightMode .card, .card.nightMode, .night_mode .card{
  --ink:#E8E8E6; --navy:#A9C1E6; --steel:#8FB0D8; --pale:#1F2E45; --crimson:#E07A74;
  --grey:#A3A7AD; --band:#23272E; --paper:#191C21; --bg:#0F1114; --rule:#C9CCD1;
  --green:#8ED69B; --green-soft:#16301C;
}
.slide{max-width:720px; margin:0 auto; background:var(--paper);
  box-shadow:0 1px 3px rgba(0,0,0,.08),0 10px 30px rgba(20,35,60,.10);}
.pad{padding:22px 28px 20px;}
.eyebrow{display:flex; align-items:center; gap:10px; font-weight:700; font-size:12px;
  letter-spacing:.14em; text-transform:uppercase; color:var(--crimson);}
.eyebrow .no{background:#8C1C1C; color:#fff; min-width:30px; text-align:center; padding:3px 6px; letter-spacing:.05em;}
.eyebrow .part{margin-left:auto; color:var(--grey); font-weight:400; letter-spacing:.1em; font-size:10.5px; text-align:right;}
.title{font-weight:700; color:var(--navy); text-transform:uppercase; letter-spacing:.03em;
  font-size:25px; line-height:1.15; margin:12px 0 10px;}
.question{font-weight:700; color:var(--navy); font-size:23px; line-height:1.25; margin:12px 0 10px;}
.rules{border-top:3px solid var(--rule); height:2px; border-bottom:1px solid var(--rule); margin:0 0 10px;}
.sub{font-style:italic; color:var(--grey); font-size:15px;}
.chips{margin-top:12px;}
.chip{display:inline-block; font-weight:700; font-size:11px; letter-spacing:.09em; text-transform:uppercase;
  padding:5px 10px; margin:0 6px 6px 0; color:#fff;}
.c-navy{background:#1B355E;} .c-steel{background:#2E5A88;} .c-green{background:#1E7A33;}
.c-slate{background:#8A939B;} .c-red{background:#B22222;} .c-amber{background:#D97A0B;}
.c-grey{background:#EFEFEF; color:#5A5A5A;} .c-yellow{background:#F2C40C; color:#1A1A1A;}
.c-pale{background:#DCE6F1; color:#1B355E;}
.cover{background:#1B355E; padding:26px 28px 24px; color:#fff;}
.cover .eyebrow{color:#F2D7D5;} .cover .eyebrow .part{color:#AFC3DE;}
.ctitle{font-weight:700; text-transform:uppercase; letter-spacing:.03em; font-size:28px; line-height:1.15; margin:26px 0 14px; color:#fff;}
.crule{width:90px; border-top:2px solid #fff; margin:0 0 12px;}
.csub{font-style:italic; color:#DCE6F1; font-size:15px;}
.cover .chips{margin-top:16px;}
.cover .c-navy{background:transparent; box-shadow:inset 0 0 0 1.5px #fff;} .cover .c-pale{background:#fff;} .cover .c-grey{background:#EFEFEF;}
.nightMode .cover, .night_mode .cover{background:#13243F;}
.prompt{margin-top:18px; padding-top:12px; border-top:1px solid var(--band); color:var(--grey); font-style:italic; font-size:15px;}
.prompt b{color:var(--crimson); font-style:normal; letter-spacing:.12em; font-size:11px; margin-right:8px;}
hr#answer{border:none; margin:0; height:0;}
.qline{font-style:italic; font-size:17px; color:var(--ink); padding:14px 28px 0; }
.qline:before{content:"— "; color:var(--crimson);}
.body{padding:12px 28px 20px;}
.stat{display:flex; margin:6px 0 14px; background:var(--paper); border:1px solid var(--band);
  box-shadow:0 2px 6px rgba(0,0,0,.06);}
.stat .bar{width:6px; background:#1B355E;}
.stat .val{font-weight:700; color:var(--navy); font-size:30px; line-height:1; padding:16px 18px; white-space:nowrap;
  border-right:1px solid var(--band); display:flex; align-items:center;}
.stat .val{font-size:clamp(20px,5.2vw,30px);}
.stat .cap{padding:12px 16px; font-size:14px; color:var(--grey); display:flex; align-items:center;}
.sec{margin-top:12px;}
.sec .hd{background:#1B355E; color:#fff; font-weight:700; font-size:11px; letter-spacing:.14em;
  text-transform:uppercase; padding:6px 10px;}
.sec .bd{border:1px solid #1A1A1A; border-top:none; padding:10px 12px; font-size:16px;}
.nightMode .sec .bd, .night_mode .sec .bd{border-color:#3A3F47;}
.sec.alt .bd{background:var(--band);}
.sec .bd b{color:var(--navy);}
.take{margin-top:14px; background:var(--green-soft); border-left:6px solid var(--green); padding:12px 14px;}
.take .lb{font-weight:700; font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--green); margin-bottom:4px;}
.take .tx{font-weight:700; font-style:italic; font-size:16.5px; color:var(--ink);}
.foot{ margin-top:18px; padding-top:10px; border-top:1px solid var(--rule);}
.fbar{display:flex; justify-content:space-between; align-items:center; gap:10px; margin-top:8px;}
.foot .ref{ font-style:italic; font-size:12px; color:var(--grey); line-height:1.35;}
.foot .links a{display:inline-block; font-weight:700; font-size:11px; letter-spacing:.1em; text-transform:uppercase;
  color:var(--steel); text-decoration:none; border:1px solid var(--steel); padding:4px 8px; margin-left:6px;}
.foot .pg{font-weight:700; color:var(--navy); font-size:10.5px; letter-spacing:.1em; text-transform:uppercase; }
.foot .links{white-space:nowrap;}
.ans{margin:4px 0 12px; border-left:6px solid var(--crimson); padding:8px 0 8px 14px;
  font-size:21px; line-height:1.3; font-weight:400; color:var(--ink);}
.ans b{color:var(--navy);}
.bignum{font-weight:700; color:var(--navy); font-size:38px; line-height:1.1; margin:6px 0 12px;}
.who{font-size:13.5px; color:var(--grey); margin:0 0 4px;}
.who b{color:var(--navy);}
.body .qline{padding:0 0 10px;}
.more{margin-top:14px; border-top:1px solid var(--band); padding-top:8px;}
.more summary{cursor:pointer; font-weight:700; font-size:11px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--steel); padding:6px 0; list-style:none;}
.more summary::-webkit-details-marker{display:none;}
.more summary:before{content:"▸  ";} .more[open] summary:before{content:"▾  ";}
.more .chips{margin-top:6px;}
@media (max-width:480px){ .ans{font-size:19px;} .bignum{font-size:30px;} .pad{padding:18px 18px 16px;} .body{padding:10px 18px 18px;} .qline{padding:12px 18px 0;}
  .title{font-size:21px;} .ctitle{font-size:23px;} .question{font-size:20px;} .stat .val{font-size:24px; padding:12px;} .foot{flex-wrap:wrap;} }
"""

HEAD = """<div class="slide"><div class="pad">
<div class="eyebrow"><span class="no">{{BlockNo}}</span><span>{{Topic}}</span></div>"""

# Each card tests ONE thing; the answer comes first, everything else is folded into "Details".
ANSWER = """<div class="ans">{{Answer}}</div>"""

STAT = """<div class="stat"><div class="bar"></div><div class="val">{{StatValue}}</div><div class="cap">{{StatCaption}}</div></div>"""

STUDY_LINE = """<div class="who"><b>{{Trial}}</b> · {{FirstAuthor}} · {{Journal}} · {{Year}}</div>"""

DETAILS = """<details class="more"><summary>Details</summary>
<div class="chips">{{Badges}}</div>
<div class="sec"><div class="hd">Design</div><div class="bd">{{Design}}</div></div>
<div class="sec alt"><div class="hd">Result</div><div class="bd">{{Result}}</div></div>
<div class="take"><div class="lb">Bottom line</div><div class="tx">{{BottomLine}}</div></div>
<div class="foot"><div class="ref">{{Citation}}</div>
<div class="fbar"><div class="pg">{{Domain}}</div><div class="links"><a href="https://pubmed.ncbi.nlm.nih.gov/{{PMID}}/">PubMed</a>{{#DOI}}<a href="https://doi.org/{{DOI}}">DOI</a>{{/DOI}}</div></div></div>
</details>"""

# 1. Named trial → what it showed (only notes with Named filled)
FRONT_NAME = """{{#Named}}<div class="slide"><div class="cover">
<div class="eyebrow"><span class="no">{{BlockNo}}</span><span>{{Topic}}</span></div>
<div class="ctitle">{{Trial}}</div><div class="crule"></div>
<div class="csub">{{FirstAuthor}} · {{Journal}} · {{Year}}</div></div>
<div class="pad"><div class="prompt"><b>RECALL</b>What did it show?</div></div>
</div>{{/Named}}"""

BACK_NAME = """<div class="slide"><div class="cover">
<div class="eyebrow"><span class="no">{{BlockNo}}</span><span>{{Topic}}</span></div>
<div class="ctitle">{{Trial}}</div><div class="crule"></div>
<div class="csub">{{FirstAuthor}} · {{Journal}} · {{Year}}</div></div>
<hr id="answer"><div class="body">
<div class="qline">{{Question}}</div>""" + ANSWER + DETAILS + """</div></div>"""

# 2. Clinical question → answer (every note)
FRONT_Q = HEAD + """
<div class="question">{{Question}}</div><div class="rules"></div>
<div class="prompt"><b>RECALL</b>What is the answer?</div>
</div></div>"""

BACK_Q = HEAD + """
<div class="question">{{Question}}</div><div class="rules"></div></div>
<hr id="answer"><div class="body">""" + ANSWER + STUDY_LINE + DETAILS + """</div></div>"""

# 3. Key number (every note with a curated stat)
FRONT_STAT = """{{#StatValue}}""" + HEAD + """
<div class="title">{{Trial}}</div><div class="rules"></div>
<div class="question">{{StatCaption}}</div>
<div class="prompt"><b>NUMBER</b>What is the figure?</div>
</div></div>{{/StatValue}}"""

BACK_STAT = HEAD + """
<div class="title">{{Trial}}</div><div class="rules"></div>
<div class="question">{{StatCaption}}</div></div>
<hr id="answer"><div class="body"><div class="bignum">{{StatValue}}</div>""" + ANSWER + DETAILS + """</div></div>"""

# Field order is append-only: existing notes keep their data when the deck is re-imported.
FIELDS = ["Trial", "Question", "Design", "Result", "BottomLine", "Topic", "Domain",
          "Journal", "Year", "Citation", "PMID", "DOI", "Badges", "BlockNo", "FirstAuthor",
          "StatValue", "StatCaption", "Answer", "Named"]

model = genanki.Model(
    MODEL_ID,
    "Landmark Study (PubMed-verified)",
    fields=[{"name": f} for f in FIELDS],
    templates=[
        {"name": "Named trial → Finding", "qfmt": FRONT_NAME, "afmt": BACK_NAME},
        {"name": "Clinical question → Answer", "qfmt": FRONT_Q, "afmt": BACK_Q},
        {"name": "Key number", "qfmt": FRONT_STAT, "afmt": BACK_STAT},
    ],
    css=CSS,
)


def load_cards():
    cards = []
    for f in sorted(glob.glob(os.path.join(WORK, "cards_*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(f), f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        cards += m.CARDS
    return cards


def load_list(fname, var):
    path = os.path.join(WORK, fname)
    if not os.path.exists(path):
        return []
    spec = importlib.util.spec_from_file_location(fname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return list(getattr(m, var))


def citation(meta):
    first = meta["first"] + (" et al." if meta["etal"] else "")
    return f'{html.escape(first)} {html.escape(meta["title"])} {html.escape(meta["journal"])} {meta["year"]}.'


def main():
    global ANSWERS, NAMED
    spec = importlib.util.spec_from_file_location("answers", os.path.join(WORK, "answers.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ANSWERS, NAMED = m.ANSWERS, m.NAMED
    abstracts = json.load(open(os.path.join(WORK, "abstracts.json")))
    cards = load_cards()
    new = load_list("new_studies.py", "NEW")
    for c in new:
        ANSWERS[c["pmid"]] = c["answer"]
        if c.get("named"):
            NAMED.add(c["pmid"])
    cards += new
    extra = load_list("extra_questions.py", "EXTRA")
    by_pmid = {c["pmid"]: c for c in cards}
    seen = set()
    for c in cards:
        assert c["pmid"] not in seen, f"duplicate study {c['pmid']}"
        seen.add(c["pmid"])
    log = {}  # added date -> list of lines for CHANGELOG.md
    decks = {}
    rows = []
    n_extra = 0
    for x in extra:
        assert x["pmid"] in by_pmid, f"extra question for unknown PMID {x['pmid']}"
    keys = [(x["pmid"], x["key"]) for x in extra]
    assert len(keys) == len(set(keys)), "duplicate extra-question key"
    for c in cards:
        meta = abstracts[c["pmid"]]
        n = block_of(c["deck"])
        if n not in BLOCKS:  # GI decks (27+) are not part of the hepatology build
            continue
        dom, cls = section_of(n)
        topic = BLOCKS[n]
        full = f"{ROOT_DECK}::{n:02d} {BLOCKS[n]}"
        if full not in decks:
            decks[full] = genanki.Deck(stable_id(full), full)
        tags = c["tags"].split() + [f"block{n:02d}"]
        if c.get("added"):
            tags += ["new_study", f"added::{c['added']}"]
            log.setdefault(c["added"], []).append(f"- New study · {n:02d} {BLOCKS[n]} · **{c['name']}** ({meta['journal']} {meta['year']}, PMID {c['pmid']})")
        note = genanki.Note(
            model=model,
            fields=[
                safe_html(c["name"]), safe_html(c["q"]), safe_html(c["design"]), safe_html(c["result"]),
                safe_html(c["bottom"]), html.escape(topic), f"Part {ROMAN[SECTIONS.index(next(x for x in SECTIONS if x[0] <= n <= x[1])) + 1]} · {dom}", html.escape(meta["journal"]), meta["year"],
                citation(meta), c["pmid"], meta["doi"] or "", badges(c["tags"], c["pmid"]), f"{n:02d}",
                html.escape(meta["first"] + (" et al." if meta["etal"] else "")), *stat_for(c),
                safe_html(ANSWERS[c["pmid"]]), "y" if c["pmid"] in NAMED else "",
            ],
            tags=tags,
            guid=genanki.guid_for("landmark-trial", c["pmid"]),
        )
        decks[full].add_note(note)
        for x in [x for x in extra if x["pmid"] == c["pmid"]]:
            f = list(note.fields)
            f[FIELDS.index("Question")] = safe_html(x["q"])
            f[FIELDS.index("Answer")] = safe_html(x["a"])
            f[FIELDS.index("StatValue")] = f[FIELDS.index("StatCaption")] = f[FIELDS.index("Named")] = ""
            decks[full].add_note(genanki.Note(
                model=model, fields=f, guid=genanki.guid_for("landmark-extra", c["pmid"], x["key"]),
                tags=c["tags"].split() + [f"block{n:02d}", "extra_q", f"added::{x['added']}"]))
            n_extra += 1
            log.setdefault(x["added"], []).append(f"- Extra question · {c['name']}: {re.sub('<[^>]+>', '', x['q'])}")
        rows.append([f"{n:02d}", BLOCKS[n], c["name"], meta["year"], meta["journal"], meta["first"], c["pmid"],
                     meta["doi"] or "", f'https://pubmed.ncbi.nlm.nih.gov/{c["pmid"]}/'])

    out = os.path.join(HERE, "Pediatric_Hepatology_Landmark_Studies.apkg")
    pkg = genanki.Package(list(decks.values()))
    pkg.media_files = []
    for dst, src in FONT_FILES.items():
        path = os.path.join(WORK, dst)
        if not os.path.exists(path):
            import shutil
            shutil.copy(os.path.join(FONT_DIR, src), path)
        pkg.media_files.append(path)
    pkg.write_to_file(out)
    with open(os.path.join(HERE, "Pediatric_Hepatology_Landmark_Studies_index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Block", "Topic", "Study", "Year", "Journal", "First author", "PMID", "DOI", "PubMed URL"])
        w.writerows(sorted(rows))
    named = sum(1 for r in rows if r[6] in NAMED)
    stats = sum(1 for c in cards if block_of(c["deck"]) in BLOCKS and stat_for(c)[0])
    total = len(rows) + named + stats + n_extra
    with open(os.path.join(HERE, "CHANGELOG.md"), "w") as f:
        f.write(f"# Deck changelog\n\nCurrent build: {len(rows)} studies, {n_extra} extra questions, ~{total} cards.\n"
                "Each day's additions are tagged `added::YYYY-MM-DD` in Anki.\n")
        for d in sorted(log, reverse=True):
            f.write(f"\n## {d}\n\n" + "\n".join(log[d]) + "\n")
    print(f"{len(rows)} studies + {n_extra} extra questions -> ~{total} cards ({named} named) in {len(decks)} sub-decks -> {out}")


if __name__ == "__main__":
    main()
