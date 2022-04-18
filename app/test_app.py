import threading

import utils.ingest_data

def main():
    print("Insert records into databases via CLI!")

    readerData = fnGetReaderData()

    print("Starting thread to read/process tweets...")

    try:
        threadReader = threading.Thread(target=fnReadThreaded, args=(readerData,))
        threadReader.start()

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