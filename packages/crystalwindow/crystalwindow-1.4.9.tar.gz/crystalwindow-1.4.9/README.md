🧊 CrystalWindow (Single-File Edition)

A tiny but mighty Pygame framework that gives u a full window system, rendering, and GUI power — all packed into one file.
No setup pain. No folder chaos. Just import, and boom 💥, instant window.

🚀 Quick Start
pip install crystalwindow

Then in ur Python script:

from CrystalWindow import Window

# create window
win = Window(800, 600, "My Cool Game")

# main loop
while win.running:
    win.check_events()
    win.fill((0, 0, 50))
    win.update()


🌀 That’s it. Run it, and boom — instant working window.

🧩 Features

✅ Built-in window manager
✅ Built-in image & icon loader (with default base64 logo)
✅ File-safe startup (even inside PyInstaller)
✅ Works offline — no extra libs
✅ Minimal and clean syntax

💾 Default Logo

The file includes a variable named DEFAULT_LOGO_BASE64 — a lil encoded PNG used when no icon is found.

Use it like: Window(800, 600, "My Window", icon=MyIcon.png)

Boom 💥 — u can show it, set it as a window icon, or meme it if u want.

🧠 Example Integration

You can use it as part of ur project (like a game, an editor, or a tool):

from CrystalWindow import Window

win = Window(800, 600, "My Window", icon=MyIcon.png)

while win.running:
    win.check_events()
    win.fill((10, 10, 20))
    win.update()

🧊 Credits

💻 Made by: Crystal Friendo
🌀 Framework: CrystalWindow
🎨 Powered by: Pygame
✨ License: Free to use, modify, and vibe with