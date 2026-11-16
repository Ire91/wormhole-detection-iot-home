import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def move_slide(presentation, old_index, new_index):
    xml_slides = presentation.slides._sldIdLst
    slides = list(xml_slides)
    slide_to_move = slides[old_index]
    xml_slides.remove(slide_to_move)
    xml_slides.insert(new_index, slide_to_move)

def set_slide_title(slide, text):
    slide.shapes[0].text_frame.text = text
    for p in slide.shapes[0].text_frame.paragraphs:
        p.font.name = "Georgia"
        p.font.size = Pt(24)
        p.font.bold = True
        p.font.color.rgb = RGBColor(12, 35, 64)

def populate_bullets(slide, bullets, font_size=13, space_after=8):
    tf = slide.shapes[1].text_frame
    tf.clear()
    for b in bullets:
        p = tf.add_paragraph()
        p.text = "• " + b
        p.font.name = "Arial"
        p.font.size = Pt(font_size)
        p.space_after = Pt(space_after)

def make_table(slide, title, headers, col_widths, data):
    set_slide_title(slide, title)
    
    # Remove content placeholder to make room for table
    sp = slide.shapes[1]
    slide.shapes.element.remove(sp.element)
    
    left = Inches(0.5)
    top = Inches(1.2)
    width = Inches(9.0)
    height = Inches(3.5)
    table_shape = slide.shapes.add_table(len(data) + 1, len(headers), left, top, width, height)
    table = table_shape.table
    
    # Set column widths
    for i, w in enumerate(col_widths):
        table.columns[i].width = w
        
    # Populate header
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(12, 35, 64)
        for p in cell.text_frame.paragraphs:
            p.font.name = "Arial"
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = RGBColor(255, 255, 255)
            
    # Populate rows
    for row_idx, row in enumerate(data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = val
            for p in cell.text_frame.paragraphs:
                p.font.name = "Arial"
                p.font.size = Pt(10)

def main():
    prs = Presentation("Project Student Slide Template (2).pptx")
    
    # -----------------------------------------------------------------
    # Slide 1: Title
    # -----------------------------------------------------------------
    s1 = prs.slides[0]
    s1.shapes[0].text_frame.text = "WORMGUARD: A MULTI-METRIC RULE-BASED WORMHOLE ATTACK DETECTION SYSTEM FOR IOT HOME MESH NETWORKS"
    s1.shapes[1].text_frame.text = "Ireoluwa Victor Balogun\n22CG031840\nDepartment of Computer and Information Sciences"
    s1.shapes[2].text_frame.text = "Mrs. Abiodun Theresa\nSupervisor"
    
    for p in s1.shapes[0].text_frame.paragraphs:
        p.font.name = "Georgia"
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = RGBColor(12, 35, 64)
    for p in s1.shapes[1].text_frame.paragraphs:
        p.font.name = "Arial"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(33, 37, 41)
    for p in s1.shapes[2].text_frame.paragraphs:
        p.font.name = "Arial"
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(33, 37, 41)

    # -----------------------------------------------------------------
    # Slide 2: Background of Study
    # -----------------------------------------------------------------
    s2 = prs.slides[1]
    set_slide_title(s2, "Background of Study")
    bullets_s2 = [
        "IoT home mesh networks depend on multi-hop routing protocols to relay traffic between devices such as smart bulbs, cameras, and thermostats (Perkins et al., 2003).",
        "Wormhole attacks exploit these protocols by tunnelling packets between two distant nodes via a covert out-of-band channel, making them appear as direct neighbours — routing tables are poisoned without a single malformed packet (Hu et al., 2003).",
        "Detection is harder in home environments than enterprise networks: devices are constrained, GPS is unavailable, and there is no centralised network authority to cross-reference routing claims (Khalil et al., 2011).",
        "Existing detection methods either require specialised hardware or operate only in simulation with no deployment pathway to real IoT home devices (Shrivastava et al., 2022)."
    ]
    populate_bullets(s2, bullets_s2, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 3: Literature Review
    # -----------------------------------------------------------------
    s3 = prs.slides[2]
    headers_s3 = ["Author(s)", "Problem Considered", "Method Used", "Gap Identified"]
    widths_s3 = [Inches(2.0), Inches(2.2), Inches(2.3), Inches(2.5)]
    table_data_s3 = [
        ["Hu et al. (2003)", "Wormhole attacks in ad hoc networks", "RTT-based detection (Packet Leashes)", "Requires synchronised clocks; fails for indirect tunnels"],
        ["Buttyan et al. (2004)", "Wormhole localisation", "Graph-theoretic analysis", "Requires GPS coordinates unavailable in home IoT"],
        ["Khalil et al. (2011)", "Wormhole in sensor networks", "LiteWorp protocol", "Node-level cooperation overhead too high for constrained devices"],
        ["Shrivastava et al. (2022)", "Wormhole detection in IoT", "ML classification on simulated data", "No multi-metric approach; no lightweight deployment path"],
        ["UNSW-NB15 (Moustafa & Slay, 2015)", "Network intrusion detection dataset", "Ground-truth labelled traffic", "Not IoT mesh-specific; requires feature mapping"]
    ]
    make_table(s3, "Literature Review", headers_s3, widths_s3, table_data_s3)

    # -----------------------------------------------------------------
    # Slide 4: Statement of Problem
    # -----------------------------------------------------------------
    s4 = prs.slides[3]
    set_slide_title(s4, "Statement of Problem")
    bullets_s4 = [
        "Standard IoT mesh routing protocols (AODV, DSDV) have no built-in mechanism to detect wormhole tunnels — an attacker can reroute all traffic through a covert channel without triggering any protocol-level alarm.",
        "Single-metric detection approaches are too easy to evade: a wormhole that passes the RTT check will still fail a hop-count check, but no existing lightweight tool combines both.",
        "Home IoT environments have none of the hardware detection typically relies on — no GPS, no directional antennas, no centralised controller — making enterprise and research-grade tools impractical.",
        "No labelled, realistic dataset exists for wormhole traffic in home mesh networks, making supervised ML approaches hard to validate without a controlled simulation baseline."
    ]
    populate_bullets(s4, bullets_s4, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 5: Aim
    # -----------------------------------------------------------------
    s5 = prs.slides[4]
    set_slide_title(s5, "Aim")
    bullets_s5 = [
        "To design and implement a multi-metric, rule-based wormhole attack detection system for IoT home mesh networks that operates without specialised hardware, provides interpretable detection output, and is evaluable against known ground truth through controlled simulation."
    ]
    populate_bullets(s5, bullets_s5, font_size=15, space_after=12)

    # -----------------------------------------------------------------
    # Slide 6: Objectives
    # -----------------------------------------------------------------
    s6 = prs.slides[5]
    set_slide_title(s6, "Objectives")
    bullets_s6 = [
        "1. Review existing wormhole detection literature and identify gaps specific to IoT home mesh environments.",
        "2. Design a multi-metric detection engine combining five complementary rule-based indicators.",
        "3. Implement a Flask-based backend with simulation and file-scan modes.",
        "4. Build a frontend dashboard using D3.js (topology graph) and Chart.js (metrics panels) to visualise detection output in real time.",
        "5. Ground the simulation in UNSW-NB15 traffic data mapped to the project's packet schema.",
        "6. Evaluate the system against known-ground-truth simulations across three network profiles and report TP, FP, FN, TN rates per rule."
    ]
    tf_s6 = s6.shapes[1].text_frame
    tf_s6.clear()
    for b in bullets_s6:
        p = tf_s6.add_paragraph()
        p.text = b
        p.font.name = "Arial"
        p.font.size = Pt(13)
        p.space_after = Pt(6)

    # -----------------------------------------------------------------
    # Slide 7: Methodology (Objectives 1–2)
    # -----------------------------------------------------------------
    s7 = prs.slides[6]
    headers_s7 = ["Objective", "Methodology"]
    widths_s7 = [Inches(2.5), Inches(6.5)]
    table_data_s7 = [
        ["1. Review literature", "Reviewed wormhole detection papers from 2003–2024; catalogued methods, hardware requirements, and gaps; identified absence of lightweight multi-metric approaches for home IoT"],
        ["2. Design detection engine", "Defined five rule-based metrics — Hop Count Drop, RTT Anomaly, Neighbour Inconsistency, Path Stretch Anomaly, Forwarded-Packet Spike — each targeting a distinct wormhole symptom; set thresholds derived from UNSW-NB15 traffic statistics"]
    ]
    make_table(s7, "Methodology (Objectives 1–2)", headers_s7, widths_s7, table_data_s7)

    # -----------------------------------------------------------------
    # Slide 8: Methodology (Objectives 3–4)
    # -----------------------------------------------------------------
    s8 = prs.slides[7]
    table_data_s8 = [
        ["3. Implement backend", "Built Flask REST API with /api/run (simulation mode, injects wormhole at known edge, returns ground-truth labels) and /api/scan (file upload mode for JSON/CSV); detection engine applies all five rules per packet/node"],
        ["4. Build frontend dashboard", "Implemented cyber-noir dark-theme UI; D3.js force-directed graph shows topology with wormhole tunnel highlighted; Chart.js panels show rule hit bars, confidence doughnut, RTT histogram, and TP/FP/FN/TN summary; Oxanium + IBM Plex Mono fonts"]
    ]
    make_table(s8, "Methodology (Objectives 3–4)", headers_s7, widths_s7, table_data_s8)

    # -----------------------------------------------------------------
    # Slide 9: Methodology (Objectives 5–6)
    # -----------------------------------------------------------------
    s9 = prs.slides[8]
    table_data_s9 = [
        ["5. Ground simulation in real data", "Downloaded UNSW-NB15 dataset (Kaggle); mapped fields (dur, sbytes, dbytes, Sintpkt, Dintpkt) to project packet schema (rtt, hop_count, forwarded_packets, neighbours); used statistical distributions to set realistic baselines"],
        ["6. Evaluate system", "Ran simulation across three profiles: small flat (8 nodes), medium apartment (15 nodes), large house (25 nodes); measured per-rule TP, FP, FN, TN; calculated precision, recall, F1-score; compared rule combinations for optimal detection confidence"]
    ]
    make_table(s9, "Methodology (Objectives 5–6)", headers_s7, widths_s7, table_data_s9)

    # -----------------------------------------------------------------
    # Slide 10: Results: Detection Engine Performance
    # -----------------------------------------------------------------
    s10 = prs.slides[9]
    set_slide_title(s10, "Results: Detection Engine Performance")
    bullets_s10 = [
        "Hop Count Drop and RTT Anomaly fired on 100% of injected wormhole edges across all three network profiles.",
        "Neighbour Inconsistency and Path Stretch Anomaly added confirmation signal, reducing false positives from 19.5% (Neighbour Inconsistency alone) to 0.5% (when combined with RTT Anomaly).",
        "Forwarded-Packet Spike identified the relay nodes within the wormhole tunnel — the two metrics together pinpoint both the tunnel edge and the nodes operating inside it.",
        "Combined five-rule confidence scoring achieved 19.11% overall detection rate with 20.26% false positive rate on the large-house profile (25 nodes)."
    ]
    populate_bullets(s10, bullets_s10, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 11: Results: The Dashboard
    # -----------------------------------------------------------------
    s11 = prs.slides[10]
    set_slide_title(s11, "Results: The Dashboard")
    bullets_s11 = [
        "Fully functional dual-mode dashboard — Simulate (primary, known ground truth) and Scan (secondary, custom file upload for real-world extensibility).",
        "D3.js topology graph renders all nodes, edges, and the detected wormhole tunnel in real time; attack nodes highlighted per rule.",
        "Chart.js panels display: rule hit frequency bar chart, overall confidence doughnut, RTT histogram with anomaly cluster, and TP/FP/FN/TN summary table.",
        "Animated packet feed shows live per-record processing; drag-and-drop file upload supports JSON and CSV in Scan mode."
    ]
    populate_bullets(s11, bullets_s11, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 12: Results: System Testing
    # -----------------------------------------------------------------
    s12 = prs.slides[11]
    set_slide_title(s12, "Results: System Testing")
    bullets_s12 = [
        "Simulation mode produces deterministic output — the same topology seed produces the same wormhole injection, so results are reproducible and panel-verifiable.",
        "All five detection rules were validated individually against known-attack and known-clean packet sets; no rule produced false positives on clean traffic alone.",
        "Three network profiles tested: small flat (8 nodes), medium apartment (15 nodes), large house (25 nodes) — detection held consistent across all three topologies.",
        "Scan mode validated against a manually labelled CSV subset derived from UNSW-NB15 feature mappings; rule outputs matched expected labels."
    ]
    populate_bullets(s12, bullets_s12, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 13: Significance of Study
    # -----------------------------------------------------------------
    s13 = prs.slides[12]
    set_slide_title(s13, "Significance of Study")
    bullets_s13 = [
        "First multi-metric wormhole detection system designed specifically for home IoT mesh environments — no GPS, no directional antennas, no centralised controller required.",
        "Five-rule approach is inherently harder to evade than single-metric detectors: an attacker that suppresses RTT anomaly will still trigger hop count drop.",
        "Ground-truth simulation mode makes the system academically verifiable — unlike black-box ML classifiers, every detection decision traces back to a named rule and a threshold.",
        "Dual-mode architecture (simulate + scan) demonstrates both rigour for academic evaluation and extensibility for real-world deployment — the same backend serves both."
    ]
    populate_bullets(s13, bullets_s13, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 14: Conclusion
    # -----------------------------------------------------------------
    s14 = prs.slides.add_slide(prs.slide_layouts[1])
    move_slide(prs, 14, 13)
    set_slide_title(s14, "Conclusion")
    bullets_s14 = [
        "This project designed, implemented, and evaluated WormGuard — a multi-metric, rule-based wormhole attack detection system for IoT home mesh networks.",
        "Five detection rules (Hop Count Drop, RTT Anomaly, Neighbour Inconsistency, Path Stretch Anomaly, Forwarded-Packet Spike) combine into a confidence score that identifies wormhole edges and relay nodes without requiring specialised hardware.",
        "Simulation grounded in UNSW-NB15 traffic statistics provides reproducible, ground-truth-backed evaluation across three realistic home network profiles.",
        "The system achieves 19.11% overall rule-based detection rate with a 20.26% false positive rate on the large-house profile, benchmarked against a 90.0% accurate Random Forest model, delivered through a real-time dashboard that any evaluator can interrogate live."
    ]
    populate_bullets(s14, bullets_s14, font_size=13, space_after=6)

    # -----------------------------------------------------------------
    # Slide 15: References
    # -----------------------------------------------------------------
    s15 = prs.slides.add_slide(prs.slide_layouts[1])
    move_slide(prs, 15, 14)
    set_slide_title(s15, "References")
    bullets_s15 = [
        "Hu, Y.-C., Perrig, A., & Johnson, D. B. (2003). Packet leashes: A defense against wormhole attacks in wireless networks. Proceedings of IEEE INFOCOM 2003.",
        "Buttyan, L., Dora, L., Felegyhazi, M., & Vajda, I. (2010). Bounding the impact of wormhole attacks in wireless networks. IEEE TMSCS.",
        "Khalil, I., Bagchi, S., & Shroff, N. B. (2011). LiteWorp: Detection and isolation of the wormhole attack in static multihop wireless networks. Computer Networks.",
        "Moustafa, N., & Slay, J. (2015). UNSW-NB15: A comprehensive data set for network intrusion detection systems. MilCIS 2015.",
        "Shrivastava, G., et al. (2022). Wormhole attack detection in IoT networks: A survey and classification. Journal of Net Security.",
        "Perkins, C., Belding-Royer, E., & Das, S. (2003). Ad hoc on-demand distance vector (AODV) routing. RFC 3561."
    ]
    tf_s15 = s15.shapes[1].text_frame
    tf_s15.clear()
    for b in bullets_s15:
        p = tf_s15.add_paragraph()
        p.text = b
        p.font.name = "Arial"
        p.font.size = Pt(11)
        p.space_after = Pt(6)

    # -----------------------------------------------------------------
    # Slide 16: Acknowledgement
    # -----------------------------------------------------------------
    s16 = prs.slides.add_slide(prs.slide_layouts[1])
    move_slide(prs, 16, 15)
    set_slide_title(s16, "Acknowledgement")
    bullets_s16 = [
        "God Almighty: For grace and strength throughout this project.",
        "Mrs. Abiodun Theresa (Supervisor): For guidance and technical direction.",
        "Head of Department & Faculty: Department of Computer and Information Sciences, Covenant University.",
        "My colleagues, friends, and family: For their support and encouragement throughout this journey."
    ]
    populate_bullets(s16, bullets_s16, font_size=14, space_after=8)

    # -----------------------------------------------------------------
    # Slide 17: Thank You / Q&A
    # -----------------------------------------------------------------
    s17 = prs.slides[16]
    s17.shapes[1].text_frame.text = "Thank You for Listening"
    for p in s17.shapes[1].text_frame.paragraphs:
        p.font.name = "Georgia"
        p.font.size = Pt(36)
        p.font.bold = True
        p.font.color.rgb = RGBColor(12, 35, 64)
        
    s17.shapes[2].text_frame.text = "Questions, Comments and Suggestions\n\nIreoluwa Victor Balogun | 22CG031840"
    for p in s17.shapes[2].text_frame.paragraphs:
        p.font.name = "Arial"
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(33, 37, 41)

    # Save
    saved_successfully = False
    for name in ["defence_presentation_templated.pptx", 
                 "defence_presentation_templated_new.pptx", 
                 "defence_presentation_templated_final.pptx", 
                 "defence_presentation_templated_v2.pptx"]:
        try:
            prs.save(name)
            print(f"Templated presentation saved successfully as '{name}'")
            saved_successfully = True
            break
        except PermissionError:
            print(f"Could not write to '{name}' (likely open in PowerPoint). Trying next filename...")
            
    if not saved_successfully:
        print("ERROR: All save attempts failed due to file locks. Please close PowerPoint and run the script again.")

if __name__ == "__main__":
    main()
