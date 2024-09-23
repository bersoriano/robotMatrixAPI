from flask import Flask, request, jsonify
from typing import List, Tuple, Dict
import uuid
import time

app = Flask(__name__)

GRID_SIZE: int = 3
MOVE_TIMES: Dict[str, int] = {"U": 0, "D": 2, "L": 1, "R": 1}
VALID_MOVES: set[str] = {"U", "D", "L", "R"}

Position = Tuple[int, int]
Grid = List[List[str]]

games: Dict[str, Dict] = {}

def create_grid() -> Grid:
    return [[" " for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def is_valid_move(position: Position, direction: str) -> bool:
    x, y = position
    return (direction == "U" and y > 0) or \
           (direction == "D" and y < 2) or \
           (direction == "L" and x > 0) or \
           (direction == "R" and x < 2)

def get_new_position(position: Position, direction: str) -> Position:
    x, y = position
    if direction == "U": return (x, y - 1)
    if direction == "D": return (x, y + 1)
    if direction == "L": return (x - 1, y)
    if direction == "R": return (x + 1, y)
    return position

def apply_move(grid: Grid, position: Position, direction: str) -> Tuple[Grid, Position]:
    new_grid = [row[:] for row in grid]
    new_position = get_new_position(position, direction)
    x, y = position
    new_x, new_y = new_position
    new_grid[y][x] = " "
    new_grid[new_y][new_x] = "R"
    return new_grid, new_position

@app.route('/api/games', methods=['POST'])
def create_game():
    game_id = str(uuid.uuid4())
    grid = create_grid()
    position = (0, 0)
    grid[0][0] = "R"
    games[game_id] = {"grid": grid, "position": position, "moves": []}
    return jsonify({"game_id": game_id}), 201

@app.route('/api/games/<game_id>', methods=['GET'])
def get_game_state(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    game = games[game_id]
    return jsonify({
        "game_id": game_id,
        "grid": game["grid"],
        "position": game["position"]
    })

@app.route('/api/games/<game_id>/moves', methods=['POST'])
def add_move(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    move = request.json.get('move')
    if move not in VALID_MOVES:
        return jsonify({"error": "Invalid move"}), 400
    games[game_id]["moves"].append(move)
    return jsonify({"message": "Move added to queue"}), 201

@app.route('/api/games/<game_id>/process', methods=['PUT'])
def process_moves(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    game = games[game_id]
    moves_processed = 0
    invalid_moves = []
    for move in game["moves"]:
        if is_valid_move(game["position"], move):
            game["grid"], game["position"] = apply_move(game["grid"], game["position"], move)
            time.sleep(MOVE_TIMES[move])
            moves_processed += 1
        else:
            invalid_moves.append(move)
    game["moves"] = [move for move in game["moves"] if move not in invalid_moves]
    game["moves"] = game["moves"][moves_processed:]
    return jsonify({
        "moves_processed": moves_processed,
        "new_position": game["position"],
        "invalid_moves": invalid_moves
    })

@app.route('/api/games/<game_id>/moves', methods=['GET'])
def get_moves(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    return jsonify({"moves": games[game_id]["moves"]})

@app.route('/api/games/<game_id>', methods=['DELETE'])
def end_game(game_id):
    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404
    del games[game_id]
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)