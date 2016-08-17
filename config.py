# -*- coding: utf-8 -*-

secret_key = "Just try to guess me"
sql_config = {
    'database_type': 'mysql',
    'user': 'root',
    'password': 'daily555',
    'address': '123.57.58.91',
    'schema': 'dailytask',
    'conn_args': {'charset': 'utf8'},
}

sql_conn = "%s://%s:%s@%s/%s" % (sql_config['database_type'],
                                 sql_config['user'],
                                 sql_config['password'],
                                 sql_config['address'],
                                 sql_config['schema'])

