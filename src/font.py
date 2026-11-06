import pygame, os

_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_PATH  = os.path.join(_BASE_DIR, "assets", "fonts", "Earthbound.otf")
_font_cache = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.Font(_FONT_PATH, size)
        except Exception:
            _font_cache[key] = pygame.font.SysFont("consolas", size, bold=bold)
    return _font_cache[key]
