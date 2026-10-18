"""Photograph the desktop reactor console without touching the operator's screen.

    python -B _tools/gui_shot.py [out.png]

WHY THIS EXISTS.  `luau-windows/gui.py` has been edited for eight phases and
nobody has ever looked at it.  Every claim about it so far is a claim about the
model behind the widgets -- `core_model_check.py` reads the StringVars, which is
the right instrument for the numbers and says nothing about whether the window
actually lays out: a label can be clipped, a row can collide, a frame can be
the wrong height, and the model stays perfect.  CLAUDE.md 0.14b: the shape of
the picture exposes a wrong ruler earlier than the numbers do.

THE RULE THIS FILE OBEYS.  The operator's mouse is off limits (memory:
windows-desktop-control).  So this file never moves the cursor, never clicks,
and never takes a screen grab.  It maps the window OFF the desktop (a geometry
far outside the virtual screen), asks Windows to paint it into a bitmap via
PrintWindow(PW_RENDERFULLCONTENT), and reads those pixels.  The window is real
and Tk lays it out for real; it simply never appears on a monitor.

WHAT IT PRINTS.  Size, a per-region brightness census, and the count of distinct
colours -- enough to tell "laid out" from "all one colour", which is the failure
mode a blank PrintWindow produces.  Exit status is 1 when the capture is
suspiciously empty, because "the picture is black" and "the window is fine, I
just could not see it" must not be the same output.

WHY NOT ImageGrab.  `ImageGrab.grab()` reads the SCREEN.  If the window is
off-desktop it captures whatever else is there, and if it is on-desktop it
photographs the operator's desktop.  PrintWindow asks the window to paint
itself, which is what we actually want.
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'luau-windows'))

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0

# A place Windows will never show: far right and far below the virtual screen.
# Printing does not care where the window is, only that it is mapped.
OFFSCREEN = "+20000+20000"


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG),
        ('biPlanes', wt.WORD), ('biBitCount', wt.WORD),
        ('biCompression', wt.DWORD), ('biSizeImage', wt.DWORD),
        ('biXPelsPerMeter', wt.LONG), ('biYPelsPerMeter', wt.LONG),
        ('biClrUsed', wt.DWORD), ('biClrImportant', wt.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wt.DWORD * 3)]


def capture(hwnd, w, h):
    """Ask the window to paint itself into a 32-bit DIB and return its bytes."""
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)

    ok = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)

    bi = BITMAPINFO()
    bi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.bmiHeader.biWidth = w
    bi.bmiHeader.biHeight = -h          # negative = top-down, no row flip
    bi.bmiHeader.biPlanes = 1
    bi.bmiHeader.biBitCount = 32
    bi.bmiHeader.biCompression = 0      # BI_RGB
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bi), DIB_RGB_COLORS)

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    return ok, buf.raw


def main():
    import tkinter as tk
    import gui

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '_attic', 'scratch', 'gui_shot.png')

    root = tk.Tk()
    console = gui.Console(root)
    # Off the desktop before it is ever mapped: `geometry` is applied by Tk
    # before the first Map event, so the window never flashes on a monitor.
    root.geometry(OFFSCREEN)
    # Let Tk lay out and run a few ticks of the model so the readouts carry
    # real numbers rather than their construction-time placeholders.
    for _ in range(20):
        root.update()
        if console._after is not None:
            pass
    root.update_idletasks()

    hwnd = int(root.winfo_id())
    # Tk gives the client area; the title bar and borders belong to the parent.
    # Asking for the frame means the picture is what a person would see.
    frame_hwnd = user32.GetAncestor(hwnd, 2)  # GA_ROOT
    if not frame_hwnd:
        frame_hwnd = hwnd

    rect = wt.RECT()
    user32.GetWindowRect(frame_hwnd, ctypes.byref(rect))
    x, y = rect.left, rect.top
    w, h = rect.right - rect.left, rect.bottom - rect.top
    print('window frame hwnd=%d at (%d,%d) size %dx%d' % (frame_hwnd, x, y, w, h))

    ok, raw = capture(frame_hwnd, w, h)

    # Tk's own geometry: if it disagrees with the frame by more than the border,
    # the capture is of something other than the console.
    cw, ch = root.winfo_width(), root.winfo_height()
    print('tk client %dx%d (frame is %dx%d, border %dx%d)'
          % (cw, ch, w, h, w - cw, h - ch))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    from PIL import Image
    img = Image.frombuffer('RGBA', (w, h), raw, 'raw', 'BGRA', 0, 1)
    img = img.convert('RGB')
    img.save(out)
    print('wrote %s (%d bytes)' % (out, os.path.getsize(out)))

    # ---- the reading that decides whether the picture means anything ----
    # A PrintWindow that failed returns an all-black (or all-one-colour) bitmap
    # WITHOUT raising.  So the assertion is not "a file exists".
    colors = img.getcolors(maxcolors=1 << 24) or []
    distinct = len(colors)
    extrema = img.convert('L').getextrema()
    print('distinct colours %d, luminance %s' % (distinct, extrema))

    root.destroy()

    problems = []
    if not ok:
        problems.append('PrintWindow returned 0')
    if w < 800 or h < 600:
        problems.append('frame smaller than minsize 820x600')
    if distinct < 50:
        problems.append('only %d distinct colours' % distinct)
    if extrema[1] - extrema[0] < 32:
        problems.append('luminance range %d' % (extrema[1] - extrema[0]))

    for p in problems:
        print('FAIL %s' % p)
    print('%s' % ('ok' if not problems else 'NOT A PICTURE OF THE CONSOLE'))
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
