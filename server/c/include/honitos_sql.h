#ifndef HONITOS_SQL_H
#define HONITOS_SQL_H

#include <string>
#include <iostream>
#include <unistd.h>   // for usleep()
#include <stdio.h>
#include <stdlib.h>
#include <mysql.h>
//#include "mysql/my_global.h"
#include "mysql/mysql.h"

class honitos_sql
{
    public:
        MYSQL *connection;
        MYSQL_RES *query_result;

        void connect();
        int query(std::string sql_query);
        void free_result();
        void close();

        honitos_sql(std::string a0, std::string a1, std::string a2, std::string a3);
        virtual ~honitos_sql();
    protected:
    private:
        static const int MAX_RECONNECT_RETRIES = 10;
        int reconnect_retries;
        std::string conn_server;
        std::string conn_user;
        std::string conn_password;
        std::string conn_database;
};

#endif // HONITOS_SQL_H
