import sys
from lxml import etree
from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')

doc = Document("22CG031840_BALOGUN_IREOLUWA_FYP_FINAL.docx")
body = doc.element.body

table_counter = 0
for idx, child in enumerate(body):
    tag = child.tag.split('}')[-1]
    if tag == 'tbl':
        first_text = ''.join(t.text or '' for t in child.findall('.//' + qn('w:t'))[:6])[:50]
        print(f"[pos {idx:04d}] TABLE {table_counter}: '{first_text}'")
        table_counter += 1
    elif tag == 'p':
        ptext = ''.join(t.text or '' for t in child.findall('.//' + qn('w:t'))).strip()
        # Only print headings and table captions
        if ptext and any(k in ptext for k in ['Table ', 'CHAPTER', 'Figure ', '1.1', '1.2', '1.3', '1.4', '1.5', 'ABSTRACT', 'REFERENCES']):
            print(f"[pos {idx:04d}] PARA:  '{ptext[:80]}'")
