"""
inspect_table_positions.py
--------------------------
Shows all paragraphs and tables in document order (using XML body children)
so we can see exactly where each table sits relative to surrounding text.
"""
import sys
from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')

doc = Document("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
body = doc.element.body

table_counter = 0
para_counter = 0

for idx, child in enumerate(body):
    tag = child.tag.split('}')[-1]  # w:tbl or w:p

    if tag == 'tbl':
        # Get first cell text as label
        try:
            first_text = child.findall('.//' + qn('w:t'))
            preview = ''.join(t.text or '' for t in first_text[:5])[:60]
        except:
            preview = '(unreadable)'
        print(f"[{idx:04d}] TABLE {table_counter}: first_text='{preview}'")
        table_counter += 1

    elif tag == 'p':
        # Get paragraph text
        texts = child.findall('.//' + qn('w:t'))
        ptext = ''.join(t.text or '' for t in texts).strip()
        if ptext:  # Only print non-empty paragraphs
            print(f"[{idx:04d}] PARA: {ptext[:100]}")
        para_counter += 1
