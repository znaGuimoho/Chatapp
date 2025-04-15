import zmq
from colorama import init, Fore, Style

init(autoreset=True)  # Auto-reset after each print

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:7934")
socket.setsockopt_string(zmq.SUBSCRIBE, "")

print("🖥️ Listening for messages from main.py...\n")

while True:
    msg = socket.recv_string()
    if msg.startswith("ROOM_CREATED|"):
        print(Fore.GREEN + "🟢 " + msg.split("|", 1)[1])
    elif msg.startswith("MESSAGE|"):
        print(Fore.BLUE + "🔵 " + msg.split("|", 1)[1])
    elif msg.startswith("JOIN|"):
        print(Fore.CYAN + " ⚪" + msg.split("|", 1)[1])
    elif msg.startswith("LEAVE|"):
        print(Fore.RED + "🔴 " + msg.split("|", 1)[1])
