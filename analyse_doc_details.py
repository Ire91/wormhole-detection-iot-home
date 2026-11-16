import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

def find_keywords(filename):
    doc = docx.Document(filename)
    
    print("=== DEDICATION PARAGRAPHS ===")
    ded_idx = -1
    for idx, p in enumerate(doc.paragraphs):
        if "DEDICATION" in p.text.upper():
            ded_idx = idx
            break
    if ded_idx != -1:
        for offset in range(1, 5):
            print(f"P{ded_idx+offset}: {doc.paragraphs[ded_idx+offset].text}")

    print("\n=== ACKNOWLEDGEMENTS PARAGRAPHS ===")
    ack_idx = -1
    for idx, p in enumerate(doc.paragraphs):
        if "ACKNOWLEDGEMENTS" in p.text.upper():
            ack_idx = idx
            break
    if ack_idx != -1:
        for offset in range(1, 8):
            text = doc.paragraphs[ack_idx+offset].text.strip()
            if text:
                print(f"P{ack_idx+offset}: {text[:150]}...")

    print("\n=== ABSTRACT PARAGRAPHS ===")
    abs_idx = -1
    for idx, p in enumerate(doc.paragraphs):
        if "ABSTRACT" in p.text.upper() and len(p.text.strip()) == 8:
            abs_idx = idx
            break
    if abs_idx != -1:
        for offset in range(1, 10):
            text = doc.paragraphs[abs_idx+offset].text.strip()
            if text:
                print(f"P{abs_idx+offset}: {text[:200]}...")

    print("\n=== OCCURRENCES OF 'PROPOSED' ===")
    proposed_count = 0
    for idx, p in enumerate(doc.paragraphs):
        if "proposed" in p.text.lower():
            proposed_count += 1
            if proposed_count <= 15:
                print(f"P{idx}: {p.text.strip()[:120]}...")
    print(f"Total occurrences of 'proposed' in paragraphs: {proposed_count}")

find_keywords("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
