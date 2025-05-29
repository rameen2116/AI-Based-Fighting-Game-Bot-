import joblib
import pandas as pd
import numpy as np
from buttons import Buttons
from command import Command

class Bot:
    def __init__(self):
        self.fire_code = ["<", "!<", "v+<", "!v+!<", "v", "!v", "v+>", "!v+!>", ">+Y", "!>+!Y"]
        self.exe_code = 0
        self.start_fire = True
        self.remaining_code = []
        self.my_command = Command()
        self.buttn = Buttons()

        # Load trained model
        try:
            self.model = joblib.load('trained_fight_model.pkl')
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

        self.frame_count = 0
        self.model_update_interval = 1  # Faster reaction
        self.cached_prediction = [0] * 10
        self.debug = False
        self.last_features = None

    def get_game_state_features(self, current_game_state, player):
        if player == "1":
            opponent = current_game_state.player2
            player_obj = current_game_state.player1
        else:
            opponent = current_game_state.player1
            player_obj = current_game_state.player2

        features = {
            'timer': current_game_state.timer,
            'has_round_started': int(current_game_state.has_round_started),
            'is_round_over': int(current_game_state.is_round_over),
            'health': player_obj.health,
            'x_coord': player_obj.x_coord,
            'y_coord': player_obj.y_coord,
            'is_jumping': int(player_obj.is_jumping),
            'is_crouching': int(player_obj.is_crouching),
            'is_player_in_move': int(player_obj.is_player_in_move),
            'move_id': player_obj.move_id,
            'Player2 health': opponent.health,
            'Player2 x_coord': opponent.x_coord,
            'Player2 y_coord': opponent.y_coord,
            'Player2 is_jumping': int(opponent.is_jumping),
            'Player2 is_crouching': int(opponent.is_crouching),
            'Player2 is_player_in_move': int(opponent.is_player_in_move),
            'Player2 move_id': opponent.move_id
        }
        return pd.DataFrame([features])

    def fight(self, current_game_state, player):
        self.frame_count += 1

        if player == "1" and self.model:
            features = self.get_game_state_features(current_game_state, player)

            if (self.frame_count % self.model_update_interval == 0 or 
                not features.equals(self.last_features)):

                self.last_features = features
                self.cached_prediction = self.model.predict(features)[0]

                # Offensive augmentation
                p1 = current_game_state.player1
                p2 = current_game_state.player2
                distance = abs(p1.x_coord - p2.x_coord)

                # Always add bias toward offense
                self.cached_prediction[4] = 1  # Y
                self.cached_prediction[6] = 1  # A

                if distance < 60:
                    self.cached_prediction[5] = 1  # B
                    self.cached_prediction[7] = 1  # X
                elif distance > 120:
                    self.cached_prediction[2] = 1  # move toward
                    self.cached_prediction[8] = 1  # L
                    self.cached_prediction[9] = 1  # R

                if self.frame_count % 10 == 0:
                    # Add "combo burst" every 10 frames
                    self.cached_prediction[4] = 1
                    self.cached_prediction[5] = 1
                    self.cached_prediction[6] = 1
                    self.cached_prediction[7] = 1

            (
                self.buttn.up, self.buttn.down, self.buttn.right, self.buttn.left,
                self.buttn.Y, self.buttn.B, self.buttn.A, self.buttn.X,
                self.buttn.L, self.buttn.R
            ) = map(bool, self.cached_prediction)

            self.my_command.player_buttons = self.buttn

        elif player == "2":
            if self.frame_count % 8 == 0:
                if self.exe_code != 0:
                    self.run_command([], current_game_state.player2)
                else:
                    diff = current_game_state.player1.x_coord - current_game_state.player2.x_coord
                    toss = np.random.randint(3)
                    if diff > 60:
                        if toss == 0:
                            self.run_command([">", "-", "!>", "v+>", "-", "!v+!>", "v", "-", "!v", "v+<", "-", "!v+!<", ">+Y", "-", "!>+!Y"], current_game_state.player2)
                        elif toss == 1:
                            self.run_command([">+^+B", ">+^+B", "!>+!^+!B"], current_game_state.player2)
                        else:
                            self.run_command(["<", "-", "!<", "v+<", "-", "!v+!<", "v", "-", "!v", "v+>", "-", "!v+!>", ">+Y", "-", "!>+!Y"], current_game_state.player2)
                    elif diff < -60:
                        if toss == 0:
                            self.run_command(["<", "-", "!<", "v+<", "-", "!v+!<", "v", "-", "!v", "v+>", "-", "!v+!>", "<+Y", "-", "!<+!Y"], current_game_state.player2)
                        elif toss == 1:
                            self.run_command(["<+^+B", "<+^+B", "!<+!^+!B"], current_game_state.player2)
                        else:
                            self.run_command([">", "-", "!>", "v+>", "-", "!v+!>", "v", "-", "!v", "v+<", "-", "!v+!<", "<+Y", "-", "!<+!Y"], current_game_state.player2)
                    else:
                        if toss >= 1:
                            if diff < 0:
                                self.run_command(["<", "<", "!<"], current_game_state.player2)
                            else:
                                self.run_command([">", ">", "!>"], current_game_state.player2)
                        else:
                            self.run_command(["v+R", "v+R", "v+R", "!v+!R"], current_game_state.player2)

            self.my_command.player2_buttons = self.buttn

        return self.my_command

    def run_command(self, com, player):
        if self.exe_code - 1 == len(self.fire_code):
            self.exe_code = 0
            self.start_fire = False
        elif len(self.remaining_code) == 0:
            self.fire_code = com
            self.exe_code += 1
            self.remaining_code = self.fire_code[0:]
        else:
            self.exe_code += 1
            code = self.remaining_code[0]

            combos = {
                "v+<": lambda: (setattr(self.buttn, 'down', True), setattr(self.buttn, 'left', True)),
                "!v+!<": lambda: (setattr(self.buttn, 'down', False), setattr(self.buttn, 'left', False)),
                "v+>": lambda: (setattr(self.buttn, 'down', True), setattr(self.buttn, 'right', True)),
                "!v+!>": lambda: (setattr(self.buttn, 'down', False), setattr(self.buttn, 'right', False)),
                ">+Y": lambda: (setattr(self.buttn, 'right', True), setattr(self.buttn, 'Y', True)),
                "!>+!Y": lambda: (setattr(self.buttn, 'right', False), setattr(self.buttn, 'Y', False)),
                "<+Y": lambda: (setattr(self.buttn, 'left', True), setattr(self.buttn, 'Y', True)),
                "!<+!Y": lambda: (setattr(self.buttn, 'left', False), setattr(self.buttn, 'Y', False)),
                "v+R": lambda: (setattr(self.buttn, 'down', True), setattr(self.buttn, 'R', not player.player_buttons.R)),
                "!v+!R": lambda: (setattr(self.buttn, 'down', False), setattr(self.buttn, 'R', False))
            }

            if code in combos:
                combos[code]()
            elif code.startswith(">+^+") or code.startswith("<+^+"):
                dir_key = 'right' if code.startswith(">") else 'left'
                action = code[-1]
                setattr(self.buttn, dir_key, True)
                setattr(self.buttn, 'up', True)
                setattr(self.buttn, action, not getattr(player.player_buttons, action))
            elif code.startswith("!>+!^+!") or code.startswith("!<+!^+!"):
                dir_key = 'right' if code[1] == '>' else 'left'
                action = code[-1]
                setattr(self.buttn, dir_key, False)
                setattr(self.buttn, 'up', False)
                setattr(self.buttn, action, False)
            else:
                basic_map = {
                    "v": lambda: setattr(self.buttn, 'down', True),
                    "!v": lambda: setattr(self.buttn, 'down', False),
                    "<": lambda: setattr(self.buttn, 'left', True),
                    "!<": lambda: setattr(self.buttn, 'left', False),
                    ">": lambda: setattr(self.buttn, 'right', True),
                    "!>": lambda: setattr(self.buttn, 'right', False),
                    "^": lambda: setattr(self.buttn, 'up', True),
                    "!^": lambda: setattr(self.buttn, 'up', False),
                }
                if code in basic_map:
                    basic_map[code]()

            self.remaining_code = self.remaining_code[1:]
        return
