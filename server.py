from bottle import route, get, run, request, template, static_file, redirect
import sqlite3
import requests
import json
import os

tenant_id = '7dbf5411-2883-4825-ab13-0771a1b73e47'
client_id = 'cb38dadf-b6d6-40fb-a3b1-4365ab3a0682'
client_secret = 'ofV7Q~a5fhi2wT5qDrAZvTXmonjKJ5rYSp-th'


@route('/')
def home():
    return template('index.html')


@route('/landing')
def landing():
    return template('landing.html')


@route('/styles/<filename>')
def styles(filename):
    return static_file(filename, root='./')

@route('/scripts/<filename>')
def scripts(filename):
    return static_file(filename, root='./')


@get('/api/<query>')
def api(query):
    try:
        result = {}

        sqliteconnection = sqlite3.connect('data.db')
        cursor = sqliteconnection.cursor()

        sql_command = query
        data = cursor.execute(sql_command)

        temp = []
        for val in data.description:
            temp.append(val[0])

        result['columns'] = temp
        info = data.fetchall()

        vals = []

        for val in info:
            temp = []

            for i in val:
                temp.append(i)

            vals.append(temp)

    except Exception as e:
        return {'ok': False, 'error': str(e)}

    result['values'] = vals
    result['ok'] = True

    sqliteconnection.close()

    return result


@get('/token')
def token():
    code = request.query['code']

    url = 'https://login.microsoftonline.com/'+tenant_id+'/oauth2/v2.0/token'

    data = {
        'Host': 'login.microsoftonline.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': 'http://localhost:8080/token',
        'scope': 'offline_access https://graph.microsoft.com/.default',
        'grant_type': 'authorization_code'
    }

    response = requests.post(url, data=data)
    refresh_token = response.json()['refresh_token']

    if not os.path.isfile('refresh-tokens.json'):
        f = open('refresh-tokens.json', 'w')
        f.write('{}')
        f.close()

    f = open('refresh-tokens.json', 'r')
    refresh_tokens = json.load(f)
    f.close()

    url = 'https://graph.microsoft.com/v1.0/me/'
    header = {'Authorization': 'Bearer '+response.json()['access_token']}

    user_id = requests.get(url, headers=header).json()['id']

    refresh_tokens[user_id] = refresh_token

    f = open('refresh-tokens.json', 'w')
    json.dump(refresh_tokens, f, indent=4)
    f.close()

    redirect('/consent-thank-you')


@route('/consent')
def get_user_consent():
    url = 'https://login.microsoftonline.com/'+tenant_id+'/oauth2/v2.0/authorize? \
    client_id='+client_id+' \
    &response_type=code \
    &redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Ftoken \
    &response_mode=query \
    &scope=offline_access%20https://graph.microsoft.com/.default\
    &state=12345'

    redirect(url)


@route('/consent-thank-you')
def consent_acknowledgment():
    return 'Thank you for consenting. You may close this tab'


run(host='localhost', port=8080)
