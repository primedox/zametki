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
