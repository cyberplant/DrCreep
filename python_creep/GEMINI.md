# The Castles of Dr. Creep (Python Port) - Technical Knowledge Base

## Project Overview
This project is a modern Python port of the classic C64 game "The Castles of Dr. Creep". It consists of a headless authoritative **Game Engine**, a binary **Castle Parser**, and multiple **Clients** (ASCII/Pygame).

---

## Authoritative Game Engine (`engine/`)

### 1. Coordinate System & Scaling
*   **Play Area**: The play area is defined as **16 to 176 world units** horizontally and **0 to 200 units** vertically.
*   **Scaling**: 1 world unit = 2 pixels. The total display resolution is **320x200**.
*   **Walkway Thickness**: Walkways have a functional thickness of **8 world units**. This range (`y` to `y + 8`) is used to provide support for entities transitioning from ladders or poles.

### 2. Physics & Movement (Strict "No Gravity")
*   **Authoritative Pipeline**: Every tick (50Hz), the engine creates a "Proposal" for every entity. This proposal is filtered through every object in the room.
*   **Support System**: There is **no continuous gravity**. Entities only move if they have "support" (defined by a Walkway, Ladder, or Pole).
*   **Edge Blocking**: If an entity attempts to move horizontally off a walkway and `has_support` becomes `False`, the movement is blocked, and the entity halts at the edge.
*   **Trapdoors**: An open trapdoor explicitly denies support, triggering a "no support" state which blocks movement over the hole.

### 3. Entity AI
*   **Mummy**: Tracks the player's X-coordinate every 12 ticks. It ignores Y-differences and relentlessly pursues the player horizontally while respecting physics.
*   **Frankenstein**: Advanced tracking. He seeks the nearest vertical structure (ladder/pole) if the player is on a different level and uses it to bridge the gap.

### 4. Interactive Components
*   **Doors**: Wide entry zones (10 world units). Entering requires an `up` intent while aligned with the frame.
*   **Teleporters**: Destination Y-offset is `+32` relative to the target icon to ensure the player lands on the floor.
*   **Switches**:
    *   **Conveyor**: Cycles through `LEFT (0) -> OFF (1) -> RIGHT (2) -> OFF (1)`.
    *   **Trapdoor**: Proximity-based trigger (walk-over) for all entities.
    *   **Lightning**: Toggle state broadcasted to clients for visual sync.

---

## Asset Interpretation

### 1. File Origins
*   `CHAR.ROM`: Standard C64 character tiles (512 tiles, 8x8 pixels).
*   `OBJECT`: Contains Sprite Descriptors, Sprite Data, and Custom Tilesets.
    *   **Sprite Pointer Table**: Located at address `0x603B` (File offset `0x583D`).
    *   **Custom Tileset**: Starts at memory `0x1000` (File offset `0x800`).

### 2. Sprite Specifications
*   **Format**: 24x21 pixel blocks.
*   **Decoding**: Determined by the `flags` byte in the descriptor.
    *   **Multicolor (2-bit)**: Used for Player, Mummy, Frankie.
    *   **High-Res (1-bit)**: Used for Doors, Doorbells, and UI text.
*   **Key IDs**:
    *   `0-5`: Player (Walking/Idle).
    *   `6-8`: Door (Frame, Closed, Open).
    *   `9`: Doorbell.
    *   `0x4B-0x50`: Mummy.
    *   `0x84-0x8A`: Frankenstein.
    *   `108`: Raygun Laser.

---

## Client Implementations

### 1. ASCII Client (`clients/ascii/`)
*   Uses `Textual` and `Rich` for rendering.
*   **Depth Effect**: Walkways are rendered as 2 rows (`=` for surface, `/` for depth).
*   **Debug Mode**: Includes a sidebar with clickable `[+]`/`[-]` buttons that send `tweak` commands to the server.

### 2. Pygame-CE Client (`clients/pygame/`)
*   **Pixel-Perfect**: Uses extracted PNGs from original assets.
*   **Scaling**: Uses `pygame.transform.scale` to map the 320x200 world to 640x400.
*   **Transparency**: Uses `BLEND_RGBA_MULT` to colorize 1-bit tiles and sprites while preserving alpha.
*   **Screenshots**: **F12** captures the scaled game surface.

---

## Quality Assurance & Visual Fidelity

### 1. Automated Testing Suite (`tests/`)
*   **Room-Specific Tests**: Each room in `ZTUTORIAL` has a dedicated test file (e.g., `tests/test_room_0.py`).
*   **Visual Regression**: Every room test includes a `test_render` method that compares the Pygame output against optimized original screenshots in `Screenshots_OriginalGame/`.
*   **Thresholds**: A global threshold (currently 45%) is used to account for emulator artifacts and scaling differences.

### 2. Visual Fidelity QA Workflow
Before making any changes to rendering logic or component visuals, follow this mandatory process:
1.  **Record Baseline**: Run the tests and note the current difference percentages:
    `pytest tests/ -v -s | grep "VISUAL DIFF"`
2.  **Apply Changes**: Fulfill the implementation or refactoring task.
3.  **Verify Improvement/Regression**: Run the tests again and compare the new percentages against your recorded baseline.
    *   **Goal**: The percentage should decrease (better similarity) or stay the same.
    *   **Alert**: If the percentage increases significantly, investigate the visual regression.

---

## Tooling
*   `tools/asset_extractor.py`: Extracts RGBA tiles and auto-detects sprite modes.
*   `engine/png_exporter.py`: Renders a full room map to a pixel-accurate PNG for layout debugging.
*   `tests/`: Comprehensive test suite using `pytest`.
    *   `tests/conftest.py`: Shared fixtures for `engine` and `renderer`.
    *   `tests/utils.py`: Visual comparison and assertion helpers.

---

## Future Focus
*   Refining the "Image" object parsing in the engine.
*   Mapping all 256 sprite IDs to their respective game states.
*   Implementing the "Ray Gun" Y-tracking AI and fire timing.
