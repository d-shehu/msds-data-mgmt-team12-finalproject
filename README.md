# MSDS: Data Management Final Project

This is the Github repo for Team 12's Final Project for the class, Special Topics in Data Science, aka Database Management class. This final project for that class and brings together the concepts
from the class including how to setup a relational and No-SQL datastore, query and configure
indices to optimize the performance. The app demos process, analyzing and searching a Twitter feed.

## Stack

### Backend

The stack is composed of a backend and frontend. The backend data stores are as follows

Redis: in-memory cache used to optimize certain queries

Mongo-DB: a doc-based database used to store the actual tweets. While the test data
is given a-priori. The app demos ingestion one record at a time to simulate the 
streaming nature of the data.

Postgres: used for data that changes infrequently such as user/profile

### Frontend & Search App

This is still being discussed and debated on the right option. The "low tech" solution
would be ipywidgets in a Jupyter notebook and that is the "simple" fall back. But will
also consider a Pythonic framework like Django which supports routing (endpoints) and 
web templates for a simple mostly static web page. The HTML front end will call the Python
middleware which in turn interacts with the data stores.

### Other Scripts

Also includes some notebooks for analyzing the data and will include a Python script for processing
the input data one record at a time. Once again, simulating streaming data. In order to work with
these notebooks, copy the <b>*.ipynb</b> files from the <b>notebooks</b> subdirectory to the
<b>input</b> in the <b>runtime</b> directory as specified in the <b>run.sh</b> script.

Beyond the run script, will likely include some builds script for creating images with some
database and other dependencies.


## Accessing the Application and Services

All apps and services that are part of this stack use the port range, 25xxx where xxx is the
used to differentiate among the services. To run the stack, simply <i>cd</i> into <b>services</b>
and execute <i>./run.sh. Follow the prompt which ask for a <b>password</b> for the data stores and <b>runtime</b> directory where the app and database data will live, along with notebooks.

To access the programmatic interface via the integrated Jupyter service, type in <b>http://<host>:25888</b> in the browser and Jupyter Hub should come up. The notebooks will be in the
<b>/work</b>.

The Docker hostname and ports for the respective services are as follows:

<table>
<tr><th>Service</th><th>Host</th><th>Port</th><th>Purpose</th</tr>
<tr><td>Jupyter</td><td>jupyterhub</td><td>25888</td><td>Programmatic access to data/app via Jupyter notebook</td></tr>
<tr><td>Postgres</td><td>pgdb</td><td>25432</td><td>Store static/structured data like users/locations</td></tr>
<tr><td>MongoDB</td><td>mongodb</td><td>25017</td><td>Store tweets and other dynamic data with flexible schema</td></tr>
<tr><td>Redis</td><td>redisdb</td><td>25379</td><td> Cacheimportant data during ingestion as well as querying</td></tr>
</table>

Each service is containerized and the respective CLI tools for each Database can be access by
executing <i>docker exec -it <host> bash. Once you see the <b>bash</b> prompt you can follow
instructions on how to access the CLI tools for each of the respective DBs. Please use the
password you passed in to the run script.

* Postgress Shell PSQL: https://www.postgresql.org/docs/current/app-psql.html
* Local Mongo On Default Port: https://www.mongodb.com/docs/v4.4/mongo/
* Redis CLI: https://redis.io/docs/manual/cli/
