import json
import os
import time
import logging
import glob
import csv
import os
import stat
import psycopg2
import sqlite3 as sql


delimiter='/'
environment = ''
bucket = ''
models = {}


def getDBString_PROD():

    # Format DB connection information
    sslmode = "sslmode=verify-ca"

    rootname = os.path.dirname

    # Format DB connection information
    # Format DB connection information
    sslrootcert = "sslrootcert={}".format(os.environ.get('PG_SSLROOTCERT'))
    sslcert = "sslcert={}".format(os.environ.get('PG_SSLCERT'))
    sslkey = "sslkey={}".format(os.environ.get('PG_SSLKEY'))

    #ensure all variables are defined in cloud shell
    hostaddr = "hostaddr={}".format(os.environ.get('PG_HOST'))
    user = "user=postgres"
    password = "password={}".format(os.environ.get('PG_PASSWORD'))
    dbname = "dbname=mgmt590"

    # Construct database connect string
    db_connect_string = " ".join([
        sslmode,
        sslrootcert,
        sslcert,
        sslkey,
        hostaddr,
        user,
        password,
        dbname
    ])

    return db_connect_string


def init_db(environment):
    print('Inside init_db' , environment)
    if environment == 'PROD':
        db_connect_string = getDBString_PROD()
        con = psycopg2.connect(db_connect_string)
    elif environment=='LOCAL':
        con = sql.connect("questionAnswer.db")
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS answers
                   (question text, context text, model text, answer text, timestamp int)''')
    return con

def saveData(data,environment):
    print('inside saveData')

    try:
        con = init_db(environment)
        cur = con.cursor()
        timestamp = int(time.time())
        for item in data['data']:
            print(item['question'])
            cur.execute(
                "INSERT INTO answers VALUES (:question,:context,:model,:answer,:timestamp)",
                {'question': item['question']
                    , 'context': item['context']
                    , 'model': 'distilled-bert'
                    , 'answer': item['answer']
                    , 'timestamp': timestamp})

            cur.execute('''CREATE TABLE IF NOT EXISTS answers
                              (question text, context text, model text, answer text, timestamp int)''')
        con.commit()
        con.close()
    except Exception as ex:
        print('Exception in saveData ' , ex)
        raise ex


def main():
    print('Inside dataProcessor')

    environment = 'PROD'

    print('Inside dataProcessor --> environment',environment)

    try:
        # fetch filed from the output directory
        folderName = os.getcwd()+'\pfs\out'

        if not os.path.exists(folderName):
            print('Output folder from first pipeline not found')
        else:
            print('Output folder found')
            for file_name in os.listdir(folderName):
                with open(folderName + delimiter+ file_name):
                    data = csv.DictReader(file_name)
                # Save to database
                saveData(data,environment)

    except Exception as ex:
        print('Exception Occurred in pipeline 02 --> ' , ex)

if __name__ == "__main__":
    logging.info('Inside main() --> Pipeline 02')
    main()
