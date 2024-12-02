import PySimpleGUI as sg


def reader_open():
    default_font = ("Arial", 12)
    default_text_color = "black"
    default_bg_color = "white"

    layout_main = [
        [sg.Text("Читалка текста", font=("Arial", 16), justification="center", expand_x=True)],
        [sg.Multiline("", key="-TEXT-", size=(60, 20), font=default_font,
                      text_color=default_text_color, background_color=default_bg_color,
                      expand_x=True, expand_y=True)],
        [sg.Button("Настройки", key="-TOGGLE_SETTINGS-", expand_x=True),
         sg.Button("Открыть файл", key="-OPEN-", expand_x=True),
         sg.Button("Сохранить файл", key="-SAVE-", expand_x=True),
         sg.Button("Выход", key="-EXIT-", expand_x=True)],
    ]

    layout_settings = [
        [sg.Text("Шрифт"), sg.Combo(["Arial", "Courier", "Helvetica", "Times New Roman"],
                                    default_value="Arial", key="-FONT-", size=(20, 1)),
         sg.Text("Размер"), sg.Spin([i for i in range(8, 36)], initial_value=12, key="-FONT_SIZE-", size=(5, 1))],
        [sg.Text("Цвет текста"), sg.ColorChooserButton("Выбрать", key="-TEXT_COLOR-", target="-TEXT_COLOR_VALUE-"),
         sg.Input(default_text_color, key="-TEXT_COLOR_VALUE-", visible=False)],
        [sg.Text("Цвет фона"), sg.ColorChooserButton("Выбрать", key="-BG_COLOR-", target="-BG_COLOR_VALUE-"),
         sg.Input(default_bg_color, key="-BG_COLOR_VALUE-", visible=False)],
        [sg.Button("Применить", key="-APPLY_SETTINGS-")]
    ]

    layout = [
        [sg.Column(layout_main, expand_x=True, expand_y=True, key="-MAIN-")],
        [sg.Column(layout_settings, visible=False, expand_x=True, key="-SETTINGS-")]
    ]

    window = sg.Window("Читалка текста", layout, resizable=True, modal=True)

    settings_visible = False

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "-EXIT-"):
            break

        if event == "-TOGGLE_SETTINGS-":
            settings_visible = not settings_visible
            window["-SETTINGS-"].update(visible=settings_visible)

        if event == "-APPLY_SETTINGS-":
            font = values["-FONT-"]
            font_size = int(values["-FONT_SIZE-"])
            text_color = values["-TEXT_COLOR_VALUE-"]
            bg_color = values["-BG_COLOR_VALUE-"]

            window["-TEXT-"].update(font=(font, font_size), text_color=text_color, background_color=bg_color)

        if event == "-OPEN-":
            filepath = sg.popup_get_file("Выберите файл", no_window=True)
            if filepath:
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        content = file.read()
                    window["-TEXT-"].update(content)
                except Exception as e:
                    sg.popup_error(f"Ошибка при чтении файла: {e}")

        if event == "-SAVE-":
            filepath = sg.popup_get_file("Сохранить как", save_as=True, no_window=True, default_extension=".txt")
            if filepath:
                try:
                    with open(filepath, "w", encoding="utf-8") as file:
                        file.write(values["-TEXT-"])
                    sg.popup("Файл успешно сохранён!")
                except Exception as e:
                    sg.popup_error(f"Ошибка при сохранении файла: {e}")

    window.close()
