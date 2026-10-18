import os, sys, ctypes, ctypes.wintypes as wt
import tkinter as tk
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'luau-windows'))
import gui
u = ctypes.windll.user32
g = ctypes.windll.gdi32
u.SendMessageW.restype = ctypes.c_ssize_t
u.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
root = tk.Tk(); c = gui.Console(root); root.geometry("+20000+20000")
for _ in range(20): root.update()
frame = u.GetAncestor(int(root.winfo_id()), 2) or int(root.winfo_id())
r = wt.RECT(); u.GetWindowRect(frame, ctypes.byref(r))
w,h = r.right-r.left, r.bottom-r.top
hdc = u.GetDC(0); mem = g.CreateCompatibleDC(hdc); bmp = g.CreateCompatibleBitmap(hdc, w, h)
g.SelectObject(mem, bmp)
PRF = 0x00000004|0x00000008|0x00000010|0x00000020  # CLIENT|ERASEBKGND|NONCLIENT|CHILDREN
for flags,name in [(PRF,'wm_print all'),(0x4|0x10|0x20,'wm_print client+children')]:
    g.PatBlt(mem,0,0,w,h,0x00FF0062)  # WHITENESS to clear
    res = u.SendMessageW(frame, 0x0317, int(mem), flags)  # WM_PRINT
    class BIH(ctypes.Structure):
        _fields_=[('biSize',wt.DWORD),('biWidth',wt.LONG),('biHeight',wt.LONG),('biPlanes',wt.WORD),
                  ('biBitCount',wt.WORD),('biCompression',wt.DWORD),('biSizeImage',wt.DWORD),
                  ('biXPelsPerMeter',wt.LONG),('biYPelsPerMeter',wt.LONG),('biClrUsed',wt.DWORD),('biClrImportant',wt.DWORD)]
    class BI(ctypes.Structure):
        _fields_=[('bmiHeader',BIH),('bmiColors',wt.DWORD*3)]
    bi=BI(); bi.bmiHeader.biSize=ctypes.sizeof(BIH); bi.bmiHeader.biWidth=w; bi.bmiHeader.biHeight=-h
    bi.bmiHeader.biPlanes=1; bi.bmiHeader.biBitCount=32
    buf=ctypes.create_string_buffer(w*h*4)
    g.GetDIBits(mem,bmp,0,h,buf,ctypes.byref(bi),0)
    data=buf.raw
    # ignore the title bar band: sample the client rows only
    row=x=0; px=set()
    for yy in range(40, h, 7):
        off=yy*w*4
        for xx in range(10, w, 11):
            px.add(data[off+xx*4:off+xx*4+3])
    print("%-24s res=%s distinct colours in client rows: %d" % (name, res, len(px)))
g.DeleteObject(bmp); g.DeleteDC(mem); u.ReleaseDC(0,hdc); root.destroy()
