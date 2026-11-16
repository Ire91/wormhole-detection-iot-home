import docx

def inspect_tables(filename):
    doc = docx.Document(filename)
    print("=== INSPECTING DOCUMENT TABLES ===")
    for idx, table in enumerate(doc.tables):
        print(f"\nTable {idx}:")
        for r_idx, r in enumerate(table.rows):
            row_text = [cell.text.strip().replace("\n", " ") for cell in r.cells]
            print(f"  Row {r_idx}: {row_text}")

inspect_tables("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
