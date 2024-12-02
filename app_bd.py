import PySimpleGUI as sg
import os
import PIL.Image
import io
import webbrowser
import sqlite3
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import hashlib
import threading
import queue
import time

from app_extension import reader
import ranoberf_next
import ranobehub_nex
import rulate_next
import bd

CACHE_DIR = 'image_cache'
os.makedirs(CACHE_DIR, exist_ok=True)
con = sqlite3.connect('../database.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

books_set = bd.load_books_from_db('rulate')
books_set2 = bd.load_books_from_db('ranobelib')
books_set3_raw = bd.load_books_from_db('ranoberf')
books_set4 = bd.load_books_from_db('ranobehub')


def extract_unique_books_db(books_raw):
    books = {}
    for item in books_raw:
        book_id = item.get('id')
        if not book_id:
            continue

        if book_id not in books:
            books[book_id] = {
                'id': book_id,
                'title': item.get('title', 'Без названия'),
                'description': item.get('description', "Описание отсутствует"),
                'link': item.get('link', ''),
                'image_path': item.get('image_path', ''),
                'chapter': item.get('updated', ''),
                'opened_chapter': item.get('opened_chapter', ''),
                'type_label': item.get('type_label', 'Неизвестный тип')  # Предполагается наличие такого поля
            }

    return list(books.values())


unique_books_set3 = extract_unique_books_db(books_set3_raw)
ranobehub = [row['title'] for row in books_set4]


def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def resize_image(image_path, resize=(200, 200)):
    img = None
    try:
        parsed_url = urlparse(image_path)
        if parsed_url.scheme in ('http', 'https'):
            cache_filename = os.path.join(CACHE_DIR, f"{get_url_hash(image_path)}.png")
            if os.path.exists(cache_filename):
                img = PIL.Image.open(cache_filename)
            else:
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                img = PIL.Image.open(io.BytesIO(response.content))
                img.thumbnail(resize)
                img.save(cache_filename, format="PNG")
        else:
            if not os.path.isabs(image_path):
                image_path = os.path.join('', image_path)
            if os.path.exists(image_path):
                img = PIL.Image.open(image_path)
                img.thumbnail(resize)
            else:
                sg.popup_error(f"Изображение не найдено: {image_path}")
                return None
    except requests.RequestException as e:
        sg.popup_error(f"Ошибка загрузки изображения из интернета: {e}")
        return None
    except PIL.UnidentifiedImageError as e:
        sg.popup_error(f"Ошибка обработки изображения: {e}")
        return None

    if img:
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        return bio.getvalue()
    return None


def authenticate(service_name, login, password):
    if not login or not password:
        sg.popup("Логин и пароль не могут быть пустыми!")
        return False
    try:
        if service_name == 'Rulate':
            rulate_next.parse_rulate(login, password)
        elif service_name == 'RanobeRF':
            ranoberf_next.parse_ranoberf(login, password)
        elif service_name == 'RanobeHub':
            ranobehub_nex.parse_ranobehub(login, password)
        elif service_name == 'RanobeLib':
            rulate_next.parse_rulate(login, password)
        else:
            sg.popup_error_with_traceback()
    except Exception as e:
        sg.popup_error(f"Ошибка при авторизации: {e}")
        return False


def show_settings_window():
    rulate_data = bd.load_auth_data('Rulate')
    ranoberf_data = bd.load_auth_data('RanobeRF')
    ranobehub_data = bd.load_auth_data('RanobeHub')
    ranobelib_data = bd.load_auth_data('RanobeLib')
    layout = [
        [sg.Text("Rulate:")],
        [sg.Text("Логин", size=(10, 1)), sg.Input(rulate_data['login'] if rulate_data else '', key='-SRC1_LOGIN-')],
        [sg.Text("Пароль", size=(10, 1)),
         sg.Input(rulate_data['password'] if rulate_data else '', key='-SRC1_PASSWORD-', password_char='*')],
        [sg.Text("RanobeRF:")],
        [sg.Text("Логин", size=(10, 1)), sg.Input(ranoberf_data['login'] if ranoberf_data else '', key='-SRC2_LOGIN-')],
        [sg.Text("Пароль", size=(10, 1)),
         sg.Input(ranoberf_data['password'] if ranoberf_data else '', key='-SRC2_PASSWORD-', password_char='*')],
        [sg.Text("RanobeHub:")],
        [sg.Text("Логин", size=(10, 1)),
         sg.Input(ranobehub_data['login'] if ranobehub_data else '', key='-SRC3_LOGIN-')],
        [sg.Text("Пароль", size=(10, 1)),
         sg.Input(ranobehub_data['password'] if ranobehub_data else '', key='-SRC3_PASSWORD-', password_char='*')],
        [sg.Text("RanobeLib:")],
        [sg.Text("Логин", size=(10, 1)),
         sg.Input(ranobelib_data['login'] if ranobelib_data else '', key='-SRC4_LOGIN-')],
        [sg.Text("Пароль", size=(10, 1)),
         sg.Input(ranobelib_data['password'] if ranobelib_data else '', key='-SRC4_PASSWORD-', password_char='*')],
        [sg.Button("Запомнить", key='-REMEMBER-'), sg.Button("Авторизация", key='-AUTHORIZE-'),
         sg.Button("Выход", key='-LOGOUT-')],
        [sg.HorizontalSeparator()],
        [sg.Button("Очистить кэш изображений", key='-CLEAR_CACHE-')],
        [sg.Button("Скачать все изображения", key='-DOWNLOAD_ALL_IMAGES-')]
    ]
    settings_window = sg.Window("Настройки", layout, modal=True)  # Сделать окно модальным
    progress_queue = queue.Queue()
    download_complete = False

    def download_all_images():
        total_images = 0
        image_paths = set()
        for book in books_set + books_set2 + unique_books_set3 + books_set4:
            image_path = book.get('image_path')
            if image_path:
                image_paths.add(image_path)

        total_images = len(image_paths)
        processed_images = 0

        for image_path in image_paths:
            parsed_url = urlparse(image_path)
            if parsed_url.scheme in ('http', 'https'):
                cache_filename = os.path.join(CACHE_DIR, f"{get_url_hash(image_path)}.png")
                if not os.path.exists(cache_filename):
                    try:
                        response = requests.get(image_path, timeout=10)
                        response.raise_for_status()
                        img = PIL.Image.open(io.BytesIO(response.content))
                        img.thumbnail((200, 200))
                        img.save(cache_filename, format="PNG")
                    except Exception as e:
                        progress_queue.put(f"Ошибка загрузки {image_path}: {e}")
            processed_images += 1
            progress_queue.put(processed_images)
        progress_queue.put("DONE")

    def show_progress_window(total):
        layout = [
            [sg.Text("Загрузка изображений...")],
            [sg.ProgressBar(max_value=total, orientation='h', size=(50, 20), key='-PROGRESS_BAR-')],
            [sg.Text("", key='-STATUS-')]]

        progress_window = sg.Window("Статус загрузки", layout, modal=True)
        progress_bar = progress_window['-PROGRESS_BAR-']
        status_text = progress_window['-STATUS-']

        while True:
            event, values = progress_window.read(timeout=100)
            if event == sg.WINDOW_CLOSED:
                break
            try:
                msg = progress_queue.get_nowait()
                if msg == "DONE":
                    status_text.update("Загрузка завершена.")
                    break
                elif isinstance(msg, int):
                    progress_bar.UpdateBar(msg)
                    status_text.update(f"Загружено {msg} из {total}")
                else:
                    status_text.update(msg)
            except queue.Empty:
                pass
            if download_complete:
                break
        progress_window.close()

    while True:
        event, values = settings_window.read()
        if event == sg.WINDOW_CLOSED:
            break
        elif event == '-REMEMBER-':
            service_data = {
                'Rulate': ('-SRC1_LOGIN-', '-SRC1_PASSWORD-'),
                'RanobeRF': ('-SRC2_LOGIN-', '-SRC2_PASSWORD-'),
                'RanobeHub': ('-SRC3_LOGIN-', '-SRC3_PASSWORD-'),
                'RanobeLib': ('-SRC4_LOGIN-', '-SRC4_PASSWORD-')}

            for service, keys in service_data.items():
                login, password = values[keys[0]], values[keys[1]]
                if login and password:
                    bd.save_auth_data(service, login, password)
            sg.popup("Данные запомнены!")
        elif event == '-AUTHORIZE-':
            try:
                service_data = {
                    'Rulate': ('-SRC1_LOGIN-', '-SRC1_PASSWORD-'),
                    'RanobeRF': ('-SRC2_LOGIN-', '-SRC2_PASSWORD-'),
                    'RanobeHub': ('-SRC3_LOGIN-', '-SRC3_PASSWORD-'),
                    'RanobeLib': ('-SRC4_LOGIN-', '-SRC4_PASSWORD-')}

                for service, keys in service_data.items():
                    login, password = values[keys[0]], values[keys[1]]
                    if login and password:
                        success = authenticate(service, login, password)
                        if success:
                            break
            except Exception as e:
                sg.popup(f"Ошибка: {e}")
        elif event == '-LOGOUT-':
            for service in ['Rulate', 'RanobeRF', 'RanobeHub', 'RanobeLib']:
                bd.delete_auth_data(service)
            sg.popup("Вы вышли из аккаунта и удалили данные.")
        elif event == '-CLEAR_CACHE-':
            try:
                files_removed = 0
                for filename in os.listdir(CACHE_DIR):
                    file_path = os.path.join(CACHE_DIR, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        files_removed += 1
                sg.popup(f"Кэш изображений очищен. Удалено файлов: {files_removed}")
            except Exception as e:
                sg.popup_error(f"Ошибка при очистке кэша: {e}")
        elif event == '-DOWNLOAD_ALL_IMAGES-':
            download_thread = threading.Thread(target=download_all_images, daemon=True)
            download_thread.start()
            total_images = len(set(
                book.get('image_path') for book in books_set + books_set2 + unique_books_set3 + books_set4 if
                book.get('image_path')
            ))
            show_progress_window(total_images)
    settings_window.close()


def update_book_info(selected_book):
    if not selected_book:
        return

    image_path = selected_book.get('image_path')
    image_data = resize_image(image_path, resize=(200, 200))
    if image_data:
        window['-IMAGE-'].update(data=image_data)
    else:
        window['-IMAGE-'].update(data=None)

    window['-TITLE-'].update(selected_book.get('title', ''))
    window['-DESCRIPTION-'].update(selected_book.get('description', ''))
    window['-LINK-'].update(selected_book.get('link', ''))
    window['-TYPE_LABEL-'].update(selected_book.get('type_label', 'Неизвестный тип'))
    window['-NEW_CHAPTERS-'].update(selected_book.get('updated', '-'))
    window['-OPENED_CHAPTERS-'].update(selected_book.get('opened_chapter', ''))


book_entry_layout = [
    [sg.Image(key='-IMAGE-', size=(200, 200))],  # Размер изображения
    [sg.Text("Название:", size=(15, 2)), sg.Text("", key='-TITLE-', size=(40, 3), auto_size_text=True)],
    [sg.Text("Описание:", size=(15, 1))],
    [sg.Multiline("", size=(60, 8), key='-DESCRIPTION-', disabled=True)],
    [sg.Text("Ссылка:", size=(15, 1)),
     sg.Text("", key='-LINK-', enable_events=True, text_color='blue', font=('Helvetica', 12, 'underline'), tooltip='Открыть ссылку', size=(60, 2))],
    [sg.Text("Обновлено:", size=(15, 1))],
    [sg.Text("", size=(40, 1), key='-NEW_CHAPTERS-')],
    [sg.Text("Прочитанные главы:", size=(15, 1))],
    [sg.Text("", size=(60, 1), key='-OPENED_CHAPTERS-')],
    [sg.Text("Тип:", size=(15, 1)), sg.Text("", key='-TYPE_LABEL-')],
    [sg.Button(button_text="Читать", key="-READER-")]
]

setting_bar_collapsed = [
    [sg.Button("⚙", key='-SETTINGS_ICON-', tooltip='Настройки')],
    [sg.Button("🗂", key='-RESERVE_ICON-', tooltip='Резерв')],
    [sg.Button("▶", key='-EXPAND-', tooltip='Развернуть')]
]

setting_bar_expanded = [
    [sg.Button("Настройки", key='-SETTINGS-')],
    [sg.Button("Резерв", key='-RESERVE-')],
    [sg.Button("◀", key='-COLLAPSE-', tooltip='Свернуть')]
]

tab_group_layout = [
    [sg.TabGroup([[
        sg.Tab('Rulate', [
            [sg.Listbox(
                list(book['title'] for book in books_set),
                size=(70, 35),
                key='-LISTBOX_RULATE-',
                enable_events=True
            )]
        ]),
        # sg.Tab('RanobeLib', [
        #     [sg.Listbox(
        #         list(book['title'] for book in books_set2),
        #         size=(70, 35),
        #         key='-LISTBOX_RANOBELIB-',
        #         enable_events=True
        #     )]
        # ]),
        sg.Tab('RanobeRF', [
            [sg.Listbox(
                list(book['title'] for book in unique_books_set3),
                size=(70, 35),
                key='-LISTBOX_RANOBERF-',
                enable_events=True
            )]
        ]),
        sg.Tab('RanobeHub', [
            [sg.Listbox(
                ranobehub,
                size=(70, 35),
                key='-LISTBOX_RANOBEHUB-',
                enable_events=True
            )]
        ])
    ]])]
]

layout = [[
    sg.Column(setting_bar_collapsed, key='-SETTING_BAR-', vertical_alignment='top'),
    sg.Column(tab_group_layout),
    sg.Column(book_entry_layout)]]

window = sg.Window("Информация о книгах", layout, resizable=False, size=(1100, 700))
setting_bar_expanded_visible = False

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break

    if event == '-LISTBOX_RULATE-':
        selected_titles = values['-LISTBOX_RULATE-']
        if selected_titles:
            selected_title = selected_titles[0]
            selected_book = next((book for book in books_set if book['title'] == selected_title), None)
            update_book_info(selected_book)

    if event == '-LISTBOX_RANOBERF-':
        selected_titles = values['-LISTBOX_RANOBERF-']
        if selected_titles:
            selected_title = selected_titles[0]
            selected_book = next((book for book in unique_books_set3 if book['title'] == selected_title), None)
            update_book_info(selected_book)

    if event == '-LISTBOX_RANOBEHUB-':
        selected_titles = values['-LISTBOX_RANOBEHUB-']
        if selected_titles:
            selected_title = selected_titles[0]
            selected_book = next((book for book in books_set4 if book['title'] == selected_title), None)
            update_book_info(selected_book)

    if event == '-LINK-':
        selected_book_title = window['-TITLE-'].get()
        selected_book = next((book for book in books_set if book['title'] == selected_book_title), None)
        if not selected_book:
            selected_book = next((book for book in unique_books_set3 if book['title'] == selected_book_title), None)
        if not selected_book:
            selected_book = next((book for book in books_set4 if book['title'] == selected_book_title), None)
        if selected_book and selected_book.get('link'):
            link = selected_book['link']
            if not link.startswith('http://') and not link.startswith('https://'):
                link = 'https://xn--80ac9aeh6f.xn--p1ai' + link
            webbrowser.open(link)

    if event == '-READER-':
        window.hide()
        reader.reader_open()
        window.un_hide()

    if event in ('-SETTINGS-', '-SETTINGS_ICON-'):
        show_settings_window()

    if event in ('-RESERVE-', '-RESERVE_ICON-'):
        sg.popup("Резервная кнопка нажата (функция пока не реализована)")

    if event in ('Up:38', 'Down:40'):
        listbox_key = '-LISTBOX_RULATE-'
        if listbox_key in values and values[listbox_key]:
            selected = values[listbox_key]
            if selected:
                current_title = selected[0]
                try:
                    current_index = next(
                        index for index, book in enumerate(books_set) if book['title'] == current_title)
                    if event == 'Up:38' and current_index > 0:
                        new_index = current_index - 1
                    elif event == 'Down:40' and current_index < len(books_set) - 1:
                        new_index = current_index + 1
                    else:
                        new_index = current_index

                    window[listbox_key].update(set_to_index=new_index)
                    selected_title = books_set[new_index]['title']
                    selected_book = books_set[new_index]
                    update_book_info(selected_book)
                except (IndexError, ValueError, StopIteration):
                    pass

    if event == '-EXPAND-':
        window['-SETTING_BAR-'].update(setting_bar_expanded)
        setting_bar_expanded_visible = True
    elif event == '-COLLAPSE-':
        window['-SETTING_BAR-'].update(setting_bar_collapsed)
        setting_bar_expanded_visible = False

window.close()
con.close()
