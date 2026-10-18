import os, sys, ctypes, ctypes.wintypes as wt, tkinter as tk
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'luau-windows'))
import gui
u = ctypes.windll.user32
root = tk.Tk(); c = gui.Console(root); root.geometry("+20000+20000")
for _ in range(3): c.step_once()
for _ in range(20): root.update()
print("before show: client", root.winfo_width(), root.winfo_height())
fr = u.GetAncestor(int(root.winfo_id()), 2)
r = wt.RECT(); u.GetWindowRect(fr, ctypes.byref(r)); print("frame rect offscreen", r.left, r.top, r.right-r.left, r.bottom-r.top)
u.SetWindowPos(fr, wt.HWND(-1), 8, 8, 0, 0, 0x0001|0x0010|0x0040)
for _ in range(10):
    root.update()
r = wt.RECT(); u.GetWindowRect(fr, ctypes.byref(r)); print("frame rect onscreen", r.left, r.top, r.right-r.left, r.bottom-r.top)
print("after show: client", root.winfo_width(), root.winfo_height())
for var, getter in c.readouts[:2]:
    print("readout", var.get())
def walk(w):
    for ch in w.winfo_children():
        try: tv = ch.cget('textvariable')
        except Exception: tv = ''
        if tv and var_match(ch):
            print("value label text=%r rootx=%d rooty=%d w=%d h=%d" % (
                ch.cget('text'), ch.winfo_rootx(), ch.winfo_rooty(), ch.winfo_width(), ch.winfo_height()))
        walk(ch)
def var_match(ch):
    try:
        v = ch.cget('textvariable')
        # the Pressure readout is the first registered var
        return str(v) in [str(t) for t,_ in [(c.readouts[0][0],0)]]
    except Exception:
        return False
walk(root)
root.destroy()
