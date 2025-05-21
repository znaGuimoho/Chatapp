from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase, ascii_lowercase
from werkzeug.utils import secure_filename
import mysql.connector
import os
import zmq

# MySQL setup
db = mysql.connector.connect(
    host="your_ip",
    user="root", #use your username
    password="your_password",
    database="chatapp",
    port=3306,
    auth_plugin='mysql_native_password'
)
mycursor = db.cursor()

# ZMQ logger (only bind if main process)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    context = zmq.Context()
    log_socket = context.socket(zmq.PUB)
    log_socket.bind("tcp://127.0.0.1:7934")
else:
    log_socket = None

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(24).hex())
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'public_files')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
socketio = SocketIO(app, cors_allowed_origins=[])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return "Invalid file", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return "Invalid session", 400

    file_url = f"/files/{filename}"
    content = {"name": name, "message": f"<a href='{file_url}' target='_blank'>📁 {filename}</a>"}
    socketio.emit("message", content, to=room)

    mycursor.execute("INSERT INTO messages (room, sender, content) VALUES (%s, %s, %s)", (room, name, content['message']))
    db.commit()

    return "", 204

def generate_unique_code(length):
    while True:
        # Generate a random room code
        code = "".join(random.choice(ascii_uppercase) for _ in range(length * 3))

        # Check if the generated code already exists in the database
        mycursor.execute("SELECT * FROM rooms WHERE room = %s", (code,))
        print("created")
        if not mycursor.fetchone():
            print("created")
            break
    return code
@app.route("/", methods=["GET", "POST"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        code = request.form.get("code", "").strip().upper()  # Ensure uppercase for consistency
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name or len(name) > 20:
            return render_template("temp.html", error="Enter a valid name (1-20 chars).", code=code, name=name)

        if join and not code:
            return render_template("temp.html", error="Please enter a room code.", code=code, name=name)

        if create:  # Create room
            print("Create room logic triggered")  # Debugging line to check if this is being entered
            room = generate_unique_code(4)  # Generate unique room code
            try:
                print(f"Creating room: {room}")  # Debugging line
                # Insert the new room into the database
                mycursor.execute("INSERT INTO rooms (room, members) VALUES (%s, %s)", (room, 1))  # Start with 1 member
                db.commit()
                print(f"Room created and inserted: {room}")  # Debugging line
            except Exception as e:
                print(f"Room creation failed: {e}")  # Debugging line
                return render_template("temp.html", error=f"Room creation failed: {e}", code=code, name=name)

        else:  # If joining a room
            room = code
            print(f"Attempting to join room: {room}")  # Debugging line
            # Check if the room exists in the database
            mycursor.execute("SELECT * FROM rooms WHERE room = %s", (room,))
            result = mycursor.fetchone()
            print(f"Room exists: {result}")  # Debugging line
            
            if not result:
                return render_template("temp.html", error="Room does not exist.", code=code, name=name)

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("temp.html")


@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return redirect(url_for("home"))

    mycursor.execute("SELECT sender, content FROM messages WHERE room = %s", (room,))
    messages = [{"name": sender, "message": content} for sender, content in mycursor.fetchall()]
    return render_template("room.html", code=room, messages=messages)

@socketio.on("connect")
def handle_connect():
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    mycursor.execute("UPDATE rooms SET members = members + 1 WHERE room = %s", (room,))
    db.commit()
    if log_socket:
        log_socket.send_string(f"JOIN|{name} joined room {room}")

@socketio.on("disconnect")
def handle_disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    mycursor.execute("UPDATE rooms SET members = members - 1 WHERE room = %s", (room,))
    db.commit()
    mycursor.execute("SELECT members FROM rooms WHERE room = %s", (room,))
    result = mycursor.fetchone()

    if result and result[0] <= 0:
        mycursor.execute("DELETE FROM rooms WHERE room = %s", (room,))
        db.commit()
        if log_socket:
            log_socket.send_string(f"{room} has been deleted")

    send({"name": name, "message": "has left the room"}, to=room)
    if log_socket:
        log_socket.send_string(f"LEAVE|{name} left room {room}")

@socketio.on("message")
def handle_message(message):
    print("Received message:", message)

    name = session.get("name")
    room = session.get("room")

    if not room or not name or not message:
        return

    content = {"name": name, "message": message}
    send(content, to=room)

    mycursor.execute(
        "INSERT INTO messages (room, sender, content) VALUES (%s, %s, %s)",
        (room, name, message)
    )
    db.commit()





@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=3000)
