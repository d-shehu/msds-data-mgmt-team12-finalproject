from flask import Flask, render_template

from lib import mydb

app = Flask(__name__)

# Define the "routes" (endpoints) for the Flask web server which will service
# requests
@app.route("/")
def fnRootDir():
    dbConnection = mydb.fnConnectToMongo()

    lsTweets = mydb.fnGetAllTweets(dbConnection)
    print(lsTweets)

    mydb.fnDisconnectFromMongo(dbConnection)

    return render_template("index.html", tweets=lsTweets)