# QA Status Report & Implementation Plan

## 1. Working Fine
* **Conveyor Physics**: Player is pushed correctly when on the moving sidewalk.
* **Mummy Release**: The trigger successfully releases the mummy.
* **Frankenstein Trigger**: Triggers and starts moving when the player is detected.
* **Ray Gun Visibility**: The ray gun is finally visible on the screen.
* **Victory Screen**: The game correctly displays the exit ASCII art.

## 2. Broken (Requires Fixes)
* **Room/Door Coloring**: Walkways and doors are not inheriting the specific map color (`room_color`). The visual paths need to be colorized properly.
* **Object Alignment (Floating)**: Doors and buttons (like the `doorbell`) are floating in the air. We need to revise the `(y * 50) // 200` logic and check offsets using the `exporter_test.py` or unit tests.
* **Mummy Spawn Position**: Spawns in the middle of the walkway instead of exactly at the tomb, making it get stuck.
* **Ray Gun AI & Fire Logic**: Currently only moves at the top. It needs to track the player's Y position, auto-fire when aligned, and the controller is invisible.
* **Teleporter Colors & Cabins**: The target destinations are all the same color, and the cabin color cycling is restricted incorrectly.
* **Trapdoor Rendering**: Open trapdoors are not visibly creating holes in the floor, and the switch is missing.
* **Conveyor Controller & State**: Controller is not visible, and the initial state isn't matching the map's start state.
* **Frankenstein AI & Physics**: Frankenstein is floating/flying. He needs strict gravity/walkway bounding and should only use ladders/poles to change elevation. In the Frankie map, the trapdoor is active but invisible.

## 3. Missing (To be Implemented)
* **Pytest for Alignment**: Add rendering tests using the `ZTUTORIAL` map to mathematically assert that objects sit on the walkways correctly.
* **Lightning Switch Assets**: Add explicit `ON` and `OFF` visual states to `assets.py`.
* **Force Field Countdown**: Add numbered animation frames for the force field switch countdown.
* **Ray Gun Controller Assets**: Add explicit `UP`, `DOWN`, `FIRE` states for the ray gun controller switch in `assets.py`.

## Action Plan
1. **Commit Plan**: Save this document to the project root as `QA_Status_Report.md`, commit it, and push to the remote repository.
2. **Fix Coordinate Rendering**: Set up Pytest to assert vertical mapping. Then fix the `y` coordinate projection for doors, buttons, mummies, and trapdoors so nothing floats.
3. **Fix Color Propagation**: Broadcast the room color from the engine and map it to `[room_color]`.
4. **Enhance AI**: Refine Frankie's pathfinding and the Ray Gun's Y-tracking logic.
5. **Update Assets**: Add the missing states to `assets.py` for Force Field timers, Ray Gun controllers, and Lightning switches.
