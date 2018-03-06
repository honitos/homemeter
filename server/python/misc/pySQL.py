import MySQLdb
from datetime import datetime

now = datetime.utcnow()
#timestamp = totimestamp(now)
timestamp = now #"2016-02-11 18:42:33"
print timestamp


db = MySQLdb.connect(host="localhost",db="Energy")


#cursor.execute("SHOW fields from Easymeter")
#result = cursor.fetchall()
#for i in result:
#	print (i)

sql_command = "INSERT INTO Easymeter (SensorTime,Total,Leistung,Tagtarif,Spartarif)"
sql_command = sql_command + " VALUES ('" + str(timestamp) + "','2','3','4','5')"
print sql_command

cursor = db.cursor()
cursor.execute(sql_command)
db.commit()
print cursor.fetchall()

db.close()

