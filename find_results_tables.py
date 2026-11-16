import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')

def find_results_tables(filename):
    doc = docx.Document(filename)
    print(f"Total tables: {len(doc.tables)}")
    for idx, table in enumerate(doc.tables):
        first_cell = table.rows[0].cells[0].text.strip().replace("\n", " ")
        print(f"Table {idx}: First cell text = {first_cell[:80]}")

find_results_tables("22CG031840_BALOGUN_IREOLUWA_FYP_1.docx")
