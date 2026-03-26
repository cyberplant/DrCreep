# Object-Oriented Component Refactoring Plan

## 1. Executive Summary
Currently, the game engine's physics, interaction, and rendering logic are heavily centralized. `GameEngine._update()` and `handle_input()` contain large `if/elif` blocks that process every object type's behavior. While functional, this monolithic approach scales poorly as we add more complex interactions (like Frankenstein's AI or Ray Gun tracking) and makes porting to Pygame/Godot more difficult because visual assets and logic are disjointed.

The proposed refactor involves migrating to an Object-Oriented (OO) component system. Every game element (Door, Conveyor, Teleporter, Frankenstein) will be defined as its own Python class inheriting from a base `GameObject` class. These classes will encapsulate their specific logic, state management, and ASCII visual assets.

## 2. Analysis & Assessment

### Benefits
* **Encapsulation & Maintainability**: Logic for a `Conveyor` lives only in the `Conveyor` class. This isolates bugs and makes tweaking individual components much easier.
* **Unified Assets**: Moving the ASCII asset definitions (from `assets.py`) directly into the component classes ties the logic and visual representation together.
* **Simplified Main Loop**: The engine's `_update` loop becomes a simple iteration over objects calling `obj.update(tick)` and handling a standardized event queue.
* **Easier Porting**: When building the Pygame or Godot clients, they can directly query the component instances for their state and bounding boxes, providing a clean API rather than parsing a generic dictionary of properties.
* **Standardized Interaction**: We can implement a clean event system (e.g., `on_player_enter`, `on_interact`) instead of hardcoding coordinate math for every object type in the main loop.

### Drawbacks & Effort
* **Initial Refactoring Cost**: Breaking apart the monolithic `_update()` method will require significant effort and regression testing to ensure no physics or interactions are broken.
* **State Synchronization**: Currently, the engine broadcasts a simple dictionary. We will need to ensure our new component classes easily serialize their state for the TCP broadcast to the clients.

### Conclusion
**It is highly recommended.** The effort spent refactoring now will drastically reduce the friction of implementing the remaining bugs (like Frankie's AI and Teleporter routing) and will pave the way for the graphical clients.

## 3. Proposed Architecture

### The Base Component Interface
Every object will inherit from a base class that defines standardized lifecycle and interaction methods:

```python
class BaseComponent:
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.state = 0
    
    # --- Lifecycle ---
    def update(self, engine, tick):
        """Called every game tick. Handle movement, timers, AI here."""
        pass

    # --- Interaction Events ---
    def on_collide(self, engine, entity):
        """Triggered when an entity (Player, Frankie, Mummy) overlaps the bounding box."""
        pass
        
    def on_interact(self, engine, player):
        """Triggered when a player presses ACTION while in range."""
        pass

    # --- Data & Rendering ---
    def serialize(self):
        """Return a dictionary of state for network broadcast."""
        return {'type': self.type, 'x': self.x, 'y': self.y, 'state': self.state}

    def get_asset(self, tick):
        """Return the current ASCII frame and color mapping."""
        pass
```

### Event Resolution
Instead of manually checking `abs(player.x - obj.x)`, the Engine will manage a spatial hash or simple bounding-box collision check.
When a collision occurs, the engine calls `obj.on_collide(player)`. The object itself decides how to respond (e.g., a `Conveyor` modifies `player.vx`, a `Trapdoor` checks if it's open to let the player fall).

## 4. Implementation Plan

* **Phase 1: Base Classes & Serialization (Prep)**
  * Define `BaseComponent` and migrate the parser to instantiate specific subclasses (e.g., `DoorComponent(data)`) instead of generic dictionaries.
  * Ensure the new classes serialize back into the exact same JSON structure so the current ASCII client doesn't break immediately.
* **Phase 2: Encapsulate `update()` Logic**
  * Move the tick-based logic (e.g., Forcefield timers, Door animation ticks, Ray Gun movement) out of `GameEngine._update()` and into the respective `obj.update()` methods.
* **Phase 3: Standardize Interactions (`on_interact`)**
  * Move the `ACTION` button logic out of `handle_input()`. The engine will just detect which objects are near the player and call `obj.on_interact(player)`.
* **Phase 4: Standardize Collisions (`on_collide`)**
  * Move the walkway support, conveyor pushing, and trapdoor falling logic into the respective collision handlers.
* **Phase 5: Asset Migration**
  * Move the dictionaries from `assets.py` into class-level attributes on the components. Update the broadcast so the client receives the exact frame to render, simplifying `client.py`.

## 6. Post-Refactor Observations & Future Improvements

### 6.1 Known Issues (To be fixed in next PR)
* **Coordinate Inaccuracies**: Despite the structural cleanup, some objects still appear misaligned. A focused pass on coordinate scaling and map data interpretation is required.

### 6.2 Planned Features
* **Map Selection Menu**: Instead of an automatic restart, the engine should scan the `castles/` directory and present a list of valid maps for the player to choose from upon victory or start.
* **Entity Unification**: Consolidate `mummies`, `frankies`, and `players` into a single `entities` list in `GameState` to simplify the pipeline iteration even further.
