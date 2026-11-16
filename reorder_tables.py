"""
reorder_tables.py
-----------------
The original DOCX has tables 4-18 appended at the end of the document
(after the References section). This script moves each table back to its
correct position, identified by an anchor paragraph keyword that appears
just before where the table should sit.

Strategy:
  1. Load document XML body children as a list.
  2. Identify each table element by its first-cell preview text.
  3. Find the anchor paragraph in the body where the table should be inserted.
  4. Remove the table from its current (end) position and reinsert it after
     the anchor paragraph.
  5. Save as a new corrected file.
"""

import sys
from lxml import etree
from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')


def get_first_cell_text(tbl_el):
    texts = tbl_el.findall('.//' + qn('w:t'))
    return ''.join(t.text or '' for t in texts[:10])


def get_para_text(p_el):
    texts = p_el.findall('.//' + qn('w:t'))
    return ''.join(t.text or '' for t in texts)


def find_para_by_keyword(body_children, keyword, start=0):
    """Return index of first paragraph containing the keyword."""
    for i in range(start, len(body_children)):
        child = body_children[i]
        if child.tag.split('}')[-1] == 'p':
            text = get_para_text(child)
            if keyword in text:
                return i
    return -1


def find_table_by_first_cell(body_children, keyword):
    """Return index of table whose first-cell text contains keyword."""
    for i, child in enumerate(body_children):
        if child.tag.split('}')[-1] == 'tbl':
            first = get_first_cell_text(child)
            if keyword in first:
                return i
    return -1


def move_table_after(body, anchor_idx, table_idx):
    """
    Remove table at table_idx from body and insert it directly after anchor_idx.
    Indices are positions in body (lxml element list).
    """
    children = list(body)
    tbl = children[table_idx]
    body.remove(tbl)

    # Re-fetch children after removal (indices shift)
    children = list(body)
    # anchor_idx may have shifted if table was before anchor
    # Find the anchor element again (it's still the same object)
    anchor_el = children[anchor_idx if table_idx > anchor_idx else anchor_idx - 1]
    anchor_pos = list(body).index(anchor_el)
    anchor_el.addnext(tbl)
    print(f"  Moved table to after anchor at new position {anchor_pos+1}")


def reorder(input_path, output_path):
    doc = Document(input_path)
    body = doc.element.body

    # Each entry: (table_first_cell_keyword, anchor_paragraph_keyword)
    # anchor = the paragraph that the table should be placed RIGHT AFTER
    table_placements = [
        # Table 4: Objective-Methodology Mapping → after "Table 1.1" reference
        ("S/NObjectiveMethodology",
         "Table 1.1: Objective"),

        # Table 5: Summary of Reviewed Studies → after "Table 2.1" reference
        ("Author(s) & YearProblem",
         "Table 2.1: Summary of Reviewed"),

        # Table 6: Comparison table → after "Table 2.2" reference
        ("FeatureML-Based Detection",
         "Table 2.2: Comparison of Wormhole"),

        # Table 7: Functional Requirements → after "Table 3.1" reference
        ("S/NRequirementDescriptionFR1",
         "Table 3.1: Functional Requirements"),

        # Table 8: Non-Functional Requirements → after "Table 3.2" reference
        ("S/NRequirementDescriptionNFR1",
         "Table 3.2: Non-Functional Requirements"),

        # Table 9: Rule Threshold Summary → after "Table 3.3" reference
        ("RuleMetricNormal Range",
         "Table 3.3: Detection Rule Threshold"),

        # Table 10: Algorithm pseudocode → after "Table 3.4" reference or algorithm intro para
        ("INPUT:  packet_stream",
         "Table 3.4: Evaluation Metrics"),

        # Table 11: Evaluation Metrics → after "Table 3.4" reference (it IS table 3.4 intro)
        ("S/NMetricDefinition",
         "Table 3.5: Simulation Profile"),

        # Table 12: Simulation Profile Configurations → after "Table 3.5" reference
        ("ProfileScenarioNodes",
         "3.7  Summary"),

        # Table 13: Detection Rule Implementation Summary → after "Table 4.1" reference
        ("RuleNameTrigger Condition",
         "Table 4.1: Detection Rule Implementation"),

        # Table 14: Nine-Cell Heterogeneity Results → after "Table 4.2" reference
        ("ProfileAttack ModeWDR Mean",
         "Table 4.2: Nine-Cell Heterogeneity"),

        # Table 15: Per-Rule TP FP → after "Table 4.3" reference
        ("RuleTotal TPTotal FP",
         "Table 4.3: Per-Rule True Positive"),

        # Table 16: Feature Importances → after "Table 4.4" reference
        ("FeatureImportance Score",
         "Table 4.4: Random Forest Feature"),

        # Table 17: ML Baseline Performance → after "Table 4.5" reference
        ("ProfilePrecisionRecall",
         "Table 4.5: Machine-Learning Baseline"),

        # Table 18: Literature comparison → after "Table 4.6" reference
        ("StudyDetection Mechanism",
         "Table 4.6: Comparison with Literature"),
    ]

    print("=" * 60)
    print("  REORDERING TABLES")
    print("=" * 60)

    for table_kw, anchor_kw in table_placements:
        children = list(body)
        table_idx = find_table_by_first_cell(children, table_kw)
        anchor_idx = find_para_by_keyword(children, anchor_kw)

        if table_idx == -1:
            print(f"  [SKIP] Table not found: '{table_kw[:40]}'")
            continue
        if anchor_idx == -1:
            print(f"  [SKIP] Anchor paragraph not found: '{anchor_kw}'")
            continue

        print(f"\n  Table:  '{table_kw[:50]}'")
        print(f"  Anchor: '{anchor_kw}'")
        print(f"  Current table position: {table_idx}, anchor position: {anchor_idx}")

        if table_idx > anchor_idx:
            # Table is after anchor — move it right after anchor
            tbl_el = children[table_idx]
            body.remove(tbl_el)
            # Find anchor again after removal
            children2 = list(body)
            anchor_el = None
            for el in children2:
                if el.tag.split('}')[-1] == 'p':
                    txt = get_para_text(el)
                    if anchor_kw in txt:
                        anchor_el = el
                        break
            if anchor_el is not None:
                anchor_el.addnext(tbl_el)
                print(f"  SUCCESS: moved table after anchor.")
            else:
                # Re-append if we can't find anchor
                body.append(tbl_el)
                print(f"  WARN: anchor not found after removal. Table re-appended.")
        else:
            print(f"  OK: Table already before anchor (position {table_idx} < {anchor_idx}), skipping.")

    doc.save(output_path)
    print("\n" + "=" * 60)
    print(f"  Saved: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    reorder(
        "22CG031840_BALOGUN_IREOLUWA_FYP_CORRECTED.docx",
        "22CG031840_BALOGUN_IREOLUWA_FYP_FINAL.docx"
    )
