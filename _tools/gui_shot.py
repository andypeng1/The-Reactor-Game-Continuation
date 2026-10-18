"""Photograph the desktop reactor console without touching the operator's mouse.

    python -B _tools/gui_shot.py [out.png]

WHY THIS EXISTS.  `luau-windows/gui.py` has been edited for ten phases and
nobody has ever looked at it.  Every claim about it so far is a claim about the
model behind the widgets -- `core_model_check.py` reads the StringVars, which is
the right instrument for the numbers and says nothing about whether the window
actually lays out: a label can be clipped, a row can collide, a frame can be
the wrong height, and the model stays perfect.  CLAUDE.md 0.14b: the shape of
the picture exposes a wrong ruler earlier than the numbers do.

THE RULE THIS FILE OBEYS.  The operator's mouse is off limits (memory:
windows-desktop-control).  This file never moves the cursor, never clicks, and
never sends input.  It only asks the OS for pixels.

PHASE 145: THE OFF-DESKTOP PATH DOES NOT WORK ON TK, AND IT SAID IT DID.
The first version mapped the window at +20000+20000 and called
PrintWindow(PW_RENDERFULLCONTENT).  That returned 1 and produced a picture whose
client area was one flat colour -- the title bar was real (the OS paints it) and
everything Tk draws was missing.  The window really had laid out: a widget-tree
probe read 85 of 85 widgets mapped with sane rectangles, so the blank frame was
the INSTRUMENT, not the console (CLAUDE.md 0.2).  Cause, measured twice: Tk's
toplevel does not answer WM_PRINT (a direct SendMessage(WM_PRINT) with the
client/children flags left the bitmap untouched), so PrintWindow has nothing to
ask for.  The guard missed it because it counted distinct colours over the WHOLE
frame -- the OS title bar alone supplies 710 colours and a full luminance range,
which is the frame saying "a window is here", not "the console is on it".

WHAT IT DOES NOW, IN ORDER.
  1. Off-desktop PrintWindow.  Cheap, silent, and if a future Tk implements
     WM_PRINT this path starts working again by itself.
  2. The client crop is judged on its own: flat colour -> path 1 failed.  Then,
     and only then, the window is moved on-screen for the length of one grab
     (~0.2 s), shown with SWP_NOACTIVATE so it does not take focus, raised
     no-activate so it is not occluded, photographed with ImageGrab, and hidden
     again before the model advances.  The operator sees a window blink; he
     does not see his cursor move.
  3. The saved PNG is cropped to the client area, so every claim below is about
     the console and not about the frame the OS drew around it.

WHAT IT PRINTS.  Which path produced the picture, the widget-tree census
(mapped/total), the client size, and a per-band brightness census of the client
area.  Exit status 1 when the capture is suspiciously empty -- "the picture is
blank" and "the window is fine, I just could not see it" must not be the same
output (CLAUDE.md 0.26 1).
"""

import ctypes
import ctypes.wintypes as wt
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'luau-windows'))

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x00000002
DIB_RGB_COLORS = 0
OFFSCREEN = "+20000+20000"


