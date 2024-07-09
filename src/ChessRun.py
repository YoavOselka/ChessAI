import pygame as p
import ChessLogic, AIPlayer
import sys
from multiprocessing import Process, Queue

# Instructions to run the game:
# 1. Navigate to the chess-engine directory in terminal
# 2. Run the following commands:
#    source /Users/yoavoselka/Desktop/chess-engine/bin/activate
#    python3 -m pip install -U pygame --user
# 3. Navigate to the chess directory
# 4. Run the game with: python3 ChessMain.py

# Constants for the game
BOARD_WIDTH = BOARD_HEIGHT = 512
DIMENSION = 8  # Dimension of the chess board (8x8)
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15  # For animations
IMAGES = {}  # Dictionary to hold images of the pieces

def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))

def main():
    p.init()
    screen = p.display.set_mode((BOARD_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = ChessLogic.GameState()  # Initialize the game state
    valid_moves = game_state.getValidMoves()  # Get all valid moves for the current state
    move_made = False  # Flag variable for when a move is made
    animate = False  # Flag variable for when a move should be animated
    loadImages()  # Load images once before the main loop
    is_running = True
    square_selected = ()  # No square is selected initially
    player_clicks = []  # This will track player clicks (two tuples)
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    player_one = True  # If a human is playing white, this will be True, else False
    player_two = False  # If a human is playing black, this will be True, else False

    while is_running:
        player_turn = (game_state.white_to_move and player_one) or (not game_state.white_to_move and player_two)
        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()
            # Mouse handler
            elif e.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()  # (x, y) location of the mouse
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE
                    if square_selected == (row, col) or col >= 8:  # User clicked the same square twice
                        square_selected = ()  # Deselect
                        player_clicks = []  # Clear clicks
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)  # Append for both 1st and 2nd click
                    if len(player_clicks) == 2 and player_turn:  # After 2nd click
                        move = ChessLogic.Move(player_clicks[0], player_clicks[1], game_state.board)
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.makeMove(valid_moves[i])
                                move_made = True
                                animate = True
                                square_selected = ()  # Reset user clicks
                                player_clicks = []
                        if not move_made:
                            player_clicks = [square_selected]

            # Key handler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_r:  # Reset the game when 'r' is pressed
                    game_state = ChessLogic.GameState()
                    valid_moves = game_state.getValidMoves()
                    square_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True

        # AI move finder
        if not game_over and not player_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # Used to pass data between threads
                move_finder_process = Process(target= AIPlayer.findBestMove, args=(game_state, valid_moves, return_queue))
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = AIPlayer.findRandomMove(valid_moves)
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(game_state.move_log[-1], screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()

def drawGameState(screen, game_state, valid_moves, square_selected):
    drawBoard(screen)  # Draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # Draw pieces on top of those squares

def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def highlightSquares(screen, game_state, valid_moves, square_selected):
    # Highlight the last move
    if len(game_state.move_log) > 0:
        last_move = game_state.move_log[-1]
        last_move_highlight = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        last_move_highlight.set_alpha(100)  # Transparency level
        last_move_highlight.fill(p.Color('green'))
        screen.blit(last_move_highlight, (last_move.end_col * SQUARE_SIZE, last_move.end_row * SQUARE_SIZE))
    
    # Highlight the selected square and its valid moves
    if square_selected:
        row, col = square_selected
        # Check if the selected square has a piece that can be moved
        if game_state.board[row][col][0] == ('w' if game_state.white_to_move else 'b'):
            # Highlight the selected square
            selected_square_highlight = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            selected_square_highlight.set_alpha(100)  # Transparency level
            selected_square_highlight.fill(p.Color('blue'))
            screen.blit(selected_square_highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            
            # Highlight valid moves from the selected square
            move_highlight = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            move_highlight.set_alpha(100)  # Transparency level
            move_highlight.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(move_highlight, (move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def drawEndGameText(screen, text):
    font = p.font.SysFont("Comic Sans MS", 40, True, True)
    text_object = font.render(text, False, p.Color("Black"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))

def animateMove(move, screen, board, clock):
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 5  # Number of frames to move one square
    total_frames = (abs(d_row) + abs(d_col)) * frames_per_square

    for frame in range(total_frames + 1):
        # Calculate the current row and column for the moving piece
        current_row = move.start_row + d_row * frame / total_frames
        current_col = move.start_col + d_col * frame / total_frames
        
        # Redraw the board and pieces
        drawBoard(screen)
        drawPieces(screen, board)
        
        # Erase the piece from its ending square
        end_square_color = colors[(move.end_row + move.end_col) % 2]
        end_square_rect = p.Rect(move.end_col * SQUARE_SIZE, move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, end_square_color, end_square_rect)
        
        # If a piece was captured, draw it back onto its square
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + 1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square_rect = p.Rect(move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square_rect)
        
        # Draw the moving piece
        moving_piece_rect = p.Rect(current_col * SQUARE_SIZE, current_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        screen.blit(IMAGES[move.piece_moved], moving_piece_rect)
        
        # Update the display and control the frame rate
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
