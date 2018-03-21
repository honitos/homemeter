Here are the files for the python (2.7) version of the server.

It receives the processed smartmeter-data from the arduino-client an writes it into a mariadb-database.
It uses the famous rf24-libs by TMRh20 (http://tmrh20.github.io/RF24/index.html).

Before starting, we need the python wrappers for alls three librarys RF24, RF24Network an RF24Mesh.
The wrappers uses libboost to make the c-libraries accessable from python.
Howto build the pythonlibs is describes here: http://tmrh20.github.io/RF24/Python.html
