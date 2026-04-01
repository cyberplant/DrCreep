import os
import sys
import pytest
import pygame
from unittest.mock import patch

# Ensure the root directory is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.game import GameEngine
from clients.pygame.renderer import PygameRenderer

@pytest.fixture
def renderer():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    # Dummy display needed for some Pygame operations
    pygame.display.set_mode((320, 200), pygame.NOFRAME) 
    return PygameRenderer(debug_mode=False)

@pytest.fixture
def engine():
    # Use ZTUTORIAL for testing and mock NetworkServer to prevent port conflicts.
    # We set debug_mode=True so that pytest can capture and show engine logs if run with -s
    with patch('engine.game.NetworkServer'):
        return GameEngine("run/data/castles/ZTUTORIAL", debug_mode=True)
