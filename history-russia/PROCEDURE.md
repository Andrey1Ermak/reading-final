# Nightly procedure — History of Russia (one lesson per run)

Audience: Andrey, an interested amateur (not a historian). Language of everything he receives: **Russian**.
Scope: from the origins to 31 December 1999. Plan: `Russian_History_Year_Plan.docx` in the repo root (26 blocks × 14 days; each block has a table День | Тема урока | Фокус и тонкие моменты).

Only the listening PDFs are kept. The deck is a working draft: build it, check it, use it, then **do not commit it**.

## 1. Pick the lesson
List `history-russia/*_audio.pdf`, find the highest `BB-DD`, take the next day in the plan (after day 14 go to day 1 of the next block). If nothing exists yet, start at 01-01. If the plan is finished (26-14 exists), stop and report that the course is complete.

## 2. Research
Use WebSearch/WebFetch. Prefer encyclopedias and scholarly sources (Большая российская энциклопедия, Britannica, university sites, books listed in the plan as Опорные источники). Verify every date, name, number and quote. Never invent quotes or figures. Where historians disagree (the plan often flags this), present the main positions fairly and attribute them in words ("историк Скрынников считал…"); do not add a verdict of your own. For the twentieth century, keep the tone factual and even-handed; give numbers of victims as ranges with who estimated them. Short quotes from medieval and pre-1929 sources (летописи, Пушкин, Карамзин) are fine.

## 3. Deck (working draft, Russian)
Read the pptx skill first. About 20 slides, serif font, clean layout: Сцена → Вопрос дня → Контекст → Люди → Что произошло (timeline) → Почему так вышло → Споры и мифы → Итог. Use text, timelines, simple diagrams and schematic maps drawn with shapes; do not download portraits or photos of people. Render (soffice → PDF → images), look at every slide, fix overflow. Save it only in the scratch/work directory, **never in the repo**.

## 4. Listening chapter (the deliverable)
Write in three passes, keep only the last:
a) full spoken narration covering every slide;
b) adapt for an interested amateur: every term explained, every person introduced ("Олег, родственник Рюрика и правитель Новгорода…"), causes and consequences spelled out;
c) rewrite as a chapter of a good popular history book or podcast: flowing connected prose. Open with a vivid scene (built on real sources, no invented details presented as fact), then the question of the day and the main idea, then the story, the reasons, the disputes and myths, and close with what grew out of it and how it connects to the next lesson.

Length: about 3 500–4 500 words (≈ 30 minutes of listening), the same as the hepatology `_audio.pdf` chapters.

Text-to-speech rules (Russian TTS app):
- plain paragraphs only; a title line and at most 3–5 short plain section titles;
- NO tables, lists, columns, figures, footnotes, citation brackets, headers/footers or page numbers in the text;
- NO Roman numerals and no abbreviations like «в.», «гг.», «г.», «т.е.», «XIV»: write «в четырнадцатом веке», «в тысяча двести сороковом году», «то есть»;
- write all years and numbers in words with the correct grammatical case;
- write ё where it belongs (её, всё, ещё);
- describe any map or timeline from the deck in words; name sources in words.

Layout: A4, single column, DejaVu Serif 12 pt (Cyrillic-safe; register the TTF with reportlab), leading ~16 pt, margins ~2.5 cm, title DejaVu Serif Bold 16 pt. Open `hepatology/05-05_New_PFIC_genes_audio.pdf` once as the layout model. Build with reportlab, then check with `pdftotext` that the Cyrillic text extracts in correct reading order with no broken words, and count words.

Save as `history-russia/BB-DD_Short_Latin_Name_audio.pdf` (short Latin transliteration or English, underscores), e.g. `01-01_Zemlya_reki_step_audio.pdf`.

## 5. Commit and push
Only the audio PDF (and `history-russia/LOG.md`, one line appended: `BB-DD — Тема — YYYY-MM-DD — N слов`). Commit message: `Add History BB-DD <Тема>`. In unattended runs follow the trigger's git rules (one command per Bash call, nothing chained).

## 6. Deliver
- Email the PDF to andrewermakwork@gmail.com via Gmail send_message. Subject: `История России — <date> — BB-DD <Тема>`. Plain-text body in Russian: topic, one-sentence teaser, link https://github.com/Andrey1Ermak/reading-final/tree/main/history-russia. Attach the PDF (base64 -w0, mimeType application/pdf). If attaching fails, send without it and say where the file is.
- Send the PDF into the session with SendUserFile (status proactive).

Final message, short, in Russian: which lesson, word count, push and email status, any problem.
