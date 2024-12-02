import requests
from bs4 import BeautifulSoup
import json
import sqlite3


def create_table_if_not_exists():
    try:
        with sqlite3.connect('database.db') as con:
            cur = con.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS rulate (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    link TEXT,
                    description TEXT,
                    opened_chapter TEXT,
                    type_label TEXT,
                    image_path TEXT
                )
            ''')
            con.commit()
    except sqlite3.Error as e:
        print(f"An error occurred while creating the table: {e}")


def parse_rulate(login, password):
    create_table_if_not_exists()
    url = 'https://tl.rulate.ru/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    data = {
        'login[login]': login,
        'login[pass]': password
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.post(url, data=data)

    if response.status_code == 403:
        print('Не пустили, спим)')
        return []

    url_pars = 'https://tl.rulate.ru/bookmarks'
    response = session.post(url_pars, data={'type': '-1'})
    html = response.text
    soup = BeautifulSoup(html, 'lxml')

    books = []

    tbody = soup.find('tbody')
    if tbody:
        cards = tbody.find_all('tr')

        for card in cards:
            title = card.find('a', rel='tooltip').text.strip()
            link = 'https://tl.rulate.ru' + card.find('a', rel='tooltip')['href']
            description = card.find('a', rel='tooltip')['title'] if card.find('a', rel='tooltip').has_attr(
                'title') else ''
            chapters = card.find_all('p', class_='note')
            new_chapters = chapters[0].get_text(strip=True)
            opened_chapters = chapters[1].get_text(strip=True)
            opened_chapters = opened_chapters.replace("Продолжить чтение", "").strip()
            type_label = card.find(class_='type-label').text.strip()
            image_tag = card.find('img')
            image_url = 'https://tl.rulate.ru' + image_tag['src'] if image_tag else ''
            # image_path = save_image_as_png(image_url)

            books.append({
                "title": title,
                "link": link,
                "description": description,
                "new_chapters": new_chapters,
                "opened_chapters": opened_chapters,
                "type_label": type_label,
                "image_path": image_url
            })

            with open('bookmarks_rulate.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f'Сохранено {len(books)} книг в bookmarks_rulate.json')

            with open('bookmarks_rulate.json', 'r', encoding='utf-8') as f:
                jsons_line = json.load(f)

            try:
                with sqlite3.connect('database.db') as con:
                    cur = con.cursor()
                    ind = 0
                    for i in jsons_line:
                        ind += 1
                        cur.execute('''
                            INSERT INTO rulate (id, title, link, description, opened_chapter, type_label, image_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            ind,
                            i['title'],
                            i['link'],
                            i['description'],
                            i['opened_chapters'],
                            i['type_label'],
                            i['image_path']
                        ))
                    con.commit()
                    con.close()
            except sqlite3.Error as e:
                print(f"An error occurred: {e}")
