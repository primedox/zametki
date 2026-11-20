import os
import traceback


def _fit_metrics():
    """Make the UI look the same on every phone.

    Android's own "display size" and "font size" settings otherwise inflate
    Kivy's dp/sp units, so text no longer fits and layouts break. We pin the
    design to a 360 dp wide screen and ignore the system font scale.
    """
    try:
        from jnius import autoclass

        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        metrics = activity.getResources().getDisplayMetrics()
        short_side = min(metrics.widthPixels, metrics.heightPixels)
        density = max(1.5, min(short_side / 360.0, 3.5))
        os.environ["KIVY_METRICS_DENSITY"] = "%.3f" % density
        os.environ["KIVY_METRICS_FONTSCALE"] = "1"
    except Exception:
        pass


_fit_metrics()

try:
    from kivy.config import Config

    Config.set("input", "mouse", "mouse,disable_multitouch")
    from kivy.core.window import Window

    Window.clearcolor = (0.957, 0.965, 0.984, 1)
except Exception:
    pass

try:
    import notes_app

    notes_app.NotesApp().run()
except BaseException:
    _tb = traceback.format_exc()
    try:
        from kivy.app import App
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
