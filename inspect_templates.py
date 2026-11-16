from pptx import Presentation

def inspect(name, path):
    print(f"\n================ INSPECTING {name} ================")
    prs = Presentation(path)
    print(f"Number of slides: {len(prs.slides)}")
    print(f"Slide width: {prs.slide_width.inches:.2f} inches")
    print(f"Slide height: {prs.slide_height.inches:.2f} inches")
    
    # Check slide layouts
    print(f"Slide layouts available: {len(prs.slide_layouts)}")
    
    # Check slides content
    for idx, slide in enumerate(prs.slides):
        print(f"\nSlide {idx+1}:")
        for shape in slide.shapes:
            if shape.has_text_frame:
                print(f"  [Text] {shape.text[:100]}")
            elif shape.has_table:
                print(f"  [Table] with {len(shape.table.rows)} rows, {len(shape.table.columns)} columns")
            else:
                print(f"  [Shape] type: {shape.shape_type}")

inspect("Final Project Slide to Use", "Final Project Slide to Use.pptx")
inspect("Project Student Slide Template (2)", "Project Student Slide Template (2).pptx")
