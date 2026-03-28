# Pygame-CE Client Implementation Phase 1: Asset Extraction & Foundation

## Objective
Extract original C64 assets (tiles and sprites) from the binary files and set up the foundation for a high-fidelity Pygame-CE client.

## Proposed Changes

### 1. Asset Extraction Tool (`tools/asset_extractor.py`)
- **Multicolor Bitmap Logic**: Implement the logic found in `src/vic-ii/bitmapMulticolor.cpp` to decode room backgrounds.
- **Sprite Extraction**: 
    - Use the pointer table at address `0x603B` (offset `0x583B` in `OBJECT` file) to find sprite data.
    - Decode 24x21 sprites (single and multicolor) into PNG sprite sheets.
- **Tile Extraction**: Decode `CHAR.ROM` into a PNG tileset.

### 2. Pygame Asset Loader (`clients/pygame/assets.py`)
- Create a class to load the extracted PNGs and provide easy access to specific sprite frames (Player, Mummy, Frankie).
- Implement the 16-color C64 palette.

### 3. Pygame Client Skeleton (`clients/pygame/client.py`)
- Set up the main loop and network receiver.
- Implement a basic `draw_room` function that uses the extracted tiles/bitmaps.

## Implementation Steps

1. **Step 1: Write `tools/asset_extractor.py`** to dump assets for visual inspection.
2. **Step 2: Create `clients/pygame/assets.py`** to manage these assets in Pygame.
3. **Step 3: Create `clients/pygame/client.py`** with the base rendering loop.

## Verification
- Visually verify the extracted sprite sheets and tilesets.
- Start the engine and the Pygame client; confirm it connects and draws a static room background.
