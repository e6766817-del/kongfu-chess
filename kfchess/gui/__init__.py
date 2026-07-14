"""GUI driver for kung-fu chess: same engine, board and rules as the
kfchess.texttests driver, but fed by real mouse events instead of
parsed stdin text, and rendered via cv2 (through the Img class in
img.py) instead of printed as ASCII.

kfchess.input.controller.Controller.handle_click_at_pixel/
handle_jump_at_pixel already take raw pixel coordinates -- the
texttests driver parses "CLICK x y" tokens out of text and forwards
those pixels to Controller; this driver forwards real mouse-event
pixels to the exact same Controller methods. No engine or input-layer
code changes between drivers, only where the pixel coordinates come
from and how the resulting board state is displayed.
"""
