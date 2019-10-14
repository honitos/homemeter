#!/usr/bin/env python

# --
# -- include some basic libraries
from __future__ import print_function
import sys
import datetime
import time
from struct import *        # this way we integrate all the contents in the global namespace without using struct.-namespace

# windowing 
from modules.intuition import intuition
screen = None

# --
# -- configuring the logger
import logging
vlogformatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
termhandler = logging.StreamHandler()
termhandler.setFormatter(vlogformatter)
filehandler = logging.FileHandler("homeserver.log")
filehandler.setFormatter(vlogformatter)
vlog = logging.getLogger()
vlog.setLevel(logging.DEBUG)
vlog.addHandler(termhandler)
#vlog.addHandler(filehandler)


# --
# -- include sql-stuff
try:
    import MySQLdb
except ImportError:
    import pymysql as MySQLdb
sqldb = None

# -- define some configurration for the sql-access
DATABASE_HOSTNAME = "192.168.2.3"
DATABASE_NAME = "smartmeter"
DATABASE_USER = "smartmeter"
DATABASE_PASSWD = "smartmeter"
DATABASE_TABLE ="easymeter"
import warnings
# -- modify behaviour of warnings: they should be raise an exception to catch them
warnings.filterwarnings("error", category=MySQLdb.Warning)


# --------------------------------------------------------------------------------------
# --
# -- Define functions for rf24 and SQL handling
# --
# --------------------------------------------------------------------------------------

def mysql_init(host=DATABASE_HOSTNAME,db=DATABASE_NAME,user=DATABASE_USER,passwd=DATABASE_PASSWD):
    global sqldb 
    vlog.info("Initiating database-connections...")
    sqldb = MySQLdb.connect(host,db,user,passwd)
    sqlcursor = sqldb.cursor()
    sqlcursor.execute("SHOW tables")
    sqltables = [v for (v,) in sqlcursor] # make a list of sqlcursor
    if DATABASE_TABLE in sqltables:
        vlog.info("Table '%s' found, will be used for storing data.",DATABASE_TABLE)
    else:
        # Create a table to store the data, if it does not exists
        sqlcommand = "CREATE TABLE IF NOT EXISTS `%(DATABASE_TABLE)` (" % locals()
        sqlcommand+= "`SensorTime` int(10) unsigned NOT NULL DEFAULT '0',"
        sqlcommand+= "`Current` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`Total` int(4) unsigned DEFAULT NULL,"
        sqlcommand+= "`DateTime` datetime(3) NOT NULL DEFAULT '0000-00-00 00:00:00.000',"
        sqlcommand+= "PRIMARY KEY (`SensorTime`),"
        sqlcommand+= "UNIQUE KEY `SensorTime` (`SensorTime`),"
        sqlcommand+= "KEY `DateTime` (`DateTime`)"
        sqlcommand+= ") ENGINE=InnoDB DEFAULT CHARSET=latin1"
        try:
            vlog.warn("Table '%s' does not exist in database '%s', creating table..." % (DATABASE_TABLE,db))
            sqlcursor.execute(sqlcommand)

        except(MySQLdb.Warning) as e:
            vlog.warn(e)

        except(MySQLdb.Error, MySQLdb.Warning) as e:
            vlog.error("Table could not been created, due to following SQL-reason:")
            return False

        except:
            vlog.error("I am sorry, but we have an unhandled exception here:")
            e = sys.exc_info()[:2]
            #vlog.error("%s - Error (%s)" % e)
            vlog.error(e)
            return False

    return True

    
    
def mysql_insert(payload):
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
        sqlcursor = sqldb.cursor()
        sqlcursor.execute(sqlcommand)
        sqldb.commit()

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

    
def mysql_get(dt):
    now = datetime.datetime.utcnow()

    sqlcommand = "SELECT SensorTime,Total,DateTime FROM easymeter "
    sqlcommand += "WHERE DateTime> '" + dt + "' LIMIT 1"
    try:
        #vlog.debug("reading dataset for (%s): (%s) ",dt,sqlcommand)
        sqlcursor = sqldb.cursor()
        sqlcursor.execute(sqlcommand)
        return sqlcursor.fetchall()

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
        if mysql_init() == True:
            for a in range(12,0,-1):
                _dt = '2018-{month}-01'.format(month=str(a));
                _result = mysql_get(_dt);
                if _result:
                    _stand = _result[0][1];
                    _kw = _stand / 10000;
                    print('Zählerstand im {monat}: {stand}'.format(monat=str(a),stand=_kw));
    except:
        e = sys.exc_info()
        vlog.error(e)
        raise
                        
    finally:

        if sqldb:
            vlog.info("Closing database...")
            sqldb.close()

        vlog.debug("Program terminated...")


else:
    vlog.error("Dieses Programm kann nicht als Modul ausgeführt werden.")

exit()

