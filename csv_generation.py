import socket
import json
from game_state import GameState
from bot import Bot
import sys
import pandas as pd
import time
import os

def connect(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", port))
    server_socket.listen(5)
    (client_socket, _) = server_socket.accept()
    print("Connected to game!")
    return client_socket

def send(client_socket, command):
    command_dict = command.object_to_dict()
    pay_load = json.dumps(command_dict).encode()
    client_socket.sendall(pay_load)

def receive(client_socket):
    pay_load = client_socket.recv(4096)
    input_dict = json.loads(pay_load.decode())
    game_state = GameState(input_dict)
    return game_state

def main():
    if sys.argv[1] == '1':
        client_socket = connect(9999)
    elif sys.argv[1] == '2':
        client_socket = connect(10000)

    current_game_state = None
    bot = Bot()
    data_log = []

    try:
        while (current_game_state is None) or (not current_game_state.is_round_over):
            current_game_state = receive(client_socket)
            bot_command = bot.fight(current_game_state, sys.argv[1])
            send(client_socket, bot_command)

            # Unpack players and buttons
            p1 = current_game_state.player1
            p2 = current_game_state.player2
            p1_buttons = p1.player_buttons
            p2_buttons = p2.player_buttons

            # Prepare row
            row = {
                "timer": current_game_state.timer,
                "fight_result": current_game_state.fight_result,
                "has_round_started": current_game_state.has_round_started,
                "is_round_over": current_game_state.is_round_over,

                "Player1_ID": p1.player_id,
                "health": p1.health,
                "x_coord": p1.x_coord,
                "y_coord": p1.y_coord,
                "is_jumping": p1.is_jumping,
                "is_crouching": p1.is_crouching,
                "is_player_in_move": p1.is_player_in_move,
                "move_id": p1.move_id,
                "player1_buttons_Up": int(p1_buttons.up),
                "player1_buttons_Down": int(p1_buttons.down),
                "player1_buttons_Right": int(p1_buttons.right),
                "player1_buttons_Left": int(p1_buttons.left),
                "player1_buttons_Y": int(p1_buttons.Y),
                "player1_buttons_B": int(p1_buttons.B),
                "player1_buttons_A": int(p1_buttons.A),
                "player1_buttons_X": int(p1_buttons.X),
                "player1_buttons_L": int(p1_buttons.L),
                "player1_buttons_R": int(p1_buttons.R),

                "Player2_ID": p2.player_id,
                "Player2 health": p2.health,
                "Player2 x_coord": p2.x_coord,
                "Player2 y_coord": p2.y_coord,
                "Player2 is_jumping": p2.is_jumping,
                "Player2 is_crouching": p2.is_crouching,
                "Player2 is_player_in_move": p2.is_player_in_move,
                "Player2 move_id": p2.move_id,
                "player2_buttons up": int(p2_buttons.up),
                "player2_buttons down": int(p2_buttons.down),
                "player2_buttons right": int(p2_buttons.right),
                "player2_buttons left": int(p2_buttons.left),
            }

            data_log.append(row)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted. Saving data...")

    finally:
        # Create directory and append to CSV
        os.makedirs("logs", exist_ok=True)
        log_path = "logs/fight_data.csv"
        df = pd.DataFrame(data_log)

        if os.path.exists(log_path):
            df.to_csv(log_path, mode='a', header=False, index=False)
        else:
            df.to_csv(log_path, index=False)

        print(f"[INFO] Data saved to {log_path}")

if __name__ == '__main__':
    main()
