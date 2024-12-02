import requests
import json
import sqlite3


def create_table_if_not_exists():
    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS ranoberf (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    link TEXT,
                    updated TEXT,
                    chapter INTEGER,
                    opened_chapter TEXT,
                    image_path TEXT,
                    type_label TEXT
                )
            ''')
            con.commit()
    except sqlite3.Error as e:
        print(f"An error occurred while creating the table: {e}")


def parse_ranoberf(login, password):
    create_table_if_not_exists()
    site = 'https://xn--80ac9aeh6f.xn--p1ai/'
    bookmark_url = 'https://xn--80ac9aeh6f.xn--p1ai/v3/bookmarks?expand=book.verticalImage,chapter&sort=-updatedAt'
    auth_url = 'https://xn--80ac9aeh6f.xn--p1ai/v3/auth/login'
    headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
               (KHTML, like Gecko) Chromium/80.0.3987.160 Chrome/80.0.3987.163 \
               Safari/537.36'}
    session = requests.Session()
    response = session.get(site)
    data = {
        'email': login,
        'password': password
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.post(auth_url, data=data)
    if response.ok:
        csrf_cookie = session.cookies.get('_csrf')
        response_data = json.loads(response.content)
        token = response_data['token']
        print(f"Токен: {token}")
        headers = {
            'Authorization': f'Bearer {token}',
            'X-CSRF-Token': csrf_cookie
        }

        response = session.get(bookmark_url, headers=headers)
        if response.ok:
            print("Запрос успешно выполнен")
            tmp = response.text
            response_data = json.loads(tmp)
            with open('bookmarks_ranoberf.json', 'w', encoding='utf-8') as json_file:
                json.dump(response_data, json_file, ensure_ascii=False, indent=4)
        else:
            print("Ошибка при выполнении запроса")
    else:
        print("Ошибка авторизации")

    with open('bookmarks_ranoberf.json', 'r', encoding='utf-8') as f:
        jsons_line = json.load(f)

    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            ind = 0
            for i in jsons_line['items']:
                ind += 1
                cur.execute('''
                    INSERT INTO ranoberf (id, title, link, updated, chapter, opened_chapter, image_path, type_label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ind,
                    i['book']['title'],
                    'https://xn--80ac9aeh6f.xn--p1ai' + i['book']['url'],
                    i['updatedAt'],
                    i['chapter']['numberChapter'],
                    i['chapter']['title'],
                    'https://xn--80ac9aeh6f.xn--p1ai' + i['book']['url'],
                    i['type']

                ))
            con.commit()
            con.close()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
