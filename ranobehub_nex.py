import json
import requests
import sqlite3


def create_table_if_not_exists():
    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS ranobehub (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    en_title TEXT,
                    link TEXT,
                    description TEXT,
                    type_label TEXT,
                    year INTEGER,
                    image_path TEXT
                )
            ''')
            con.commit()
    except sqlite3.Error as e:
        print(f"An error occurred while creating the table: {e}")


def parse_ranobehub(login, password):
    create_table_if_not_exists()

    url = f'https://ranobehub.org/api/get/user/{login}/rate'
    session = requests.Session()
    response = session.get(url)
    tmp = response.text
    response_data = json.loads(tmp)

    with open('bookmarks_ranobehub.json', 'w', encoding='utf-8') as json_file:
        json.dump(response_data, json_file, ensure_ascii=False, indent=4)

    with open('bookmarks_ranobehub.json', 'r', encoding='utf-8') as f:
        jsons_line = json.load(f)

    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            ind = 0
            for i in jsons_line['data']['relations']:
                ind += 1
                cur.execute('''
                    INSERT INTO ranobehub (id, title, en_title, link, description, type_label, year, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ind,
                    i['ranobe']['names']['rus'],
                    i['ranobe']['names']['eng'],
                    i['ranobe']['url'],
                    i['ranobe']['synopsis'],
                    i['status']['title'],
                    i['ranobe']['year'],
                    i['ranobe']['posters']['big']
                ))
            con.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")