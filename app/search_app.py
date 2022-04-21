from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading

# User library
from utils import tweet
from utils import ingest_data

async_mode = None  # "threading", "eventlet" or "gevent"

# TODO: if there's time let's package these in the "create_app" function
# Some globals. Should be stored in a structure
app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)

# Insertion is "single" threaded, i.e. only one user can initiate the injection
insertLock = threading.Lock()
sockLock = threading.Lock()
readerThread = None
updaterThread = None
readerData = None

# Everytime we start clear up the data and init the schema
# fresh start.
ingest_data.fnInitSchemaData()

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
    dbConnection = tweet.fnConnect()

    lsTweets = tweet.fnGetAllTweets(dbConnection)
    print(lsTweets)

    tweet.fnDisconnect(dbConnection)

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
                doStream = False
                insertDelay = 0

                streamArg=request.args.get("stream")
                if streamArg is not None and streamArg == "1":
                    print("Info: Streaming mode enabled")
                    doStream = True
                else:
                    print("Warning: stream argument is not valid: ", streamArg)

                # Only relavent for streaming
                if doStream:
                    insertDelayArg=int(request.args.get("insertDelay"))
                    print("Info: stream delay is: ", insertDelayArg)

                doStream = False
                sampleArg=request.args.get("sample")
                if sampleArg is not None:
                    print("Arguments for insertion are: stream: {0}, delay: {1}, sample: {2}", streamArg, 
                            insertDelayArg, sampleArg)

                    readerData = ingest_data.fnGetReaderData(sampleArg, insertDelayArg)
                    readerData["isIngesting"] = True
                    readerThread = threading.Thread(target=ingest_data.fnReadThreaded, args=(readerData,))
                    readerThread.start()
                else:
                    # TODO: return meaningful error. Need 403 and possibly base.html template
                    print("Error: please specify a sample file to ingest")

            except Exception as error:
                print("Error while trigger job: ", error)
        
    return render_template("index.html")

@app.route("/clear")
def fnClearDB():
    global readerData
    # Prevent clearing of DB while data is being inserted
    with insertLock:
        print("Reader data is", readerData)
        okToClear = readerData is not None and not readerData["isIngesting"]
        if(okToClear):
            ingest_data.fnClearData(readerData)
        elif readerData is not None:
            # TODO: return meaningful error. Need 403 and possibly base.html template
            print("Error: currently ingesting data. Please wait ...")

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