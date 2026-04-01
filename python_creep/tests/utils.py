import os
import pygame
import pytest
from PIL import Image, ImageChops

def get_image_diff_percent(img1, img2):
    """Calculates the percentage of differing pixels between two images."""
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.NEAREST)
        
    diff = ImageChops.difference(img1, img2)
    bbox = diff.getbbox()
    if not bbox:
        return 0.0 # perfectly identical
        
    diff_data = diff.convert("L").getdata()
    # If the image is all black, this is an error
    img1_data = img1.convert("L").getdata()
    if sum(img1_data) == 0:
         raise ValueError("Rendered image is all black!")
         
    diff_pixels = sum(1 for pixel in diff_data if pixel > 30) # threshold to ignore minor artifacts
    total_pixels = img1.width * img1.height
    
    return (diff_pixels / total_pixels) * 100.0

def auto_crop_c64(img):
    """Attempts to crop out emulator borders from a C64 screenshot."""
    bg = Image.new('RGB', img.size, (0, 0, 0))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        cropped = img.crop(bbox)
        return cropped
    return img

def assert_render_match(engine, renderer, room_id, screenshot_name, tmp_path, threshold=45.0):
    """Renders a room and asserts it matches the provided screenshot baseline."""
    # Setup player in the room to ensure it renders
    player = engine.state.players[0]
    player.room_id = room_id
    
    # Process several ticks to ensure things are initialized
    for _ in range(5):
        engine._update()
    
    state_dict = engine.get_state_dict()
    surface = renderer.render_state(state_dict)
    
    # Save the pygame surface
    rendered_path = tmp_path / f"rendered_room_{room_id}.png"
    pygame.image.save(surface, str(rendered_path))
    rendered_img = Image.open(rendered_path).convert("RGB")
    
    # Verify not all black
    extrema = rendered_img.convert("L").getextrema()
    assert extrema[1] > 0, f"Rendered room {room_id} is all black!"
    
    # Load original screenshot
    original_path = f"Screenshots_OriginalGame/{screenshot_name}"
    if not os.path.exists(original_path):
        pytest.skip(f"Original screenshot not found at {original_path}")
        
    original_img = Image.open(original_path).convert("RGB")
    cropped_original = auto_crop_c64(original_img)
    resized_original = cropped_original.resize(rendered_img.size, Image.Resampling.LANCZOS)
    
    # Save debug diffs
    diff_dir = "tests/diffs"
    os.makedirs(diff_dir, exist_ok=True)
    resized_original.save(f"{diff_dir}/original_{screenshot_name}")
    rendered_img.save(f"{diff_dir}/rendered_{screenshot_name}")
    
    diff_percent = get_image_diff_percent(rendered_img, resized_original)
    assert diff_percent < threshold, f"Room {room_id} differs from {screenshot_name} by {diff_percent:.2f}%"

def verify_not_black(img, name="Image"):
    """Asserts that the image is not all black."""
    extrema = img.convert("L").getextrema()
    assert extrema[1] > 0, f"{name} is all black!"
