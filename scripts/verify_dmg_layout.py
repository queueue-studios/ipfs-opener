#!/usr/bin/env python3
"""verify_dmg_layout.py — Check that a mounted DMG's .DS_Store carries the intended
Finder window styling.

Usage: verify_dmg_layout.py <.DS_Store> <win_w> <win_h_incl_titlebar> <icon_size> \
                            <app_x> <app_y> <apps_x> <apps_y>

Exits non-zero (and prints what's wrong) if the window bounds, toolbar/status/path
bar visibility, icon size, background, or icon positions don't match. Finder
sometimes ignores `set bounds` (seen on macOS 27) and silently ships a huge
window — this catches it before the DMG is signed/notarized.
"""
import plistlib, re, struct, sys

ds = sys.argv[1]
win_w, win_h, icon, app_x, app_y, apps_x, apps_y = map(int, sys.argv[2:9])
data = open(ds, "rb").read()
problems = []


def blob_plist(tag):
    i = data.find(tag)
    if i < 0:
        return None
    j = data.find(b"bplist00", i)
    ln = struct.unpack(">I", data[j - 4:j])[0]
    return plistlib.loads(data[j:j + ln])


bwsp = blob_plist(b"bwsp")
if not bwsp:
    problems.append("no window settings (bwsp) record")
else:
    m = re.match(r"\{\{-?\d+, -?\d+\}, \{(\d+), (\d+)\}\}", bwsp.get("WindowBounds", ""))
    size = tuple(map(int, m.groups())) if m else None
    if size != (win_w, win_h):
        problems.append(f"window size is {size}, expected {(win_w, win_h)}")
    for key in ("ShowToolbar", "ShowStatusBar", "ShowSidebar"):
        if bwsp.get(key, True):
            problems.append(f"{key} is not hidden")
    # Finder (macOS 15–27) never records the path bar per window; it follows the
    # viewer's global View > Show Path Bar setting. Only complain if it's recorded on.
    if bwsp.get("ShowPathbar", False):
        problems.append("ShowPathbar is recorded as visible")

icvp = blob_plist(b"icvp")
if not icvp:
    problems.append("no icon view options (icvp) record")
else:
    if int(icvp.get("iconSize", 0)) != icon:
        problems.append(f"icon size is {icvp.get('iconSize')}, expected {icon}")
    if icvp.get("backgroundType") != 2:
        problems.append("background is not a picture")
    if icvp.get("arrangeBy") != "none":
        problems.append(f"icons are auto-arranged ({icvp.get('arrangeBy')})")

locs = sorted(struct.unpack(">II", data[m.end() + 4:m.end() + 12])
              for m in re.finditer(b"Ilocblob", data))
want = sorted([(app_x, app_y), (apps_x, apps_y)])
if locs != want:
    problems.append(f"icon positions are {locs}, expected {want}")

if problems:
    print("!! DMG layout verification failed:", file=sys.stderr)
    for p in problems:
        print("   -", p, file=sys.stderr)
    sys.exit(1)
print(f"   window {win_w}x{win_h}, icons {icon} pt at {want}, bars hidden, background set — OK")