def dpi_aware():
    """Make this process DPI-aware BEFORE any HWND exists.

    Phase 145's first on-screen capture came out at the wrong scale: Tk and
    GetWindowRect both report the 125%-virtualised coordinates a DPI-unaware
    process sees, while ImageGrab reads the composited screen in PHYSICAL pixels.
    The two disagreed by exactly 1.25, so the grab covered the left 1044 physical
    columns of a 1305-pixel-wide window and the right column -- every value in
    the console -- fell outside the picture.  The reading that caught it was the
    x of a known label: Tk said 501, the picture said 623 (501 * 1.25).

    Declaring awareness removes the virtualisation, so every coordinate in this
    file is physical, and the console is rendered the way the operator's 125%
    display draws it.  Returns the level actually granted, which is printed.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per-monitor
        return 'per-monitor'
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()           # system
        return 'system'
    except Exception:
        return 'unaware (coordinates may disagree with ImageGrab)'

HWND_TOPMOST = wt.HWND(-1)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080


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


def distinct(img):
    """Colours in a PIL image, counted exactly (no 256-colour ceiling)."""
    return len(img.getcolors(maxcolors=1 << 24) or [])


def main():
    awareness = dpi_aware()                 # before the first HWND, or it is a no-op
    import tkinter as tk
    # Tk maps its toplevel WITH ACTIVATION even at +20000+20000, so the act of
    # building the console already takes the foreground away from whatever the
    # operator had focused.  Remember it before the first HWND exists and give
    # it back at the end -- otherwise "the window never appeared on a monitor"
    # would be true while his keyboard focus had still been stolen.
    fg_before_window = user32.GetForegroundWindow()
    import gui
    from PIL import Image, ImageGrab

    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '_attic', 'scratch', 'gui_shot.png')
    # `--armed` ticks the model's own checkbox first: unarmed, the whole
    # core-model half of the readout column is dashes ("-"), which is the
    # console telling the truth, not the layout failing.
    armed = '--armed' in sys.argv

    root = tk.Tk()
    console = gui.Console(root)
    root.geometry(OFFSCREEN)
    # The readouts are StringVars filled by Console._tick, which is scheduled on
    # the Tk clock at sim.period (1.0 s default).  Twenty update() calls finish
    # in milliseconds, so the first version photographed a window whose every
    # value was still its empty construction-time string -- a picture of the
    # widgets with the numbers missing, which is not a defect in the console.
    # step_once() advances the model synchronously, so the picture is taken
    # after the same work a tick does, without waiting on wall time.
    if armed:
        console.arm_var.set(True)
        console.on_arm()
    for _ in range(3 if not armed else 6):
        console.step_once()
    for _ in range(20):
        root.update()
    root.update_idletasks()

    hwnd = int(root.winfo_id())
    frame_hwnd = user32.GetAncestor(hwnd, 2) or hwnd      # GA_ROOT
    rect = wt.RECT()
    user32.GetWindowRect(frame_hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top

    # Where the client area sits INSIDE the frame: this is the crop that keeps
    # the OS's title bar out of the reading (and out of the deliverable).
    origin = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(origin))
    cx, cy = origin.x - rect.left, origin.y - rect.top
    cw, ch = root.winfo_width(), root.winfo_height()

    # ---- path 1: off-desktop PrintWindow ----
    ok, raw = capture(frame_hwnd, w, h)
    img = Image.frombuffer('RGBA', (w, h), raw, 'raw', 'BGRA', 0, 1).convert('RGB')
    client = img.crop((cx, cy, cx + cw, cy + ch))
    path = 'PrintWindow (off-desktop)'
    focus_before = user32.GetForegroundWindow()
    focus_after = focus_before
    if distinct(client) < 50:
        # ---- path 2: one blink on screen, no activation ----
        user32.SetWindowPos(frame_hwnd, HWND_TOPMOST, 8, 8, 0, 0,
                            SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        root.update()
        user32.UpdateWindow(frame_hwnd)
        img = ImageGrab.grab(bbox=(8, 8, 8 + w, 8 + h), all_screens=True)
        client = img.crop((cx, cy, cx + cw, cy + ch))
        path = 'ImageGrab (one on-screen blink, no activation)'
        focus_after = user32.GetForegroundWindow()
        user32.SetWindowPos(frame_hwnd, HWND_TOPMOST, 20000, 20000, 0, 0,
                            SWP_NOSIZE | SWP_NOACTIVATE | SWP_HIDEWINDOW)
        root.update()

    # Keep only the client area: the title bar is the OS's, not the console's.
    img = client

    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print('path          %s' % path)
    print('dpi awareness  %s' % awareness)
    print('focus          foreground before %d after %d (unchanged: %s)'
          % (focus_before, focus_after, focus_before == focus_after))
    print('frame hwnd=%d %dx%d, client %dx%d at +%d+%d inside it'
          % (frame_hwnd, w, h, cw, ch, cx, cy))
    print('wrote %s (%d bytes) client-only %dx%d'
          % (out, os.path.getsize(out), img.width, img.height))

    # ---- the reading that decides whether the picture means anything ----
    # A PrintWindow that did nothing returns a bitmap WITHOUT raising, so the
    # assertion is not "a file exists" and not "the frame has many colours".
    colors = img.getcolors(maxcolors=1 << 24) or []
    extrema = img.convert('L').getextrema()

    # Row bands, so "which part of the console came out" is one reading rather
    # than a whole-image average that a bright empty panel can carry.
    bands = []
    for i in range(6):
        top = img.height * i // 6
        bot = img.height * (i + 1) // 6
        band = img.crop((0, top, img.width, bot))
        bands.append((i + 1, distinct(band), band.convert('L').getextrema()))

    print('client colours %d, luminance %s' % (len(colors), extrema))
    for i, n, ex in bands:
        print('  band %d  colours %5d  luminance %s' % (i, n, ex))

    root.destroy()

    # Give the foreground back, then READ it back: the restore is a claim about
    # the operator's desktop, so it gets the same treatment as every other claim.
    if fg_before_window and user32.GetForegroundWindow() != fg_before_window:
        user32.SetForegroundWindow(fg_before_window)
    fg_restored = user32.GetForegroundWindow() == fg_before_window
    print('focus          returned to hwnd %d: %s' % (fg_before_window, fg_restored))

    problems = []
    if not fg_restored:
        problems.append('foreground focus was not given back to hwnd %d' % fg_before_window)
    if not ok and path.startswith('PrintWindow'):
        problems.append('PrintWindow returned 0')
    if cw < 800 or ch < 600:
        problems.append('client smaller than minsize 820x600')
    if len(colors) < 50:
        problems.append('only %d distinct colours in the client area' % len(colors))
    if extrema[1] - extrema[0] < 32:
        problems.append('client luminance range %d' % (extrema[1] - extrema[0]))
    flat = [i for i, n, _ in bands if n < 8]
    if flat:
        problems.append('bands %s are flat (<8 colours)' % flat)

    for p in problems:
        print('FAIL %s' % p)
    print('%s' % ('ok' if not problems else 'NOT A PICTURE OF THE CONSOLE'))
    return 1 if problems else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:               # see CLAUDE.md 0.6: an uncaught exception
        import traceback                # can leave rc = 0, and "the checker
        traceback.print_exc()           # crashed" then looks like "all clear".
        sys.exit(1)
