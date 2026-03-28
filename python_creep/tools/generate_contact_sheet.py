import os
from PIL import Image

def generate_contact_sheet(sprite_dir, output_path):
    files = sorted([f for f in os.listdir(sprite_dir) if f.endswith(".png")])
    if not files: return
    
    # Grid size
    cols = 16
    rows = (len(files) + cols - 1) // cols
    
    # Max dimensions
    max_w = 0
    max_h = 0
    for f in files:
        with Image.open(os.path.join(sprite_dir, f)) as img:
            max_w = max(max_w, img.width)
            max_h = max(max_h, img.height)
    
    # Add padding
    cell_w = max_w + 10
    cell_h = max_h + 20
    
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (50, 50, 50))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(sheet)
    
    for i, f in enumerate(files):
        sprite_id = f.split("_")[1].split(".")[0]
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        
        with Image.open(os.path.join(sprite_dir, f)) as img:
            # Upscale for visibility
            img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
            sheet.paste(img, (x + 5, y + 5))
            draw.text((x + 5, y + cell_h - 15), f"ID: {sprite_id}", fill=(255, 255, 255))
            
    sheet.save(output_path)
    print(f"Generated contact sheet at {output_path}")

if __name__ == "__main__":
    generate_contact_sheet("data/extracted_sprites", "data/sprite_contact_sheet.png")
