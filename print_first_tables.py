import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')

def print_first_tables(filename):
    doc = docx.Document(filename)
    for idx in range(min(len(doc.tables), 3)):
        print(f"\nTable {idx}:")
        table = doc.tables[idx]
        for r_idx, r in enumerate(table.rows):
            row_text = [cell.text.strip().replace("\n", " ") for cell in r.cells]
            print(f"  Row {r_idx}: {row_text}")

print_first_tables("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
