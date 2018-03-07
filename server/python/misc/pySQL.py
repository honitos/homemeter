import MySQLdb
from datetime import datetime

now = datetime.utcnow()
#timestamp = totimestamp(now)
timestamp = now #"2016-02-11 18:42:33"
print timestamp


db = MySQLdb.connect(	host="192.168.2.3",
						db="smartmeter",
						user="smartmeter",
						passwd="smartmeter")
print("connected.")
cursor = db.cursor()
cursor.execute("SHOW fields from easymeter")
result = cursor.fetchall()
for i in result:
	print (i)

db.close()
print("2")
exit()

sql_command = "INSERT INTO Easymeter (SensorTime,Total,Leistung,Tagtarif,Spartarif)"
sql_command = sql_command + " VALUES ('" + str(timestamp) + "','2','3','4','5')"
print sql_command

cursor = db.cursor()
cursor.execute(sql_command)
db.commit()
print cursor.fetchall()

db.close()

