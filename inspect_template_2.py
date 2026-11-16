import sys
from pptx import Presentation

# Configure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

prs = Presentation("Project Student Slide Template (2).pptx")
print(f"Number of slides: {len(prs.slides)}")
print(f"Slide width: {prs.slide_width.inches:.2f} inches")
print(f"Slide height: {prs.slide_height.inches:.2f} inches")
print(f"Slide layouts available: {len(prs.slide_layouts)}")

for idx, slide in enumerate(prs.slides):
    print(f"\nSlide {idx+1}:")
    for shape in slide.shapes:
        if shape.has_text_frame:
            # strip out-of-range character for printing
            safe_text = shape.text.encode('utf-8', errors='ignore').decode('utf-8')[:120]
            print(f"  [Text] {safe_text}")
        elif shape.has_table:
            print(f"  [Table] with {len(shape.table.rows)} rows, {len(shape.table.columns)} columns")
        else:
            try:
                print(f"  [Shape] name: {shape.name}, type: {shape.shape_type}")
            except Exception:
                print("  [Shape] unknown type")
