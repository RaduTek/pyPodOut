import os

SCREEN_W = 640
SCREEN_H = 480
FPS = 30
TRANSITION_DURATION = 0.4   # seconds, horizontal slide between screens
VOLUME_STEP = 1 / 16        # volume change per key press
VOLUME_HUD_DURATION = 1.5   # seconds the volume overlay stays up
PREVIOUS_RESTART_THRESHOLD = 3.0   # seconds; "previous" restarts the track past this point

RES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "res")

BG_COLOR = (0, 0, 0)
TEXT_COLOR = (230, 230, 230)
TEXT_HIGHLIGHT_COLOR = (255, 255, 255)
TEXT_SECONDARY_COLOR = (176, 176, 176)

MARGIN_X = 8          # left/right content margin
TEXT_GAP = 12          # space between icon and text / text and chevron
# 480 - 40 = 440 = lcm(55, 88): exactly 8 rows of 55px or 5 rows of 88px below the bar.
STATUS_BAR_HEIGHT = 40
STATUS_BAR_FONT_SIZE = 26
TOP_OFFSET = STATUS_BAR_HEIGHT
MENU_FONT_SIZE = 30

# Overflowing text (a selected menu row, the Now Playing title) scrolls (marquee).
MARQUEE_SPEED = 60     # px/s the text slides while scrolling
MARQUEE_HOLD = 1.5     # seconds the text pauses at each end

# Scroll hint drawn at the right edge of overflowing menus (clear of the chevrons).
SCROLL_HINT_INSET = 1
SCROLL_HINT_WIDTH = 5
SCROLL_HINT_MIN_THUMB = 20
SCROLL_HINT_TRACK_COLOR = (45, 45, 45)
SCROLL_HINT_THUMB_COLOR = (175, 175, 175)
