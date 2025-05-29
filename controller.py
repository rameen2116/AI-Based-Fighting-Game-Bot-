
import socket
import json
from game_state import GameState
#from bot import fight
import sys
from bot import Bot
def connect(port):
    #For making a connection with the game
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("127.0.0.1", port))
    server_socket.listen(5)
    (client_socket, _) = server_socket.accept()
    print ("Connected to game!")
    return client_socket

def send(client_socket, command):
    #This function will send your updated command to Bizhawk so that game reacts according to your command.
    command_dict = command.object_to_dict()
    pay_load = json.dumps(command_dict).encode()
    client_socket.sendall(pay_load)

def receive(client_socket):
    #receive the game state and return game state
    pay_load = client_socket.recv(4096)
    input_dict = json.loads(pay_load.decode())
    game_state = GameState(input_dict)

    return game_state

def main():
    if (sys.argv[1]=='1'):
        client_socket = connect(9999)
    elif (sys.argv[1]=='2'):
        client_socket = connect(10000)
    current_game_state = None
    #print( current_game_state.is_round_over )
    bot=Bot()
    while (current_game_state is None) or (not current_game_state.is_round_over):

        current_game_state = receive(client_socket)
        bot_command = bot.fight(current_game_state,sys.argv[1])
        send(client_socket, bot_command)
if __name__ == '__main__':
   main()
