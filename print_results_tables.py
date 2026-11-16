import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')

def print_tables(filename):
    doc = docx.Document(filename)
    for idx in range(12, len(doc.tables)):
        print(f"\n================ TABLE {idx} ================")
        table = doc.tables[idx]
        for r_idx, r in enumerate(table.rows):
            row_text = [cell.text.strip().replace("\n", " ") for cell in r.cells]
            print(f"  Row {r_idx}: {row_text}")

print_tables("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
