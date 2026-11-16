import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect_docx(filename):
    doc = docx.Document(filename)
    print(f"File: {filename}")
    print(f"Number of paragraphs: {len(doc.paragraphs)}")
    print(f"Number of tables: {len(doc.tables)}")
    print(f"Number of sections: {len(doc.sections)}")
    
    print("\n--- FIRST 40 PARAGRAPHS ---")
    for idx, p in enumerate(doc.paragraphs[:40]):
        text = p.text.strip()
        if text:
            print(f"P{idx}: [Style={p.style.name}] {text[:100]}")

inspect_docx("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
