import docx

def inspect_cert(filename):
    doc = docx.Document(filename)
    print("=== INSPECTING CERTIFICATION SECTION ===")
    for idx in range(16, 23):
        print(f"P{idx}: {doc.paragraphs[idx].text}")

inspect_cert("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
