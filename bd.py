import sqlite3
import PySimpleGUI as sg

con = sqlite3.connect('../database.db')
con.row_factory = sqlite3.Row
cur = con.cursor()


def load_books_from_db(table_name):
    try:
        cur.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cur.description]
        rows = cur.fetchall()
        books = [dict(zip(columns, row)) for row in rows]
        return books
    except sqlite3.Error as e:
        sg.popup_error(f"Ошибка при загрузке данных из таблицы {table_name}: {e}")
        return []


def save_auth_data(service_name, login, password):
    try:
        cur.execute("REPLACE INTO auth (service_name, login, password) VALUES (?, ?, ?)",
                    (service_name, login, password))
        con.commit()
    except sqlite3.Error as e:
        sg.popup_error(f"Ошибка при сохранении данных авторизации: {e}")


def load_auth_data(service_name):
    cur.execute("SELECT login, password FROM auth WHERE service_name = ?", (service_name,))
    row = cur.fetchone()
    return {'login': row['login'], 'password': row['password']} if row else None


def delete_auth_data(service_name):
    cur.execute("DELETE FROM auth WHERE service_name = ?", (service_name,))
    con.commit()
