"""Desktop UI for kung-fu chess: renders the board/pieces via cv2 (through
the Img class in img.py) and drives kfchess.engine.GameEngine in real time.

frontend/ depends one-way on kfchess/ (imports GameEngine, Board, Piece,
Controller, etc.) -- kfchess/ never imports anything from here.
"""
