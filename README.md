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

### Frontend (Search)

This is still being discussed and debated on the right option. The "low tech" solution
would be ipywidgets in a Jupyter notebook. And that is the "simple" fall back. But will
also consider a Pythonic framework like Djanko which supports routing (endpoints) and 
web templates for a simple mostly static web page. The HTML front end will call the Python
middleware which in turn interacts with the data stores.

## Other Scripts

Also includes some notebooks for analyzing the data and will include a Python script for processing
the input data one record at a time. Once again, simulating streaming data.

Beyond the run script, will likely include some builds script for creating images with some
database and other dependencies.
