import traceback

try:
    import notes_app
    notes_app.NotesApp().run()
except BaseException:
    _tb = traceback.format_exc()
    try:
        from kivy.app import App
        from kivy.core.window import Window
        from kivy.metrics import dp
        from kivy.uix.label import Label
        from kivy.uix.scrollview import ScrollView

        class CrashApp(App):
            def build(self):
                label = Label(
                    text="ОШИБКА ЗАПУСКА:\n\n" + _tb,
                    size_hint_y=None,
                    halign="left",
                    valign="top",
                    font_size=dp(11),
                    color=(1, 1, 1, 1),
                )
                label.bind(width=lambda w, v: setattr(w, "text_size", (v - dp(16), None)))
                label.bind(texture_size=lambda w, v: setattr(w, "height", v[1] + dp(40)))
                scroll = ScrollView()
                scroll.add_widget(label)
                return scroll

        CrashApp().run()
    except BaseException:
        pass
