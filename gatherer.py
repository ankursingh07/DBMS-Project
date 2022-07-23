import json
import requests
import sqlite3
import pandas

tenant_id = '7dbf5411-2883-4825-ab13-0771a1b73e47'
client_id = 'cb38dadf-b6d6-40fb-a3b1-4365ab3a0682'
client_secret = 'ofV7Q~a5fhi2wT5qDrAZvTXmonjKJ5rYSp-th'


def get_access_token():
    '''Obtain an access token from Microsoft by calling Oauth2 /token endpoint'''

    url = 'https://login.microsoftonline.com/' + tenant_id + '/oauth2/v2.0/token/'

    data = {
        'Host': 'login.microsoftonline.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }

    response = requests.post(url, data=data)
    return response.json()['access_token']


def get_all_users():
    '''Write the list of all users in the team to database'''

    access_token = get_access_token()

    url = 'https://graph.microsoft.com/v1.0/users'
    header = {'Authorization': 'Bearer ' + access_token}

    users = requests.get(url, headers=header).json()['value']

    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    sql_command = 'CREATE TABLE IF NOT EXISTS USERS(USERID VARCHAR(36), EMAILID VARCHAR(100), NAME VARCHAR(100), TITLE VARCHAR(100), PHONENO VARCHAR(100), PRIMARY KEY(USERID, EMAILID));'
    cursor.execute(sql_command)

    for user in users:
        sql_command = 'INSERT OR IGNORE INTO USERS VALUES("%s", "%s", "%s", "%s", "%s");'%(user['id'], user['mail'], user['displayName'], user['jobTitle'], user['businessPhones'][0])
        cursor.execute(sql_command)

    sqliteconnection.commit()
    sqliteconnection.close()


def get_all_mails():
    '''Write the list of all mails in the team to database'''

    access_token = get_access_token()

    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    sql_command = 'SELECT USERID FROM USERS;'
    data = cursor.execute(sql_command)

    user_ids = data.fetchall()

    sql_command = 'CREATE TABLE IF NOT EXISTS EMAILS(ID VARCHAR(152), SENDER VARCHAR(36), RECEIVER VARCHAR(36), SUBJECT TEXT, BODY TEXT, DATETIME VARCHAR(20), PRIMARY KEY(ID), FOREIGN KEY (SENDER) REFERENCES USERS(USERID), FOREIGN KEY (RECEIVER) REFERENCES USERS(USERID));'
    cursor.execute(sql_command)

    for user_id in user_ids:
        id = user_id[0]

        url = 'https://graph.microsoft.com/v1.0/users/'+id+'/messages'
        header = {'Authorization': 'Bearer ' + access_token}

        while True:
            emails = requests.get(url, headers=header).json()

            for email in emails['value']:
                email['subject'] = email['subject'].replace('"', '""')
                email['body']['content'] = email['body']['content'].replace('"', '""')

                sql_command = 'INSERT OR IGNORE INTO EMAILS VALUES("%s", "%s", "%s", "%s", "%s", "%s");'%(email['id'], email['sender']['emailAddress']['address'], email['toRecipients'][0]['emailAddress']['address'], email['subject'], email['body']['content'], email['sentDateTime'])
                cursor.execute(sql_command)

            if '@odata.nextLink' not in emails:
                break
            else:
                url = emails['@odata.nextLink']

    sqliteconnection.commit()
    sqliteconnection.close()


def get_all_events():
    '''Write the list of all calendar events in the team to database'''

    access_token = get_access_token()

    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    sql_command = 'SELECT USERID FROM USERS;'
    data = cursor.execute(sql_command)

    user_ids = data.fetchall()

    sql_command = 'CREATE TABLE IF NOT EXISTS EVENTS(ID VARCHAR(152), OWNER VARCHAR(36), BODY TEXT, WEBLINK TEXT, DATETIME VARCHAR(20), PRIMARY KEY(ID), FOREIGN KEY (OWNER) REFERENCES USERS(USERID));'
    cursor.execute(sql_command)

    for user_id in user_ids:
        id = user_id[0]

        url = 'https://graph.microsoft.com/v1.0/users/'+id+'/events'
        header = {'Authorization': 'Bearer ' + access_token}

        while True:
            events = requests.get(url, headers=header).json()

            for event in events['value']:
                event['body']['content'] = event['body']['content'].replace('"', '""')

                sql_command = 'INSERT OR IGNORE INTO EVENTS VALUES("%s", "%s", "%s", "%s", "%s");'%(event['id'], event['organizer']['emailAddress']['address'], event['body']['content'], event['webLink'], event['createdDateTime'])
                cursor.execute(sql_command)

            if '@odata.nextLink' not in events:
                break
            else:
                url = events['@odata.nextLink']

    sqliteconnection.commit()
    sqliteconnection.close()


def get_user_access_token(refresh_token):
    url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'

    data = {
        'Host': 'login.microsoftonline.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'redirect_uri': 'http://localhost:8080/token',
        'scope': 'offline_access https://graph.microsoft.com/.default',
        'grant_type': 'refresh_token'
    }

    response = requests.post(url, data=data)
    return response.json()['access_token']


def get_all_conversations():
    '''Write all chats of all signed in users to the database'''

    f = open('refresh-tokens.json', 'r')
    users = json.load(f)
    f.close()

    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    sql_command = 'CREATE TABLE IF NOT EXISTS CONVERSATION(ID VARCHAR(91), TYPE VARCHAR(20));'
    cursor.execute(sql_command)

    sql_command = 'CREATE TABLE IF NOT EXISTS CHATS(ID VARCHAR(13), MESSAGE TEXT, SENDER VARCHAR(36), CONVERSATIONID VARCHAR(91), DATETIME VARCHAR(20), PRIMARY KEY(ID, CONVERSATIONID), FOREIGN KEY(CONVERSATIONID) REFERENCES CONVERSATION(ID));'
    cursor.execute(sql_command)

    for user in users:
        access_token = get_user_access_token(users[user])

        url = 'https://graph.microsoft.com/v1.0/users/'+user+'/chats/'
        header = {'Authorization': 'Bearer ' + access_token}

        response = requests.get(url, headers=header)
        conversations = response.json()['value']

        for conversation in conversations:
            sql_command = 'INSERT OR IGNORE INTO CONVERSATION VALUES("%s", "%s")'%(conversation['id'], conversation['chatType'])
            cursor.execute(sql_command)

            url = 'https://graph.microsoft.com/v1.0/users/'+user+'/chats/'+conversation['id']+'/messages'
            header = {'Authorization': 'Bearer ' + access_token}

            while True:
                chats = requests.get(url, headers=header).json()

                for chat in chats['value']:
                    if chat['messageType'] == 'message':
                        chat['body']['content'] = chat['body']['content'].replace('"', '""')

                        sql_command = 'INSERT OR IGNORE INTO CHATS VALUES("%s", "%s", "%s", "%s", "%s")'%(chat['id'], chat['body']['content'], chat['from']['user']['id'], chat['chatId'], chat['createdDateTime'])
                        cursor.execute(sql_command)

                if '@odata.nextLink' not in chats:
                    break
                else:
                    url = chats['@odata.nextLink']

    sqliteconnection.commit()
    sqliteconnection.close()


def get_all_todolists():
    '''Write todo lists of all signed in users to database'''

    f = open('refresh-tokens.json', 'r')
    users = json.load(f)
    f.close()

    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    sql_command = 'CREATE TABLE IF NOT EXISTS TODOLIST(ID VARCHAR(120), OWNER VARCHAR(36), NAME VARCHAR(100), SHARED BIT(1), PRIMARY KEY(ID), FOREIGN KEY(OWNER) REFERENCES USERS(USERID));'
    cursor.execute(sql_command)

    for user in users:
        access_token = get_user_access_token(users[user])

        url = 'https://graph.microsoft.com/v1.0/users/'+user+'/todo/lists/'
        header = {'Authorization': 'Bearer ' + access_token}

        response = requests.get(url, headers=header)
        todolists = response.json()['value']

        for todolist in todolists:
            sql_command = '''INSERT OR IGNORE INTO TODOLIST VALUES("%s", "%s", "%s", '%s')'''%(todolist['id'], user, todolist['displayName'], 1 if todolist['isOwner'] else 0)
            cursor.execute(sql_command)

    sqliteconnection.commit()
    sqliteconnection.close()


def desc(table_name):
    sqliteconnection = sqlite3.connect('data.db')
    cursor = sqliteconnection.cursor()

    cursor.execute('PRAGMA table_info("%s")'%table_name)

    column_names = []

    for column_name in cursor.description:
        column_names.append(column_name[0])

    records = []

    for record in cursor.fetchall():
        records.append(list(record))

    df = pandas.DataFrame(records, columns=column_names)
    df.drop(['cid'], axis=1, inplace=True)

    return df

