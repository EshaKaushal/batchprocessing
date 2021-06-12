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
import base64


delimiter='/'
environment = ''
bucket = ''
models = {}


def getDBString_PROD():

    # Format DB connection information
    sslmode = "sslmode=verify-ca"

    if not os.path.exists('.ssl'):
        os.makedirs('.ssl')

    filecontents = os.environ.get('PG_SSLROOTCERT')
    decoded_sslrootcert = base64.b64decode(filecontents)
    with open('.ssl/server-ca.pem', 'wb') as f:
        f.write(decoded_sslrootcert)

    filecontents = os.environ.get('PG_SSLCLIENT_CERT')
    decoded_sslclientcert = base64.b64decode(filecontents)
    with open('.ssl/client-cert.pem', 'wb') as f:
        f.write(decoded_sslclientcert)

    filecontents = os.environ.get('PG_SSL_CLIENT_KEY')
    decoded_sslclientkey = base64.b64decode(filecontents)
    with open('.ssl/client-key.pem', 'wb') as f:
        f.write(decoded_sslclientkey)

    os.chmod(".ssl/server-ca.pem", 0o600)
    os.chmod(".ssl/client-cert.pem", 0o600)
    os.chmod(".ssl/client-key.pem", 0o600)

    hostaddr = "hostaddr={}".format(os.environ.get('PG_HOST'))
    user = "user=postgres"
    dbname = "dbname=mgmt590"
    password = "password={}".format(os.environ.get('PG_PASSWORD'))

    sslrootcert = "sslrootcert=.ssl/server-ca.pem"
    sslcert = "sslcert=.ssl/client-cert.pem"
    sslkey = "sslkey=.ssl/client-key.pem"

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
    elif environment=='TEST':
        con = sql.connect("questionAnswerTest.db")
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

    print('Inside dataProcessor --> environment',environment )

    try:
        # fetch filed from the output directory
        folderName = '/pfs/out/'

        if not os.path.exists(folderName):
            print('Output folder from first pipeline not found')
        else:
            print('Output folder found')

            for file_name in [file for file in os.listdir(folderName) if file.endswith('.json')]:
                print('Found the json file')
                with open(folderName+ file_name) as json_file:
                    print('Loading the data')
                    data = json.load(json_file)
                    print('Loaded the data')

                # Save to database
                saveData(data,environment)

    except Exception as ex:
        print('Exception Occurred in pipeline 02 --> ' , ex)


if __name__ == "__main__":
    logging.info('Inside main() --> Pipeline 02')
    main()
