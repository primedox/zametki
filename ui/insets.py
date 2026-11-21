"""Android system-bar insets.

On many phones (notably Samsung on recent Android versions) the app surface is
drawn underneath the status bar / camera cut-out, which hides the top of every
screen. We measure how much of the surface is actually covered and let the app
keep its content clear of that area.
"""


def measure():
    """Return (top_px, bottom_px, note) to keep clear of. Safe on any platform."""
    try:
        from jnius import autoclass
    except Exception:
        return 0, 0, "no jnius"

    try:
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        res = activity.getResources()
        rid = res.getIdentifier("status_bar_height", "dimen", "android")
        top = res.getDimensionPixelSize(rid) if rid > 0 else 0
        bottom = 0
        real_h = 2400

        try:
            insets = activity.getWindow().getDecorView().getRootWindowInsets()
            if insets is not None:
                top = max(top, insets.getStableInsetTop())
                bottom = insets.getStableInsetBottom()
                cutout = insets.getDisplayCutout()
                if cutout is not None:
                    top = max(top, cutout.getSafeInsetTop())
        except Exception:
            pass

        # where does the Kivy surface really sit on the screen?
        try:
            surface = autoclass("org.libsdl.app.SDLActivity").mSurface
            array = autoclass("java.lang.reflect.Array")
            arr = array.newInstance(autoclass("java.lang.Integer").TYPE, 2)
            surface.getLocationOnScreen(arr)
            surface_y = int(arr[1])
            surface_h = int(surface.getHeight())
            real = autoclass("android.util.DisplayMetrics")()
            activity.getWindowManager().getDefaultDisplay().getRealMetrics(real)
            real_h = int(real.heightPixels)
            top_pad = max(0, top - surface_y)
            bottom_pad = max(0, bottom - (real_h - (surface_y + surface_h)))
            note = "y=%d h=%d screen=%d bars=%d/%d" % (surface_y, surface_h, real_h, top, bottom)
        except Exception as exc:  # measuring failed: assume the top is covered
            top_pad, bottom_pad = top, 0
            note = "fallback (%s) bars=%d/%d" % (type(exc).__name__, top, bottom)

        limit = int(0.12 * max(real_h, 1))
        return min(top_pad, limit), min(bottom_pad, limit), note
    except Exception as exc:
        return 0, 0, "error %s" % type(exc).__name__


def use_resize_mode():
    """Ask Android to shrink the window when the keyboard opens.

    Without this the system picks "pan" for a single-surface app: the whole
    window slides up under the status bar and the keyboard covers the bottom.
    """
    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass
    except Exception:
        return

    @run_on_ui_thread
    def _apply():
        try:
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            activity.getWindow().setSoftInputMode(16)  # SOFT_INPUT_ADJUST_RESIZE
        except Exception:
            pass

    _apply()


_kb_cache = {}


def keyboard_state():
    """Return (visible, overlap_px): is the keyboard open and how much of our
    surface does it still cover (0 when the system already resized the window)."""
    try:
        from jnius import autoclass

        if "api" not in _kb_cache:
            _kb_cache["api"] = autoclass("android.os.Build$VERSION").SDK_INT
        if _kb_cache["api"] < 30:
            return False, 0
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        insets = activity.getWindow().getDecorView().getRootWindowInsets()
        if insets is None:
            return False, 0
        ime = autoclass("android.view.WindowInsets$Type").ime()
        if not insets.isVisible(ime):
            return False, 0
        kb_bottom = insets.getInsets(ime).bottom

        surface = autoclass("org.libsdl.app.SDLActivity").mSurface
        array = autoclass("java.lang.reflect.Array")
        arr = array.newInstance(autoclass("java.lang.Integer").TYPE, 2)
        surface.getLocationOnScreen(arr)
        real = autoclass("android.util.DisplayMetrics")()
        activity.getWindowManager().getDefaultDisplay().getRealMetrics(real)
        keyboard_top = int(real.heightPixels) - int(kb_bottom)
        surface_bottom = int(arr[1]) + int(surface.getHeight())
        return True, max(0, surface_bottom - keyboard_top)
    except Exception:
        return False, 0
