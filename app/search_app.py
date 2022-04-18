from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading

# User library
from utils import mydb
from utils import ingest_data

async_mode = None  # "threading", "eventlet" or "gevent"

# Some globals. Should be stored in a structure
app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)

# Insertion is "single" threaded, i.e. only one user can initiate the injection
insertLock = threading.Lock()
sockLock = threading.Lock()
readerThread = None
updaterThread = None
readerData = None

# Long-lived (runs as soon as the 1st client connects)
def fnThreadUpdates():
    while True:
        global readerData
        progress = 0.0
        processed = 0
        doSend = False

        with insertLock:
            if readerData != None:
                progress = readerData["progress"]
                processed = readerData["processed"]
                doSend = progress > 0 or processed > 0
        
        # If there's a reason to broadcast
        if doSend:
            pctProgress = "{progress: .2f}%".format(progress=progress*100.0)
            socketio.emit('update', {'progress': pctProgress, 'processed': processed})
        
        socketio.sleep(3) # Don't spam the clients too frequently

# Define the "routes" (endpoints) for the Flask web server which will service
# requests
@app.route("/")
def fnRoot():
    return render_template("index.html")

@app.route("/search")
def fnSearch():
    dbConnection = mydb.fnConnectToMongo()

    lsTweets = mydb.fnGetAllTweets(dbConnection)
    print(lsTweets)

    mydb.fnDisconnectFromMongo(dbConnection)

    return render_template("index.html", tweets=lsTweets)

@app.route("/insert")
def fnInsert():
    global readerThread
    global readerData
    # Make sure one user can get in and trigger start/stop
    with insertLock:
        # Is thread in progress
        if (readerThread is None):
            try:
                readerData = ingest_data.fnGetReaderData()
                readerThread = threading.Thread(target=ingest_data.fnReadThreaded, args=(readerData,))
                readerThread.start()
            except Exception as error:
                print("Error while trigger job: ", error)
        
    return render_template("index.html")

@app.route("/stop")
def fnStop():
    global readerThread
    global readerData

    with insertLock:
        # Is thread in progress
        if (not readerThread is None):
            try:
                readerData["continue"] = False
                readerThread.join()
                readerData = None
                readerThread = None
            except Exception as error:
                print("Error while stopping job: ", error)
    # Send stop update
    socketio.emit('stopped')

@socketio.on('get_updates')
def fnGetUpdates():
    print("Received request from client: ")

@socketio.event
def connect():
    print("Client connected")
    global updaterThread
    with sockLock:
        try:
            if updaterThread is None:
                updaterThread = socketio.start_background_task(fnThreadUpdates)
        except Exception as error:
            print("Error while trying to start updater thread: ", error)