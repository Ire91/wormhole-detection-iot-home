import docx

def find_placeholders(filename):
    doc = docx.Document(filename)
    print("=== SEARCHING FOR PLACEHOLDERS ===")
    for idx, p in enumerate(doc.paragraphs):
        text = p.text
        if "HOD" in text or "Head of Department" in text or "[" in text or "]" in text:
            print(f"P{idx}: {text}")

find_placeholders("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
