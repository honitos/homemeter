#include "honitos_sql.h"

honitos_sql::honitos_sql(std::string server,std::string user, std::string password, std::string database)
{
    //ctor
    conn_server = server;
    conn_user = user;
    conn_password = password;
    conn_database = database;
}

honitos_sql::~honitos_sql()
{
    //dtor
}

void honitos_sql::connect()
{
    this->connection = mysql_init(NULL);

    // connect to the database with the details attached.
    if (!mysql_real_connect(connection,conn_server.c_str(),
                                        conn_user.c_str(),
                                        conn_password.c_str(),
                                        conn_database.c_str(), 0, NULL, 0)) {
      printf("Connection error : %s\n", mysql_error(this->connection));
      exit(1);
    }

}

void honitos_sql::close()
{
    mysql_close(this->connection);
}

void honitos_sql::free_result()
{
    mysql_free_result(this->query_result);
}

int honitos_sql::query(std::string sql_query)
{
    // send the query to the database
    int error = 0;

    while(error == 0)
    {
        if(mysql_query(this->connection,sql_query.c_str())==0)
        {
            this->query_result = mysql_use_result(this->connection);
            break;
        }
        else
        {
            error = mysql_errno(this->connection);
            switch(error)
            {
            case 2006:
                // trying to reconnect to database ...
                this->reconnect_retries +=1;

                switch(this->reconnect_retries) {
                case 1:
                    std::cout << "trying to reconnect ...";
                    break;

                case this->MAX_RECONNECT_RETRIES:
                    std::cout << "max retries failed..." << std::endl;
                    exit(1);

                default:
                    std::cout << this->reconnect_retries << "..";
                    break;
                }
                usleep(2000);
                error = this->query(sql_query);
                break;

            default:
                printf("\nMySQL query error : %d, %s\n", error, mysql_error(this->connection));
                exit(1);
            }
        }

    }
    if(error == 0) this->reconnect_retries=0;

    return error;
}
