import sys
from pptx import Presentation

sys.stdout.reconfigure(encoding='utf-8')
prs = Presentation("Project Student Slide Template (2).pptx")

for slide_idx, slide in enumerate(prs.slides):
    print(f"\nSlide {slide_idx+1}:")
    for shape_idx, shape in enumerate(slide.shapes):
        if shape.has_text_frame:
            text = shape.text.replace("\n", "\\n")
            print(f"  Shape {shape_idx}: Name='{shape.name}', Text='{text}'")
