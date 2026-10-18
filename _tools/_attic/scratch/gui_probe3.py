import os, sys, tkinter as tk
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'luau-windows'))
import gui
root = tk.Tk(); c = gui.Console(root); root.geometry("+20000+20000")
for _ in range(3): c.step_once()
for _ in range(20): root.update()
root.update_idletasks()
print("client", root.winfo_width(), root.winfo_height())
for var, getter in c.readouts[:8]:
    print("var value=%r" % (var.get(),))
# find labels with textvariable
def walk(w):
    for ch in w.winfo_children():
        try:
            tv = ch.cget('textvariable')
        except Exception:
            tv = ''
        if tv:
            print("label var=%-14s text=%-14r x=%4d w=%4d parent=%s" % (
                str(tv), ch.cget('text'), ch.winfo_rootx()-root.winfo_rootx(),
                ch.winfo_width(), ch.winfo_parent()))
        walk(ch)
walk(root)
root.destroy()
