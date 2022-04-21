import threading
from time import sleep

from utils import ingest_data

def main():
    print("Insert records into databases via CLI!")

    # Start with a clean slate and do this at the start of the app
    ingest_data.fnInitSchemaData()

    # Run just the ingestion logic with the sample data and some parameters
    print("Enter sample filename to ingest (corona-out-2, corona-out-3):")
    sampleFilename = input()
    if(sampleFilename == ""):
        sampleFilename="corona-out-2"
    print("Insertion delay (milliseconds):")
    insertionDelay = input()
    if(insertionDelay == ""):
        insertionDelay=1
    else:
        insertionDelay=int(insertionDelay)

    print("Processing file ", sampleFilename, " with insertion delay ", insertionDelay)
    readerData = ingest_data.fnGetReaderData(sampleFilename, insertionDelay)

    print("Starting thread to read/process tweets...")
    try:
        threadReader = threading.Thread(target=ingest_data.fnReadThreaded, args=(readerData,))
        threadReader.start()

        # Wait for thread to start doing some work
        while(readerData["processed"] == 0):
            sleep(1)

        cmd = ""
        while(cmd != "stop" and readerData["progress"] < 1.0):
            print("Enter command:")
            cmd = input()
            if (cmd == "stop"):
                print("Stopping thread")
                readerData["continue"] = False # Signal to thread
                print("Waiting for thread to finish...")
                threadReader.join()
            elif (cmd == "wait"):
                print("Waiting for thread to finish...")
                threadReader.join()
            elif (cmd == "progress"):
                print("Processed number of tweets: ", readerData["processed"])
                print("Percent of file processed is ~: {progress:.2f}".format(
                    progress=readerData["progress"]*100.0))
    except Exception as error:
        print("Unexpected error while running thread: ", error)

    print("Thread processed number of tweets: ", readerData["processed"])
    print("Percent of file processed is ~: {progress:.2f}".format(
                    progress=readerData["progress"]*100.0))

if __name__ == "__main__":
    main()