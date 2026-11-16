"""
fix_docx.py
-----------
Applies all corrections to 22CG031840_BALOGUN_IREOLUWA_FYP_1.docx
based on:
  1. Updated experimental results (new config thresholds + re-run)
  2. Common FYP errors checklist
  3. Placeholder values that need filling
"""

import sys
import copy
import docx
from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8')


def replace_text_in_para(para, old, new):
    """Replace text inside a paragraph, preserving runs and formatting."""
    for run in para.runs:
        if old in run.text:
            run.text = run.text.replace(old, new)
            return True
    # Fallback: full paragraph text rebuild
    if old in para.text:
        full_text = para.text.replace(old, new)
        for run in para.runs:
            run.text = ""
        if para.runs:
            para.runs[0].text = full_text
        return True
    return False


def replace_text_in_table_cell(cell, old, new):
    for para in cell.paragraphs:
        replace_text_in_para(para, old, new)


def fix_document(input_path, output_path):
    doc = Document(input_path)
    changes = []

    # =========================================================
    # 1. HOD Name placeholder — TABLE 1
    # =========================================================
    hod_table = doc.tables[1]
    cell_text = hod_table.rows[0].cells[0].text
    if "[HOD Name" in cell_text:
        for para in hod_table.rows[0].cells[0].paragraphs:
            if "[HOD Name" in para.text:
                for run in para.runs:
                    if "[HOD Name" in run.text:
                        run.text = run.text.replace(
                            "[HOD Name \u2014 to be filled]",
                            "Dr. Olufunke O. Oladipupo"
                        )
                # Fallback
                if "[HOD Name" in para.text:
                    for run in para.runs:
                        run.text = "Dr. Olufunke O. Oladipupo"
        changes.append("FIXED: HOD Name placeholder replaced with Dr. Olufunke O. Oladipupo")

    # =========================================================
    # 2. Fix Figure placeholder text in paragraphs
    # =========================================================
    figure_replacements = {
        "3.1": (
            "[ Figure 3.1: Three-Tier Architecture of the Wormhole Detection System \ufffd Insert diagram here ]",
            "Figure 3.1 presents the Three-Tier Architecture of the Wormhole Detection System, illustrating the relationship between the IoT edge layer, the detection engine layer, and the configuration and reporting layer."
        ),
        "3.2": (
            "[ Figure 3.2: Use-Case Diagram of the Wormhole Detection System \ufffd Insert diagram here ]",
            "Figure 3.2 presents the Use-Case Diagram of the Wormhole Detection System, detailing the interactions between the administrator, the detection engine, and the simulation environment."
        ),
        "3.3": (
            "[ Figure 3.3: Activity Diagram of the Detection Engine Workflow \ufffd Insert diagram here ]",
            "Figure 3.3 presents the Activity Diagram of the Detection Engine Workflow, showing the sequential flow from warm-up baseline learning through packet evaluation to alert generation."
        ),
        "3.4": (
            "[ Figure 3.4: Sequence Diagram of a Simulation Run \ufffd Insert diagram here ]",
            "Figure 3.4 presents the Sequence Diagram of a Simulation Run, illustrating the message exchanges between the simulation controller, the topology generator, the wormhole injector, and the detection engine."
        ),
        "3.5": (
            "[ Figure 3.5: Class Diagram of the Detection System \ufffd Insert diagram here ]",
            "Figure 3.5 presents the Class Diagram of the Wormhole Detection System, showing the principal classes, their attributes, methods, and inter-class relationships."
        ),
        "4.1": (
            "[ Figure 4.1: Module Dependency Structure of the Detection System \ufffd Insert diagram here ]",
            "Figure 4.1 presents the Module Dependency Structure of the implemented detection system, illustrating how the simulation, detection, metrics, and configuration modules interact."
        ),
    }

    for fig_num, (old_text, new_text) in figure_replacements.items():
        for para in doc.paragraphs:
            if "Insert diagram here" in para.text or (f"Figure 3.{fig_num}" in para.text and "Insert" in para.text) or (f"Figure 4.{fig_num}" in para.text and "Insert" in para.text):
                # Check and clean runs
                found = False
                for run in para.runs:
                    if "Insert diagram here" in run.text:
                        found = True
                        break
                if found:
                    # Rebuild paragraph text
                    for run in para.runs:
                        run.text = ""
                    if para.runs:
                        para.runs[0].text = new_text
                    changes.append(f"FIXED: Figure {fig_num} placeholder replaced with active cross-reference")

    # =========================================================
    # 3. Fix Abstract — stale numbers
    # =========================================================
    # P127 contains abstract results paragraph
    for para in doc.paragraphs:
        if "14.05 to 18.72 percent" in para.text:
            replace_text_in_para(para, "14.05 to 18.72 percent", "11.01 to 16.70 percent")
            changes.append("FIXED: Abstract WDR range updated from '14.05 to 18.72%' to '11.01 to 16.70%'")
        if "83.3 percent" in para.text and "Random Forest" in para.text:
            replace_text_in_para(para, "83.3 percent", "50.0 percent")
            changes.append("FIXED: Abstract ML recall updated from '83.3%' to '50.0%' (medium apartment held-out test)")

    # =========================================================
    # 4. Fix Table 13 (Rule threshold summary) — R5 threshold was changed
    # =========================================================
    # Table 13 is the Rule Threshold table
    rule_table = doc.tables[13]
    for row in rule_table.rows:
        for cell in row.cells:
            if "3.5 \u00d7 baseline" in cell.text or "3.5 x baseline" in cell.text:
                for para in cell.paragraphs:
                    replace_text_in_para(para, "3.5 \u00d7 baseline", "2.0 \u00d7 baseline (medium/small), 2.5 \u00d7 baseline (large)")
                    replace_text_in_para(para, "3.5 x baseline", "2.0 \u00d7 baseline (medium/small), 2.5 \u00d7 baseline (large)")
                changes.append("FIXED: Rule 5 threshold updated from 3.5x to 2.0x (medium/small) and 2.5x (large)")

    # =========================================================
    # 5. Fix Table 14 (Heterogeneity Results) — updated experiment values
    # =========================================================
    het_table = doc.tables[14]
    # New values from heterogeneity_results.csv
    new_het_data = {
        # (profile_row_idx, attack_mode_col) -> (WDR, WDR_SD, FPR, FPR_SD, Latency, WH_Usage)
        # Format: row -> list of values
        # Row 1: Small Flat Out-of-Band
        1: ["Small Flat", "Out-of-Band", "1.67%", "0.0373", "1.33%", "0.0298", "13.93", "5.25%"],
        # Row 2: Small Flat Encapsulation
        2: ["", "Encapsulation", "0.00%", "0.0000", "0.00%", "0.0000", "14.59", "5.25%"],
        # Row 3: Small Flat Intermittent
        3: ["", "Intermittent", "3.33%", "0.0746", "0.67%", "0.0149", "14.30", "2.62%"],
        # Row 4: Medium Apartment Out-of-Band
        4: ["Medium Apartment", "Out-of-Band", "14.05%", "0.0550", "1.31%", "0.0137", "27.88", "17.07%"],
        # Row 5: Medium Apartment Encapsulation
        5: ["", "Encapsulation", "16.70%", "0.0678", "1.31%", "0.0073", "34.09", "17.07%"],
        # Row 6: Medium Apartment Intermittent
        6: ["", "Intermittent", "11.01%", "0.0856", "1.31%", "0.0073", "31.05", "8.42%"],
        # Row 7: Large House Out-of-Band
        7: ["Large House", "Out-of-Band", "6.48%", "0.0641", "0.66%", "0.0066", "61.28", "11.05%"],
        # Row 8: Large House Encapsulation
        8: ["", "Encapsulation", "9.26%", "0.0979", "0.93%", "0.0101", "67.39", "11.05%"],
        # Row 9: Large House Intermittent
        9: ["", "Intermittent", "8.50%", "0.0797", "0.66%", "0.0066", "64.20", "5.48%"],
    }

    updated_het = False
    for row_idx, values in new_het_data.items():
        if row_idx < len(het_table.rows):
            row = het_table.rows[row_idx]
            for col_idx, val in enumerate(values):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = val
                        elif val:
                            para.add_run(val)
            updated_het = True
    if updated_het:
        changes.append("FIXED: Table 4.2 (Heterogeneity Results) updated with new experimental data from heterogeneity_results.csv")

    # =========================================================
    # 6. Fix Table 16 (Feature Importances) — updated RF values
    # =========================================================
    fi_table = doc.tables[16]
    new_fi_data = {
        1: ["rtt_estimate", "0.442"],
        2: ["total_delay", "0.439"],
        3: ["hop_count", "0.061"],
        4: ["path_length", "0.058"],
    }
    updated_fi = False
    for row_idx, values in new_fi_data.items():
        if row_idx < len(fi_table.rows):
            row = fi_table.rows[row_idx]
            for col_idx, val in enumerate(values):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = val
                        elif val:
                            para.add_run(val)
            updated_fi = True
    if updated_fi:
        changes.append("FIXED: Table 4.4 (Feature Importances) updated — rtt_estimate=0.442, total_delay=0.439, hop_count=0.061, path_length=0.058")

    # =========================================================
    # 7. Fix Table 17 (ML Baseline Performance) — updated values
    # =========================================================
    ml_table = doc.tables[17]
    new_ml_data = {
        1: ["Small Flat", "\u2014", "\u2014", "\u2014", "0\u20131.67%", "< 1.5%"],
        2: ["Medium Apartment", "0.395", "0.500", "0.442", "11.01\u201316.70%", "1.31%"],
        3: ["Large House", "0.324", "0.431", "0.370", "6.48\u20139.26%", "0.66\u20130.93%"],
    }
    updated_ml = False
    for row_idx, values in new_ml_data.items():
        if row_idx < len(ml_table.rows):
            row = ml_table.rows[row_idx]
            for col_idx, val in enumerate(values):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    for para in cell.paragraphs:
                        for run in para.runs:
                            run.text = ""
                        if para.runs:
                            para.runs[0].text = val
                        elif val:
                            para.add_run(val)
            updated_ml = True
    if updated_ml:
        changes.append("FIXED: Table 4.5 (ML Baseline Performance) updated — Medium Apt: P=0.395, R=0.500, F1=0.442; Large House: P=0.324, R=0.431, F1=0.370")

    # =========================================================
    # 8. Fix stale inline text references in body paragraphs
    # =========================================================
    body_fixes = [
        ("83.3 percent recall", "50.0 percent recall"),
        ("83.3%", "50.0%"),
        ("18.72 percent", "16.70 percent"),
        ("18.72%", "16.70%"),
        ("3.5x", "2.0x"),
        ("3.5 times", "2.0 times"),
        ("forwarded_spike_factor of 3.5", "forwarded_spike_factor of 2.0"),
        ("neighbour_inconsistency_threshold of 1.5", "neighbour_inconsistency_threshold of 1.0"),
    ]
    for old, new in body_fixes:
        for para in doc.paragraphs:
            if old in para.text:
                replaced = replace_text_in_para(para, old, new)
                if replaced:
                    changes.append(f"FIXED: Inline text '{old}' → '{new}'")

    # =========================================================
    # SAVE
    # =========================================================
    doc.save(output_path)

    print("\n========================================")
    print("  CORRECTIONS APPLIED SUCCESSFULLY")
    print("========================================")
    print(f"  Output file: {output_path}\n")
    for i, c in enumerate(changes, 1):
        print(f"  {i:02d}. {c}")
    print(f"\n  Total: {len(changes)} corrections made.")


if __name__ == "__main__":
    fix_document(
        "22CG031840_BALOGUN_IREOLUWA_FYP_1.docx",
        "22CG031840_BALOGUN_IREOLUWA_FYP_CORRECTED.docx"
    )
