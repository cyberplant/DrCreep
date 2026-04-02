# Pygame QA Assessment & Task Tracking

## Overview
This document tracks the current QA issues identified in the Pygame implementation of The Castles of Dr. Creep. It serves as a central plan detailing the current status and task analysis for each issue to ensure our development state is always clear.

## Issue Tracker

### 1. Pole Movement and Walkway Offsets
*   **Status:** Completed
*   **Description:** When the player goes down on a pole, they cannot reach the floor. There might be hardcoded offsets preventing this. Visually, original game poles end at the walkway start (top), while stairs/ladders end at the walkway end (bottom).
*   **Task Analysis:**
    *   Investigate `engine/game.py` or `engine/components/` (specifically pole and player interaction) to identify and remove any hardcoded vertical offsets.
    *   Adjust the engine's physics and the Pygame renderer to ensure poles terminate at the top edge of walkways, while ladders extend to the bottom edge, matching the original game's layout logic.

### 2. Ladder/Pole Movement Restrictions and Animations
*   **Status:** Completed
*   **Description:** The user can currently move sideways while on a ladder or pole. This should only be allowed when they intersect with a walkway. Additionally, specific climbing sprites/animations for ladders and poles are missing.
*   **Task Analysis:**
    *   **Physics:** Update the player movement logic in the engine to block horizontal input (`dx`) if the player is actively on a ladder or pole, *unless* they are currently overlapping a walkway providing lateral support.
    *   **Graphics:** Locate the climbing sprites in the original assets (`data/sprite_contact_sheet.png` or `data/extracted_sprites/`). Update `clients/pygame/renderer.py` to utilize these animations when the player is moving vertically.

### 3. Walkway 3D Effect and Player Positioning
*   **Status:** Completed
*   **Description:** The player currently walks exactly on top of the walkway. They should walk in the 'middle' (vertically) to give a 3D depth sensation. The walkway's bottom line and rightmost pixels need to be brown to complete the 3D effect.
*   **Task Analysis:**
    *   **Positioning:** Adjust the vertical rendering offset of the player sprite relative to the walkway. The engine's definition of "support" remains the same, but the visual representation needs to shift down slightly.
    *   **Rendering:** Update the walkway rendering logic in Pygame. This involves drawing a brown border on the bottom and right edges of walkway tiles to simulate depth, either by modifying the base tile graphics or drawing primitive lines in the renderer.

### 4. Map View Rendering
*   **Status:** Completed
*   **Description:** The map view is currently rendering all black and not showing the castle layout.
*   **Task Analysis:**
    *   Investigate the map view state and rendering loop within the Pygame client. Identify why the parsed map data is failing to draw to the screen surface. Fix the rendering pipeline for the map state.

### 5. Doorbell / Button Coloring
*   **Status:** Completed
*   **Description:** The door opening button (doorbell) coloring is incorrect. It's a big circle with an inner circle and a black space between. Currently, the inner black space is being colored instead of the outer circle. The outer circle should match the corresponding door's color.
*   **Task Analysis:**
    *   The current sprite extraction or color replacement logic is targeting the wrong pixel values.
    *   Investigate using a multicolor sprite approach or refining the palette swapping logic in Pygame (`PixelArray` or mask colorization) to ensure only the correct outer ring of the doorbell sprite receives the target door color.

### 6. Door Opening Animation and Sound
*   **Status:** Completed
*   **Description:** Opening a door should play a specific sound and trigger a smooth bottom-to-top animation of the door sprite changing, rather than an immediate swap.
*   **Task Analysis:**
    *   **Animation:** Implement a transition effect in the renderer. When a door state changes to open, progressively reveal the "open" sprite from bottom to top over a few frames (e.g., using Pygame clipping rects), rather than an instantaneous frame swap.
    *   **Sound:** Identify the correct door opening sound effect from the original game assets and integrate a sound playback trigger into the door interaction logic.

### 7. Door Entry Transition Animation
*   **Status:** Completed
*   **Description:** Entering a door to change rooms should animate the player moving "inside" the door and gradually decreasing in size over ~1 second until gone.
*   **Task Analysis:**
    *   Introduce a new transient state in the engine or client (e.g., `ROOM_TRANSITION`) that temporarily suspends normal player control.
    *   Implement a visual effect in the Pygame renderer that scales down the player sprite (`pygame.transform.scale`) and centers it within the door frame over a set duration before completing the room transition.

### 8. Vertical Input Blocking and Switch Interactions
*   **Status:** Completed
*   **Description:** Pressing UP/DOWN without a ladder/pole should be blocked. Interacting with switches (like lightning) should toggle them based on matching the direction (e.g., if up-ON, pressing down toggles it). Lightning is missing "ON" animations and sound effects.
*   **Task Analysis:**
    *   **Input Blocking:** Refine player intent processing to ignore UP/DOWN inputs if there is no climbable object present, *except* when positioned over an interactable switch.
    *   **Switches:** Implement directional toggle logic for switches.
    *   **Lightning Visuals/Audio:** Locate the animated lightning sprites. Implement rendering logic to display them when the switch is active. Add the appropriate switch toggle sound effect.

### 9. Frankie Level Hole (Trapdoor) Blocking
*   **Status:** Completed
*   **Description:** The hole in the floor on the Frankie level currently allows the player to walk over it. It should act as a gap in the walkway preventing movement.
*   **Task Analysis:**
    *   Check the engine's representation of this "hole" in the parsed room data. It needs to correctly break the walkway support continuity.
    *   Ensure the engine's `has_support` check properly identifies this gap. According to the "strict no-gravity" rules, moving over a gap without support MUST block the movement at the edge. If `has_support` is false at the target horizontal position, the movement is denied.
