import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

def view_abstract(filename):
    doc = docx.Document(filename)
    abs_idx = -1
    for idx, p in enumerate(doc.paragraphs):
        if "ABSTRACT" in p.text.upper() and len(p.text.strip()) == 8:
            abs_idx = idx
            break
    if abs_idx != -1:
        for offset in range(1, 8):
            print(f"P{abs_idx+offset}: {doc.paragraphs[abs_idx+offset].text}")

view_abstract("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
