# Drawing helpers every app can use, so apps stay short.
# Sizes are given as a fraction of the screen, so the same app fits any screen:
# the 5-inch touchscreen standing up, lying down, or a window on the Mac.

import textwrap

import cv2
import pygame

WHITE, BLACK = (255, 255, 255), (16, 18, 28)
GRAY, DIM = (150, 156, 170), (60, 66, 84)
GREEN, RED, YELLOW, BLUE = (60, 200, 110), (235, 80, 80), (255, 200, 40), (70, 150, 255)

_fonts = {}


def unit(screen):
    """One "unit" is 1% of the screen's shorter side. Use it for sizes."""
    return min(screen.get_size()) / 100


def font(size):
    size = max(8, int(size))
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)       # pygame's built-in font
    return _fonts[size]


def text(screen, words, center, size=8, color=WHITE):
    """Writes words centered on a point. size is in units. Shrinks to fit the screen's width."""
    pixels = size * unit(screen)
    picture = font(pixels).render(str(words), True, color)
    room = screen.get_width() * 0.94
    if picture.get_width() > room:
        picture = font(pixels * room / picture.get_width()).render(str(words), True, color)
    box = picture.get_rect(center=(int(center[0]), int(center[1])))
    screen.blit(picture, box)
    return box


def paragraph(screen, words, center, size=5, color=WHITE):
    """Like text(), but long sentences wrap onto several lines instead of shrinking."""
    wide, high = screen.get_size()
    letters_per_line = int(wide / (size * unit(screen) * 0.42))
    lines = textwrap.wrap(str(words), letters_per_line) or [""]
    step = size * unit(screen) * 0.9
    top = center[1] - step * (len(lines) - 1) / 2
    for row, line in enumerate(lines):
        text(screen, line, (center[0], top + row * step), size, color)


def button(screen, rect, words, color=BLUE, chosen=False, size=6):
    """Draws a big rounded touch button. chosen=True gives it a bright outline."""
    rect = pygame.Rect(rect)
    radius = int(2 * unit(screen))
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    if chosen:
        pygame.draw.rect(screen, WHITE, rect, width=max(3, int(unit(screen))), border_radius=radius)
    text(screen, words, rect.center, size, WHITE)
    return rect


def camera_picture(screen, frame, rect):
    """Draws the camera's picture inside a box on the screen."""
    if frame is None:
        return
    rect = pygame.Rect(rect)
    small = cv2.resize(frame, (rect.width, rect.height))
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    picture = pygame.image.frombuffer(rgb.tobytes(), (rect.width, rect.height), "RGB")
    screen.blit(picture, rect)
    pygame.draw.rect(screen, WHITE, rect, width=2)


def robot_face(screen, center, size, eyes_open=True, color=GREEN):
    """The robot's face: two eyes that can blink."""
    x, y = center
    for side in (-1, 1):
        eye = pygame.Rect(0, 0, size * 0.5, size * (0.7 if eyes_open else 0.08))
        eye.center = (x + side * size * 0.5, y)
        pygame.draw.rect(screen, color, eye, border_radius=int(size * 0.15))
