"""Capture a top-level window to PNG using GDI, with no third-party dependencies.

Written by hand rather than pulled from a library because the emulator's own F12
screenshot path needs window focus, which is unreliable in an automated run.
"""
import ctypes
import struct
import zlib
from ctypes import wintypes
from pathlib import Path

user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', ctypes.c_long),
        ('biHeight', ctypes.c_long),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', ctypes.c_long),
        ('biYPelsPerMeter', ctypes.c_long),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]


def _png(width, height, rgb_rows):
    """Wrap raw top-down RGB rows into a PNG byte string."""
    raw = b''.join(b'\x00' + row for row in rgb_rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 6))
            + chunk(b'IEND', b''))


def find_window_for_pid(pid, class_name='SDL_app'):
    found = []
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid:
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, 256)
            found.append((hwnd, cls.value))
        return True

    user32.EnumWindows(proc(cb), 0)
    for hwnd, cls in found:
        if cls == class_name:
            return hwnd
    return found[0][0] if found else None


def capture(hwnd, dest):
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    width, height = rect.right - rect.left, rect.bottom - rect.top
    if width <= 0 or height <= 0:
        raise RuntimeError(f'degenerate window size {width}x{height}')

    window_dc = user32.GetWindowDC(hwnd)
    screen_dc = user32.GetDC(0)
    mem_dc = gdi32.CreateCompatibleDC(screen_dc)

    info = BITMAPINFO()
    info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = width
    info.bmiHeader.biHeight = -height  # negative => top-down rows
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    info.bmiHeader.biCompression = BI_RGB

    bits = ctypes.c_void_p()
    gdi32.CreateDIBSection.restype = ctypes.c_void_p
    bitmap = gdi32.CreateDIBSection(mem_dc, ctypes.byref(info), DIB_RGB_COLORS,
                                    ctypes.byref(bits), None, 0)
    if not bitmap:
        raise ctypes.WinError(ctypes.get_last_error())
    old = gdi32.SelectObject(mem_dc, ctypes.c_void_p(bitmap))

    # Copy from the screen so we capture what is actually visible, then make sure the
    # window is on top before doing so.
    user32.SetForegroundWindow(hwnd)
    gdi32.BitBlt(mem_dc, 0, 0, width, height, screen_dc, rect.left, rect.top, SRCCOPY)

    buf = ctypes.string_at(bits, width * height * 4)
    gdi32.SelectObject(mem_dc, ctypes.c_void_p(old))
    gdi32.DeleteObject(ctypes.c_void_p(bitmap))
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(0, screen_dc)
    user32.ReleaseDC(hwnd, window_dc)

    rows = []
    stride = width * 4
    for y in range(height):
        row = buf[y * stride:(y + 1) * stride]
        rows.append(bytes(b for i in range(0, stride, 4) for b in row[i:i + 3]))

    Path(dest).write_bytes(_png(width, height, rows))
    return width, height
