# -*- coding: utf-8 -*-
import sys
import datetime
from struct import * # this way we integrate all the contents in the global namespace without using struct.-namespace

# --
# -- include sql-stuff
try:
    import MySQLdb
except ImportError:
    import pymysql as MySQLdb

import logging
import warnings
# -- modify behaviour of warnings: they should be raise an exception to catch them
warnings.filterwarnings("error", category=MySQLdb.Warning)

vlogformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
termhandler = logging.StreamHandler()
termhandler.setFormatter(vlogformatter)
filehandler = logging.FileHandler("homeserver.log")
filehandler.setFormatter(vlogformatter)
vlog = logging.getLogger()
vlog.setLevel(logging.INFO)
vlog.addHandler(termhandler)
#vlog.addHandler(filehandler)


# --------------------------------------------------------------------------------------
# -- Define functions for SQL handling
# --------------------------------------------------------------------------------------
class sql(object):
    db = None
    logger = None
    
    def loginfo(self, message):
        if self.logger:
            self.logger.info(message)
            
    def logwarn(self, message):
        if self.logger:
            self.logger.warn(message)

    def logerror(self, message):
        if self.logger:
            self.logger.error(message)

    def close(self):
        if self.db:
            self.db.close()
            
    def __init__(self, logger=None, host="192.168.2.3", db="smartmeter", user="", passwd="", table="easymeter"):
        self.host = host
        self.db = db
        self.user = user
        self.passwd = passwd
        self.table = table
        
        if logger:
            self.logger = logger
           
        self.loginfo("Initiating database-connections...")
        try:
            self.db = MySQLdb.connect(host, user, passwd, db)
            self.cursor = self.db.cursor()
            self.cursor.execute("SHOW tables")
            self.tables = [v for (v,) in self.cursor] # make a list of sqlcursor
            self.loginfo("tables: {a}".format(a=self.tables))
            if self.table in self.tables:
                self.loginfo("Table '{dt}' found, will be used for storing data.".format(dt=self.table))
            else:
                self.loginfo("Table '{dt}' NOT found, will be created.".format(dt=self.table))
                # Create a table to store the data, if it does not exists
                sqlcommand = "CREATE TABLE IF NOT EXISTS `{dt}` (".format(dt=self.table)
                sqlcommand+= "`SensorTime` int(10) unsigned NOT NULL DEFAULT '0',"
                sqlcommand+= "`Current` int(4) unsigned DEFAULT NULL,"
                sqlcommand+= "`Total` int(4) unsigned DEFAULT NULL,"
                sqlcommand+= "`DateTime` datetime(3) NOT NULL DEFAULT '0000-00-00 00:00:00.000',"
                sqlcommand+= "PRIMARY KEY (`SensorTime`),"
                sqlcommand+= "UNIQUE KEY `SensorTime` (`SensorTime`),"
                sqlcommand+= "KEY `DateTime` (`DateTime`)"
                sqlcommand+= ") ENGINE=InnoDB DEFAULT CHARSET=latin1"
                self.logwarn("Table '{t}' does not exist in database '{db}', creating table...".format(t=self.table,db=db))
                self.cursor.execute(sqlcommand)

        except(MySQLdb.Warning) as e:
            self.logwarn(e)

        except(MySQLdb.Error, MySQLdb.Warning) as e:
            self.logerror("SQLDB-Error (%d): %s" % (e.args[0], e.args[1]))

        except:
            self.logerror("Problem while initiation the sql-connection.:")
            e = sys.exc_info()[:2]
            #vlog.error("%s - Error (%s)" % e)
            self.logeerror(e)

    def insertDataset(self, payload):
        now = datetime.datetime.utcnow()
        actSensorTime,valTotal,valTarif1,valTarif2,valCurrent = unpack("<LLLLL", bytes(payload))

        sqlcommand = "INSERT INTO easymeter (SensorTime,Current,Total,Datetime) "
        sqlcommand += "VALUES ("
        sqlcommand += str(actSensorTime) + ","
        sqlcommand += str(valCurrent) + ","
        sqlcommand += str(valTotal) + ","
        sqlcommand += "Now(3))"
        try:
            #vlog.debug("sending to db: ",sql_command)
            self.cursor = self.db.cursor()
            self.cursor.execute(sqlcommand)
            self.db.commit()

        except(MySQLdb.Error,MySQLdb.Warning) as e:

            if e[0]==1061: #Already Exists Primary Key error
                self.logerror("SQLDB-Error: Dataset with SensorTime (%d) already exists, will be ignored." % actSensorTime)
            else:
                self.logerror("SQLDB-Error (%d): %s" % (e.args[0], e.args[1]))
            return False

        except:
            self.logeerror("I am sorry, but we have an unhandled exception here:")
            e = sys.exc_info()
            self.logerror(e)
            return False


        return True

    def getDatasetByDate(self, dt):
        now = datetime.datetime.utcnow()

        sqlcommand = "SELECT SensorTime,Total,DateTime FROM easymeter "
        sqlcommand += "WHERE DateTime> '" + dt + "' LIMIT 1"
        try:
            #vlog.debug("reading dataset for (%s): (%s) ",dt,sqlcommand)
            self.cursor = self.db.cursor()
            self.cursor.execute(sqlcommand)
            return self.cursor.fetchall()

        except(MySQLdb.Error,MySQLdb.Warning) as e:

            if e[0]==1061: #Already Exists Primary Key error
                vlog.error("SQLDB-Error: Dataset with SensorTime (%d) already exists, will be ignored.",actSensorTime)
            else:
                vlog.error("SQLDB-Error (%d): %s" % (e.args[0], e.args[1]))

        except:
            vlog.error("I am sorry, but we have an unhandled exception here:")
            e = sys.exc_info()
            vlog.error(e)
            return False


        return True

# --------------------------------------------------------------------------------------
# --
# -- main routine
# --
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        mysql = sql(vlog)
        if False:
            ostand = 0
            for a in range(1,26,1):
                _dt = '2018-01-{days}'.format(days=str(a))
                _result = mysql.getDatasetByDate(_dt)
                if _result:
                    stand = _result[0][1];
                    if ostand == 0:
                        ostand = stand
                    verbrauch = stand - ostand
                    kw = verbrauch / 10000.0
                    ostand = stand
                    data.append(kw)
                    print('Zählerstand im {monat}: {stand}'.format(monat=str(a),stand=verbrauch));
                   
    except:
        e = sys.exc_info()
        print(e)
        raise
                        
    finally:
        if mysql:
            mysql.close()
        print("Program terminated...")
    exit()