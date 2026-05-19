import os
import sys
from PIL import Image, ImageDraw

# Add pinterest_engine path to import the generator
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pinterest_engine.pin_generator import create_split_screen_layout

def test_layout():
    # 1. Create a primary dummy base image (e.g. 1000x1500 px) with a diagonal line pattern
    base_img = Image.new("RGBA", (1000, 1500), (220, 200, 180, 255)) # beige tint
    draw = ImageDraw.Draw(base_img)
    for offset in range(0, 1500, 50):
        draw.line([(0, offset), (1000, offset + 1000)], fill=(180, 150, 120, 255), width=3)
    
    # Save base temp image
    temp_raw = "scratch/temp_raw.png"
    base_img.save(temp_raw)
    
    # 2. Create a secondary dummy image with a square pattern
    sec_img = Image.new("RGBA", (1000, 1500), (180, 220, 200, 255)) # green-teal tint
    sec_draw = ImageDraw.Draw(sec_img)
    for x in range(0, 1000, 80):
        for y in range(0, 1500, 80):
            sec_draw.rectangle([(x, y), (x+40, y+40)], fill=(140, 180, 160, 255))
            
    temp_sec = "scratch/temp_sec.png"
    sec_img.save(temp_sec)
    
    print("Testing layout OPTION A: Extreme Zoom Split...")
    create_split_screen_layout(
        temp_raw,
        "Dubai Chocolate Bar with Pistachio Cream",
        "final_pin_cli-test-pin-1.jpg",
        board_type="dessert"
    )
    
    print("\nTesting layout OPTION B: Two-Image Collage...")
    create_split_screen_layout(
        temp_raw,
        "Summer Dinner Recipes",
        "final_pin_cli-test-pin-2.jpg",
        board_type="dinner",
        secondary_image_path=temp_sec
    )
    
    # Clean up temp
    for path in [temp_raw, temp_sec]:
        if os.path.exists(path):
            os.remove(path)
    print("\nLayout test runs completed successfully!")

if __name__ == "__main__":
    test_layout()
