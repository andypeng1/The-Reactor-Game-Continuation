import os, sys, tkinter as tk
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'luau-windows'))
import gui
root = tk.Tk()
c = gui.Console(root)
root.geometry("+20000+20000")
for _ in range(20):
    root.update()
info = []
def walk(w, d=0):
    if d > 3: return
    try:
        info.append((d, w.winfo_class(), str(w)[-40:], w.winfo_ismapped(),
                     w.winfo_x(), w.winfo_y(), w.winfo_width(), w.winfo_height()))
    except Exception as e:
        info.append((d, 'ERR', repr(e), 0,0,0,0,0)); return
    for ch in w.winfo_children():
        walk(ch, d+1)
walk(root)
print("mapped %d / total %d" % (sum(1 for r in info if r[3]), len(info)))
for r in info[:45]:
    print("%s%-16s mapped=%s %4d,%4d %4dx%-4d %s" % ("  "*r[0], r[1], r[3], r[4], r[5], r[6], r[7], r[2]))
root.destroy()
