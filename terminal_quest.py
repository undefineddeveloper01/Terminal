"""
Retro Terminal Quest Game for Tarun (aka Legend Developer)
A stealth challenge — no spoilers up front.
Framework: PySide6
Run:  pip install PySide6
      py -3 terminal_quest.py   (or: python terminal_quest.py)
"""

import base64
import math
import os
import random
import struct
import sys
import tempfile
import wave

from PySide6.QtCore import Qt, QTimer, QUrl, QPoint, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QFont, QPainter, QColor, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QPlainTextEdit, QLineEdit, QGridLayout,
    QFrame, QDialog, QMessageBox, QSizePolicy
)

try:
    from PySide6.QtMultimedia import QSoundEffect
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False
    QSoundEffect = object  # fallback dummy


# ============================================================================
# CONFIG — EDIT EVERYTHING HERE. All personalization lives in this dict.
# ============================================================================
CONFIG = {
    # --- People ---
    "RECIPIENT_NAME": "Tarun",
    "RECIPIENT_NICKNAME": "Legend Developer",
    "SENDER_NAME": "Undefined Developer",
    "BIRTHDAY_DATE": "4/10/26",

    # --- Theme: "neon_green" | "cyber_cyan" | "amber" (default = cyber_cyan) ---
    "THEME": "cyber_cyan",
    "THEMES": {
        "neon_green": {"bg": "#0D1117", "fg": "#00FF66", "dim": "#00AA44", "accent": "#00FF66", "warn": "#FF3131"},
        "cyber_cyan":  {"bg": "#000000", "fg": "#00F0FF", "dim": "#0088AA", "accent": "#00F0FF", "warn": "#FF3131"},
        "amber":       {"bg": "#0A0800", "fg": "#FFB000", "dim": "#AA7700", "accent": "#FFB000", "warn": "#FF3131"},
    },

    # --- Typewriter speeds (ms per char) ---
    "TYPE_MIN_MS": 12,
    "TYPE_MAX_MS": 38,

    # --- Puzzle 1: OPERATION ELDER_PROTOCOL. EDIT ME — personalise wording ---
    # Each entry: chapter, story (typed), question, options[4], answer, hint,
    #             success (on correct), fail (on wrong)
    "TRIVIA_QUESTIONS": [
        {
            "chapter": "CH.1 // THE SPARK",
            "story": "> log found... little dev already loved code... loops at midnight, just for fun...\n> then elder brother notices... 'okay, you're doing good. go for it.'",
            "question": "You started coding because YOU loved it — but who was the catalyst that pushed you forward?",
            "options": ["Tarun — elder brother", "YouTube tutorial", "College professor", "StackOverflow"],
            "answer": 0,
            "hint": "Not your origin. Your catalyst. Think family.",
            "success": "[OK] Correct. Passion was yours. Fuel was his.",
            "fail": "[DENIED] Nope. The code was yours — the push was his. Retry.",
        },
        {
            "chapter": "CH.2 // THE AI KEY",
            "story": "> elder brother slides a glowing USB across the table...\n> 'kid, let me show you ChatGPT... and HOW to use it.'",
            "question": "What legendary weapon did your elder brother hand you?",
            "options": ["ChatGPT incantations", "A sword", "Biryani recipe", "WiFi password"],
            "answer": 0,
            "hint": "Prompt engineering, taught with patience.",
            "success": "[OK] AI key accepted. Sensei would be proud.",
            "fail": "[Hmm... biryani comes LATER. Focus, young dev.]",
        },
        {
            "chapter": "CH.3 // THE ARENA",
            "story": "> sensei points to a glowing arena gate...\n> 'go grind XP there. loops. arrays. no crying.'",
            "question": "Where did he send you to grind XP like a sensei?",
            "options": ["HackerRank", "Gym", "Kitchen", "Instagram reels"],
            "answer": 0,
            "hint": "Rank. Hacker. Grind. You know this.",
            "success": "[OK] Side quest cleared: 3 loops solved without crying.",
            "fail": "[DENIED] Gym? Bro codes, he doesn't curl. Retry.",
        },
        {
            "chapter": "CH.4 // THE LEGENDARY BUFF",
            "story": "> stats scan... patience: 9999 | status: busy with work...\n> yet when the kitchen server reboots, legends are cooked...",
            "question": "Patient by day, busy with work — but unstoppable chef of which legendary duo?",
            "options": ["Chicken biryani + mutton curry", "Maggi", "Salad", "npm install"],
            "answer": 0,
            "hint": "Dum + gravy. One pot legend, one curry king.",
            "success": "[OK] Chicken biryani + mutton curry buff applied. HP fully restored.",
            "fail": "[DENIED] Salad?? The legend would never. Retry.",
        },
        {
            "chapter": "CH.5 // THE DISTANCE",
            "story": "> ping brother... different cities... busy jobs... less talk...\n> packets drop, but one connection never times out...",
            "question": "What never disconnects, no matter the city?",
            "options": ["localhost:brotherhood — always connected", "Office WiFi", "Bluetooth", "VPN"],
            "answer": 0,
            "hint": "Not a network. A bond.",
            "success": "> ping brother... reply in 0ms. Connection: FOREVER.",
            "fail": "[DENIED] VPN disconnects. Brotherhood doesn't. Retry.",
        },
    ],

    # --- Puzzle 2: Base64 cipher. EDIT ME if you want a different secret ---
    # Decoded key the player must type. Encoded string is shown in-game.
    "CIPHER_DECODED": "LEGEND_DEVELOPER_TARUN_ACCESS_GRANTED",
    "CIPHER_ENCODED": "TEVHRU5EX0RFVkVMT1BFUl9UQVJVTl9BQ0NFU1NfR1JBTlRFRA==",  # base64 of above
    "CIPHER_HINT": "Base64 → ASCII. Try: echo <string> | base64 -d  •  or python: base64.b64decode(s)",

    # --- Puzzle 3: ASCII maze. '@'=player, '#'=wall, '.'=floor, 'E'=exit ---
    # Guaranteed solvable (tested). EDIT ME carefully — keep rectangular, keep @ and E.
    "MAZE_MAP": [
        "###############",
        "#@....#......E#",
        "#.###.#.#####.#",
        "#...#...#...#.#",
        "###.#####.#.#.#",
        "#...#.....#...#",
        "#.###.#####.###",
        "#.....#.....#.#",
        "#.#####.###.#.#",
        "#.......#.....#",
        "###############",
    ],

    # --- Finale ---
    "SECRET_IMAGE": "img/DUO_PHOTO.jpeg",  # bundled into the exe; revealed on button click
    "SECRET_IMAGE_CAPTION": "// recovered memory: duo-photo.jpeg //",
    "FINALE_TITLE": "PAYLOAD UNLOCKED // HAPPY BIRTHDAY RISHU BHAIYA!",
    "FINALE_MESSAGE": (
        "Happy Birthday Rishu Bhaiya — 4/10/26!\n"
        "You cleared all three gates: trivia, cipher, and the maze.\n\n"
        "Thanks for the catalyst moments — telling me I was doing good\n"
        "when it mattered, showing me how to actually use ChatGPT,\n"
        "and pointing me at HackerRank instead of letting me drift.\n\n"
        "Also on record: elite chicken biryani. Elite mutton curry.\n\n"
        "Different cities, busy schedules — connection stays up.\n"
        "Keep building.\n\n"
        "— Undefined Developer"
    ),
}

BANNER_MAIN = r"""
 _____    _    ____  _   _ _   _
|_   _|  / \  |  _ \| | | | \ | |
  | |   / _ \ | |_) | | | |  \| |
  | |  / ___ \|  _ <| |_| | |\  |
  |_| /_/   \_\_| \_\\___/|_| \_|
   L E G E N D   P R O T O C O L
"""

BANNER_WIN = r"""
__   _____  _   _  __        _____  _   _
\ \ / / _ \| | | | \ \      / / _ \| \ | |
 \ V / | | | | | |  \ \ /\ / / | | |  \| |
  | || |_| | |_| |   \ V  V /| |_| | |\  |
  |_| \___/ \___/     \_/\_/  \___/|_| \_|
"""


def resource_path(rel):
    """Resolve a bundled resource path.

    Works both when running terminal_quest.py directly and from inside
    the PyInstaller onefile exe (which unpacks data to sys._MEIPASS).
    Build with:  --add-data "img;img"
    """
    try:
        base = sys._MEIPASS  # set by PyInstaller onefile bundle
    except AttributeError:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


# ============================================================================
# Sound — synthesized WAVs (stdlib only), played via QSoundEffect w/ fallback
# ============================================================================
class SoundManager:
    # High-frequency sounds: skipped while already playing (prevents
    # restart-churn that can wedge the audio backend silent mid-game).
    LOOP_GUARD = {"tick", "move"}

    def __init__(self):
        self.enabled = True
        self.files = {}   # name -> wav path (no Qt objects here)
        self.sounds = {}  # name -> QSoundEffect, created lazily after QApplication exists
        self.dir = os.path.join(tempfile.gettempdir(), "terminal_quest_sounds")
        try:
            os.makedirs(self.dir, exist_ok=True)
        except Exception:
            pass
        self._build()

    def _write_wav(self, filename, notes, rate=22050, volume=0.35):
        """notes = list of (freq_hz, duration_sec). freq 0 = silence."""
        path = os.path.join(self.dir, filename)
        if os.path.exists(path):
            try:
                # Reuse cache only if it looks like a real WAV; else regenerate.
                if os.path.getsize(path) > 128:
                    return path
            except Exception:
                pass
        try:
            frames = bytearray()
            for freq, dur in notes:
                n = int(rate * dur)
                for i in range(n):
                    t = i / rate
                    env = 1.0 - (i / max(n, 1))  # linear decay avoids clicks
                    v = math.sin(2 * math.pi * freq * t) * volume * env if freq > 0 else 0.0
                    frames += struct.pack("<h", int(max(-1, min(1, v)) * 32767))
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(rate)
                w.writeframes(bytes(frames))
        except Exception:
            return ""
        return path

    def _build(self):
        self.files = {
            "tick":    self._write_wav("tick.wav", [(1400, 0.03)], volume=0.15),
            "error":   self._write_wav("error.wav", [(160, 0.18), (110, 0.25)], volume=0.4),
            "success": self._write_wav("success.wav", [(660, 0.12), (880, 0.2)], volume=0.35),
            "triumph": self._write_wav("triumph.wav", [(523, 0.14), (659, 0.14), (784, 0.14), (1046, 0.45)], volume=0.35),
            "move":    self._write_wav("move.wav", [(900, 0.04)], volume=0.18),
        }

    def _ensure(self, name):
        """Create the QSoundEffect on first use — only once QApplication exists.

        Effects built before QApplication (e.g. at import time) have no media
        backend and go silent; lazy creation avoids that entirely.
        """
        if not HAS_AUDIO:
            return None
        eff = self.sounds.get(name)
        if eff is not None:
            return eff
        path = self.files.get(name)
        if not path or not os.path.isfile(path):
            return None
        try:
            from PySide6.QtWidgets import QApplication
            if QApplication.instance() is None:
                return None  # too early, no event loop yet
            eff = QSoundEffect()
            eff.setSource(QUrl.fromLocalFile(path))
            eff.setVolume(0.5)
            self.sounds[name] = eff
            return eff
        except Exception:
            return None

    def play(self, name):
        if not self.enabled:
            return
        try:
            eff = self._ensure(name)
            if eff is None:
                return
            try:
                err = getattr(QSoundEffect, "Error", None)
                if err is not None and eff.status() == err:
                    # Broken source (e.g. stale cache) — reload once, skip this beat.
                    path = self.files.get(name)
                    if path and os.path.isfile(path):
                        eff.setSource(QUrl.fromLocalFile(path))
                    return
            except Exception:
                pass
            if name in self.LOOP_GUARD:
                try:
                    if eff.isPlaying():
                        return  # let the current blip finish; retriggering wedges audio
                except Exception:
                    pass
            else:
                try:
                    eff.stop()  # clean replay for one-shot chimes
                except Exception:
                    pass
            eff.play()
        except Exception:
            pass


SOUND = SoundManager()


# ============================================================================
# Helpers — theme, fonts, shake, flash
# ============================================================================
def theme():
    return CONFIG["THEMES"].get(CONFIG["THEME"], CONFIG["THEMES"]["cyber_cyan"])


def mono_font(size=11):
    f = QFont("Consolas", size)
    f.setStyleHint(QFont.Monospace)
    f.setFixedPitch(True)
    return f


def shake(widget, distance=12, duration=350):
    """Shake animation for wrong answers."""
    try:
        orig = widget.pos()
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.setKeyValueAt(0.0, orig)
        anim.setKeyValueAt(0.2, orig + QPoint(-distance, 0))
        anim.setKeyValueAt(0.4, orig + QPoint(distance, 0))
        anim.setKeyValueAt(0.6, orig + QPoint(-distance // 2, 0))
        anim.setKeyValueAt(0.8, orig + QPoint(distance // 2, 0))
        anim.setKeyValueAt(1.0, orig)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        widget._shake_anim = anim  # keep ref
    except Exception:
        pass


class ScanlineOverlay(QWidget):
    """CRT scanline overlay — transparent, mouse-transparent, always on top."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 18))
        p.setPen(QColor(0, 0, 0, 70))
        step = 4
        for y in range(0, self.height(), step):
            p.drawLine(0, y, self.width(), y)


class TypewriterBox(QPlainTextEdit):
    """Read-only terminal box with character-by-character typewriter effect."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(mono_font(11))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)
        self._queue = ""
        self._done_cb = None
        self._tick_every = 3
        self._tick_n = 0

    def type_text(self, text, done_cb=None, tick_sound=True):
        self._queue = text
        self._done_cb = done_cb
        self._tick_sound = tick_sound
        self._timer.start(random.randint(CONFIG["TYPE_MIN_MS"], CONFIG["TYPE_MAX_MS"]))

    def _step(self):
        if not self._queue:
            self._timer.stop()
            if self._done_cb:
                cb, self._done_cb = self._done_cb, None
                cb()
            return
        ch, self._queue = self._queue[0], self._queue[1:]
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(ch)
        self.ensureCursorVisible()
        self._tick_n += 1
        if getattr(self, "_tick_sound", True) and self._tick_n % self._tick_every == 0:
            SOUND.play("tick")
        self._timer.setInterval(random.randint(CONFIG["TYPE_MIN_MS"], CONFIG["TYPE_MAX_MS"]))

    def fast_forward(self):
        """Dump remaining queue instantly."""
        if self._queue:
            self.moveCursor(QTextCursor.End)
            self.insertPlainText(self._queue)
            self._queue = ""


# ============================================================================
# Maze widget — QPainter tiles, WASD / arrows
# ============================================================================
class MazeWidget(QFrame):
    CELL = 34

    def __init__(self, on_win, parent=None):
        super().__init__(parent)
        self.on_win = on_win
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFont(mono_font(12))
        self.reset()
        w = len(self.grid[0]) * self.CELL
        h = len(self.grid) * self.CELL
        self.setFixedSize(w + 4, h + 4)
        self.moves = 0

    def reset(self):
        self.grid = [list(row) for row in CONFIG["MAZE_MAP"]]
        self.moves = 0
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                if c == "@":
                    self.px, self.py = x, y
                    self.grid[y][x] = "."
        self.update()
        if hasattr(self, "moves_label"):
            self.moves_label.setText("MOVES: 0")

    def try_move(self, dx, dy):
        nx, ny = self.px + dx, self.py + dy
        if ny < 0 or ny >= len(self.grid) or nx < 0 or nx >= len(self.grid[0]):
            SOUND.play("error")
            return
        if self.grid[ny][nx] == "#":
            SOUND.play("error")
            shake(self, distance=6, duration=200)
            return
        self.px, self.py = nx, ny
        self.moves += 1
        SOUND.play("move")
        if self.grid[ny][nx] == "E":
            self.update()
            SOUND.play("success")
            QTimer.singleShot(400, self.on_win)
        self.update()
        parent = self.parent()
        if parent is not None:
            lbl = parent.findChild(QLabel, "maze_moves")
            if lbl:
                lbl.setText(f"MOVES: {self.moves}  |  WASD / ARROWS to move  |  R to reset")

    def paintEvent(self, event):
        t = theme()
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(t["bg"]))
        for y, row in enumerate(self.grid):
            for x, c in enumerate(row):
                r = self.rect().adjusted(2, 2, -2, -2)
                cx = r.x() + x * self.CELL
                cy = r.y() + y * self.CELL
                rect = (cx + 2, cy + 2, self.CELL - 4, self.CELL - 4)
                if c == "#":
                    p.fillRect(*rect, QColor(t["dim"]))
                    p.setPen(QColor(t["fg"]))
                    p.drawRect(cx + 2, cy + 2, self.CELL - 4, self.CELL - 4)
                elif c == "E":
                    p.fillRect(*rect, QColor("#FFB000" if CONFIG["THEME"] != "amber" else t["fg"]))
                    p.setPen(QColor("black"))
                    p.setFont(mono_font(14))
                    p.drawText(cx, cy, self.CELL, self.CELL, Qt.AlignCenter, "E")
                else:
                    p.setPen(QColor(t["dim"]))
                    p.drawText(cx, cy, self.CELL, self.CELL, Qt.AlignCenter, "·")
        # player
        r = self.rect().adjusted(2, 2, -2, -2)
        cx = r.x() + self.px * self.CELL
        cy = r.y() + self.py * self.CELL
        p.fillRect(cx + 2, cy + 2, self.CELL - 4, self.CELL - 4, QColor(t["fg"]))
        p.setPen(QColor("black"))
        p.setFont(mono_font(15))
        p.drawText(cx, cy, self.CELL, self.CELL, Qt.AlignCenter, "@")


# ============================================================================
# Fireworks widget — canvas celebration
# ============================================================================
class FireworksWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.particles = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._running = False

    def start(self):
        self._running = True
        self._timer.start(60)

    def stop(self):
        self._running = False
        self._timer.stop()

    def _burst(self):
        t = theme()
        colors = [t["fg"], "#FFB000", "#FF69B4", "#FFFFFF", t["accent"]]
        cx = random.randint(30, max(31, self.width() - 30))
        cy = random.randint(20, max(21, self.height() - 20))
        for _ in range(28):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.0, 4.5)
            self.particles.append({
                "x": cx, "y": cy,
                "vx": math.cos(ang) * spd, "vy": math.sin(ang) * spd,
                "life": random.randint(14, 26),
                "color": random.choice(colors),
            })

    def _tick(self):
        if self._running and len(self.particles) < 220 and random.random() < 0.6:
            self._burst()
        for pt in self.particles:
            pt["x"] += pt["vx"]
            pt["y"] += pt["vy"]
            pt["vy"] += 0.08
            pt["life"] -= 1
        self.particles = [pt for pt in self.particles if pt["life"] > 0]
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("transparent"))
        for pt in self.particles:
            p.setPen(QColor(pt["color"]))
            p.drawEllipse(int(pt["x"]), int(pt["y"]), 3, 3)


# ============================================================================
# Main window
# ============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.attempts = 0
        self.level = 1
        self.trivia_idx = 0
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(860, 640)
        self.resize(920, 720)
        self._drag_pos = None

        # Root container (stylized server-terminal border)
        root = QWidget()
        self.setCentralWidget(root)
        self.root_layout = QVBoxLayout(root)
        self.root_layout.setContentsMargins(2, 2, 2, 2)
        self.root_layout.setSpacing(0)
        self.frame = QFrame()
        self.frame.setObjectName("TermFrame")
        self.root_layout.addWidget(self.frame)
        lay = QVBoxLayout(self.frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Custom title bar
        self.titlebar = QWidget()
        self.titlebar.setObjectName("TitleBar")
        tb = QHBoxLayout(self.titlebar)
        tb.setContentsMargins(10, 6, 6, 6)
        dots = QLabel("● ● ●")
        dots.setObjectName("Dots")
        self.title_label = QLabel(f"tarun@legend-terminal: ~/legend-protocol — {CONFIG['RECIPIENT_NAME']}")
        self.title_label.setFont(mono_font(10))
        tb.addWidget(dots)
        tb.addWidget(self.title_label, stretch=1)
        self.btn_mute = QPushButton("[SOUND: ON]")
        self.btn_mute.setObjectName("ChromeBtn")
        self.btn_mute.clicked.connect(self.toggle_sound)
        self.btn_min = QPushButton("—")
        self.btn_min.setObjectName("ChromeBtn")
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close = QPushButton("X")
        self.btn_close.setObjectName("ChromeBtn")
        self.btn_close.clicked.connect(self.close)
        for b in (self.btn_mute, self.btn_min, self.btn_close):
            b.setFixedHeight(26)
            tb.addWidget(b)
        lay.addWidget(self.titlebar)

        # Top status bar
        self.status_top = QLabel()
        self.status_top.setObjectName("StatusBar")
        self.status_top.setFont(mono_font(10))
        lay.addWidget(self.status_top)

        # Stacked stages
        self.stack = QStackedWidget()
        lay.addWidget(self.stack, stretch=1)

        self.page_boot = self.build_boot()
        self.page_q1 = self.build_trivia()
        self.page_q2 = self.build_cipher()
        self.page_q3 = self.build_maze()
        self.page_win = self.build_finale()
        for pg in (self.page_boot, self.page_q1, self.page_q2, self.page_q3, self.page_win):
            self.stack.addWidget(pg)

        # Bottom status bar
        self.status_bot = QLabel("[SYS] F1/F2/F3=theme • M=mute • ENTER=continue • R=reset maze")
        self.status_bot.setObjectName("StatusBar")
        self.status_bot.setFont(mono_font(9))
        lay.addWidget(self.status_bot)

        # CRT overlay
        self.overlay = ScanlineOverlay(self.frame)
        self.overlay.setGeometry(self.frame.rect())
        self.overlay.raise_()
        self.overlay.show()

        self.apply_theme()
        self.update_status()
        self.stack.setCurrentIndex(0)
        self.start_boot()

    # --- window drag (frameless) ---
    def mousePressEvent(self, e):
        if e.position().y() < 60:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag_pos is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "overlay"):
            self.overlay.setGeometry(self.frame.rect())

    # --- theme / status ---
    def apply_theme(self):
        t = theme()
        self.setStyleSheet(f"""
            QMainWindow {{ background: {t['bg']}; }}
            #TermFrame {{ background: {t['bg']}; border: 2px solid {t['fg']}; border-radius: 8px; }}
            #TitleBar {{ background: #11161d; border-bottom: 1px solid {t['fg']}; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            #TitleBar QLabel {{ color: {t['fg']}; }}
            #Dots {{ color: {t['fg']}; font-size: 13px; }}
            #ChromeBtn {{ background: transparent; color: {t['fg']}; border: 1px solid {t['dim']};
                          font-family: Consolas; font-size: 10px; padding: 2px 10px; border-radius: 4px; }}
            #ChromeBtn:hover {{ background: {t['fg']}; color: black; }}
            #StatusBar {{ background: #0a0e13; color: {t['fg']}; padding: 4px 10px; border-top: 1px solid {t['dim']}; border-bottom: 1px solid {t['dim']}; }}
            QLabel, QPlainTextEdit, QTextEdit {{ color: {t['fg']}; }}
            QPlainTextEdit, QTextEdit, QLineEdit {{
                background: #05070b; border: 1px solid {t['dim']}; border-radius: 4px;
                color: {t['fg']}; font-family: Consolas; selection-background-color: {t['fg']}; selection-color: black;
            }}
            QLineEdit:focus {{ border: 1px solid {t['fg']}; }}
            QPushButton {{ background: transparent; color: {t['fg']}; border: 1px solid {t['fg']};
                           font-family: Consolas; font-weight: bold; padding: 8px 14px; border-radius: 4px; }}
            QPushButton:hover {{ background: {t['fg']}; color: black; }}
            QPushButton:disabled {{ color: {t['dim']}; border-color: {t['dim']}; }}
            #BigBanner {{ font-family: Consolas; }}
        """)

    def update_status(self):
        self.status_top.setText(
            f"[STATUS: SECURE | LEVEL: {self.level}/4 | ATTEMPTS: {self.attempts} | "
            f"TARGET: {CONFIG['RECIPIENT_NAME'].upper()} ({CONFIG['RECIPIENT_NICKNAME'].upper()})]"
        )

    def fail(self, widget):
        self.attempts += 1
        self.update_status()
        SOUND.play("error")
        shake(widget, distance=12)
        orig = self.frame.styleSheet()
        t = theme()
        self.frame.setStyleSheet(f"#TermFrame {{ border: 2px solid {t['warn']}; }}")
        QTimer.singleShot(280, self.apply_theme)

    def toggle_sound(self):
        SOUND.enabled = not SOUND.enabled
        self.btn_mute.setText("[SOUND: ON]" if SOUND.enabled else "[SOUND: OFF]")

    # ================= Stage 1: Boot =================
    def build_boot(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        banner = QLabel(BANNER_MAIN)
        banner.setObjectName("BigBanner")
        banner.setFont(mono_font(10))
        banner.setAlignment(Qt.AlignCenter)
        lay.addWidget(banner)
        sub = QLabel(f"// SECURE LEGEND SHELL v4.10 — challenge locked for {CONFIG['RECIPIENT_NAME']}")
        sub.setFont(mono_font(10))
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        self.boot_box = TypewriterBox()
        self.boot_box.setMinimumHeight(260)
        lay.addWidget(self.boot_box, stretch=1)
        row = QHBoxLayout()
        self.btn_boot = QPushButton("[ START PROTOCOL ]  (or press ENTER)")
        self.btn_boot.clicked.connect(self.goto_trivia)
        self.btn_boot.setEnabled(False)
        row.addStretch(1)
        row.addWidget(self.btn_boot)
        row.addStretch(1)
        lay.addLayout(row)
        return w

    def boot_lines(self):
        r, n, s = CONFIG["RECIPIENT_NAME"], CONFIG["RECIPIENT_NICKNAME"], CONFIG["SENDER_NAME"]
        return (
            f"[OK] Initializing memory for operative: {r} ...\n"
            f"[OK] Alias confirmed: {n} ...\n"
            f"[OK] Mounting sealed challenge payload ...\n"
            f"[OK] Sender signature verified: {s} ...\n"
            f"[OK] Hardening shell Chronicles/crypto/maze modules ...\n"
            f"[OK] CRT glow ............ ONLINE\n"
            f"[OK] Sound synth ......... ONLINE\n"
            f"[..] 3 gates detected: TRIVIA > CIPHER > MAZE\n"
            f"[>>] Press ENTER or click [ START PROTOCOL ] to begin, {r}.\n"
        )

    def start_boot(self):
        self.boot_box.clear()
        self.boot_box.type_text(self.boot_lines(), done_cb=lambda: self.btn_boot.setEnabled(True))

    # ================= Stage 2: Trivia =================
    def build_trivia(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        self.trivia_title = QLabel()
        self.trivia_title.setFont(mono_font(12))
        lay.addWidget(self.trivia_title)
        self.trivia_box = TypewriterBox()
        self.trivia_box.setMinimumHeight(150)
        self.trivia_box.setMaximumHeight(220)
        lay.addWidget(self.trivia_box)
        grid = QGridLayout()
        self.opt_btns = []
        for i in range(4):
            b = QPushButton()
            b.clicked.connect(lambda _=False, i=i: self.answer_trivia(i))
            self.opt_btns.append(b)
            grid.addWidget(b, i // 2, i % 2)
        lay.addLayout(grid)
        self.trivia_feed = QLabel("")
        self.trivia_feed.setFont(mono_font(10))
        lay.addWidget(self.trivia_feed)
        lay.addStretch(1)
        return w

    def goto_trivia(self):
        self.level = 1
        self.trivia_idx = 0
        self.update_status()
        self.stack.setCurrentIndex(1)
        self.show_trivia()

    def show_trivia(self):
        qs = CONFIG["TRIVIA_QUESTIONS"]
        if self.trivia_idx >= len(qs):
            self.goto_cipher()
            return
        q = qs[self.trivia_idx]
        chapter = q.get("chapter", f"Q{self.trivia_idx + 1}")
        self.trivia_title.setText(f"GATE 1/3 — OPERATION: ELDER_PROTOCOL  {chapter}  [{self.trivia_idx + 1}/{len(qs)}]")
        self.trivia_feed.setText(f"HINT: {q.get('hint', '')}")
        for b in self.opt_btns:
            b.setEnabled(False)
        self.trivia_box.clear()
        full = q.get("story", "") + "\n\nQ: " + q["question"] + "\n> awaiting input_"
        self.trivia_box.type_text(full,
                                  done_cb=lambda: self._enable_opts(q))

    def _enable_opts(self, q):
        for i, b in enumerate(self.opt_btns):
            b.setText(f"[{i + 1}] {q['options'][i]}")
            b.setEnabled(True)
        self.opt_btns[0].setFocus()

    def answer_trivia(self, i):
        q = CONFIG["TRIVIA_QUESTIONS"][self.trivia_idx]
        if i == q["answer"]:
            SOUND.play("success")
            ok_msg = q.get("success", "[OK] Correct. Next question loading...")
            self.trivia_idx += 1
            self.level = 1
            self.update_status()
            if self.trivia_idx >= len(CONFIG["TRIVIA_QUESTIONS"]):
                self.trivia_feed.setText(ok_msg + " Decrypting next module...")
                QTimer.singleShot(1100, self.goto_cipher)
            else:
                self.trivia_feed.setText(ok_msg)
                QTimer.singleShot(1100, self.show_trivia)
        else:
            self.trivia_feed.setText(q.get("fail", "[DENIED] Wrong answer. Glitch detected — try again."))
            self.fail(self.page_q1)

    # ================= Stage 3: Cipher =================
    def build_cipher(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        title = QLabel("GATE 2/3 — CIPHER // Base64 intercept")
        title.setFont(mono_font(12))
        lay.addWidget(title)
        story = QLabel(f"Agent {CONFIG['RECIPIENT_NAME']}, we intercepted an encoded payload.\nDecode it and type the CLEAR TEXT to proceed. (UPPER_SNAKE format)")
        story.setFont(mono_font(10))
        lay.addWidget(story)
        self.cipher_view = QLabel(CONFIG["CIPHER_ENCODED"])
        self.cipher_view.setFont(mono_font(13))
        self.cipher_view.setAlignment(Qt.AlignCenter)
        self.cipher_view.setFrameShape(QFrame.Box)
        self.cipher_view.setMargin(14)
        self.cipher_view.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(self.cipher_view)
        hint = QLabel(f"HINT: {CONFIG['CIPHER_HINT']}")
        hint.setFont(mono_font(9))
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.cipher_input = QLineEdit()
        self.cipher_input.setFont(mono_font(12))
        self.cipher_input.setPlaceholderText("type decoded key here, e.g. HELLO_WORLD_...")
        self.cipher_input.returnPressed.connect(self.check_cipher)
        lay.addWidget(self.cipher_input)
        row = QHBoxLayout()
        self.btn_hint = QPushButton("[ REVEAL FIRST 5 CHARS ]")
        self.btn_hint.clicked.connect(self.cipher_hint)
        self.btn_verify = QPushButton("[ DECRYPT & VERIFY ]")
        self.btn_verify.clicked.connect(self.check_cipher)
        row.addWidget(self.btn_hint)
        row.addWidget(self.btn_verify)
        lay.addLayout(row)
        self.cipher_feed = QLabel("")
        self.cipher_feed.setFont(mono_font(10))
        lay.addWidget(self.cipher_feed)
        lay.addStretch(1)
        return w

    def goto_cipher(self):
        self.level = 2
        self.update_status()
        self.stack.setCurrentIndex(2)
        self.cipher_input.setFocus()

    def cipher_hint(self):
        key = CONFIG["CIPHER_DECODED"]
        self.cipher_feed.setText(f"[HINT] Key starts with: {key[:5]}...  (length {len(key)})")
        SOUND.play("tick")

    def check_cipher(self):
        want = CONFIG["CIPHER_DECODED"].strip().upper()
        got = self.cipher_input.text().strip().upper()
        # sanity: also accept if they pasted base64-decoded with spaces
        got_norm = got.replace(" ", "_").replace("-", "_")
        if got_norm == want:
            SOUND.play("success")
            self.cipher_feed.setText("[OK] Cipher cracked. Opening maze sector...")
            QTimer.singleShot(800, self.goto_maze)
        else:
            # helpful: verify our constant is valid base64 of want (dev self-check)
            try:
                assert base64.b64encode(want.encode()).decode() == CONFIG["CIPHER_ENCODED"]
            except AssertionError:
                pass
            self.cipher_feed.setText("[DENIED] Bad key. Check padding / underscores and retry.")
            self.fail(self.page_q2)

    # ================= Stage 4: Maze =================
    def build_maze(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        title = QLabel("GATE 3/3 — MAZE // guide @ to E")
        title.setFont(mono_font(12))
        lay.addWidget(title)
        info = QLabel("WASD or ARROW KEYS to move • R to reset • Reach E to unlock payload", objectName="maze_moves")
        info.setFont(mono_font(10))
        lay.addWidget(info)
        center = QHBoxLayout()
        center.addStretch(1)
        self.maze = MazeWidget(on_win=self.goto_finale)
        center.addWidget(self.maze)
        center.addStretch(1)
        lay.addLayout(center)
        row = QHBoxLayout()
        btn_reset = QPushButton("[ RESET MAZE (R) ]")
        btn_reset.clicked.connect(self.maze.reset)
        row.addStretch(1)
        row.addWidget(btn_reset)
        row.addStretch(1)
        lay.addLayout(row)
        lay.addStretch(1)
        return w

    def goto_maze(self):
        self.level = 3
        self.update_status()
        self.stack.setCurrentIndex(3)
        self.maze.reset()
        self.maze.setFocus()

    # ================= Stage 5: Finale =================
    def build_finale(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 14, 18, 14)
        banner = QLabel(BANNER_WIN)
        banner.setFont(mono_font(9))
        banner.setAlignment(Qt.AlignCenter)
        lay.addWidget(banner)
        self.fire = FireworksWidget()
        lay.addWidget(self.fire)
        title = QLabel(CONFIG["FINALE_TITLE"])
        title.setFont(mono_font(12))
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        self.finale_msg = QPlainTextEdit()
        self.finale_msg.setFont(mono_font(11))
        self.finale_msg.setReadOnly(True)
        self.finale_msg.setPlainText(CONFIG["FINALE_MESSAGE"])
        self.finale_msg.setMinimumHeight(190)
        lay.addWidget(self.finale_msg, stretch=1)
        row = QHBoxLayout()
        btn_photo = QPushButton("[ OPEN SECRET PHOTO ]")
        btn_photo.clicked.connect(self.open_photo)
        btn_replay = QPushButton("[ REPLAY PROTOCOL ]")
        btn_replay.clicked.connect(self.replay)
        row.addStretch(1)
        row.addWidget(btn_photo)
        row.addWidget(btn_replay)
        row.addStretch(1)
        lay.addLayout(row)
        return w

    def goto_finale(self):
        self.level = 4
        self.update_status()
        # refresh message in case CONFIG edited live
        self.finale_msg.setPlainText(CONFIG["FINALE_MESSAGE"])
        self.stack.setCurrentIndex(4)
        SOUND.play("triumph")
        self.fire.start()

    def open_photo(self):
        path = resource_path(CONFIG["SECRET_IMAGE"])
        if not os.path.isfile(path):
            QMessageBox.warning(self, "Missing photo",
                f"Could not find:\n{path}\n\nKeep the img folder next to the script\n(or rebuild the exe with --add-data \"img;img\").")
            return
        pix = QPixmap(path)
        if pix.isNull():
            QMessageBox.warning(self, "Photo error",
                "Found the file but could not decode it as an image.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(CONFIG.get("SECRET_IMAGE_CAPTION", "secret-photo"))
        dlg.setStyleSheet(self.styleSheet())  # reuse terminal theme
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(12, 12, 12, 12)
        lab = QLabel()
        lab.setAlignment(Qt.AlignCenter)
        lab.setPixmap(pix.scaled(680, 520, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        lay.addWidget(lab)
        cap = QLabel(CONFIG.get("SECRET_IMAGE_CAPTION", ""))
        cap.setFont(mono_font(10))
        cap.setAlignment(Qt.AlignCenter)
        lay.addWidget(cap)
        row = QHBoxLayout()
        row.addStretch(1)
        btn_close = QPushButton("[ CLOSE ]")
        btn_close.clicked.connect(dlg.accept)
        row.addWidget(btn_close)
        row.addStretch(1)
        lay.addLayout(row)
        dlg.setMinimumSize(420, 320)
        dlg.exec()

    def replay(self):
        self.fire.stop()
        self.attempts = 0
        self.trivia_idx = 0
        self.cipher_input.clear()
        self.update_status()
        self.stack.setCurrentIndex(0)
        self.start_boot()

    # --- global keys ---
    def keyPressEvent(self, event):
        k = event.key()
        # theme shortcuts
        if k == Qt.Key_F1:
            CONFIG["THEME"] = "neon_green"; self.apply_theme(); return
        if k == Qt.Key_F2:
            CONFIG["THEME"] = "cyber_cyan"; self.apply_theme(); return
        if k == Qt.Key_F3:
            CONFIG["THEME"] = "amber"; self.apply_theme(); return
        if k == Qt.Key_M:
            self.toggle_sound(); return
        # boot: ENTER continues
        if self.stack.currentIndex() == 0 and k in (Qt.Key_Return, Qt.Key_Enter):
            if self.btn_boot.isEnabled():
                self.goto_trivia()
            else:
                self.boot_box.fast_forward()
            return
        # trivia: 1-4 shortcuts
        if self.stack.currentIndex() == 1 and k in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4):
            idx = k - Qt.Key_1
            if self.opt_btns[idx].isEnabled():
                self.answer_trivia(idx)
            return
        # maze keys
        if self.stack.currentIndex() == 3:
            mapping = {
                Qt.Key_W: (0, -1), Qt.Key_Up: (0, -1),
                Qt.Key_S: (0, 1), Qt.Key_Down: (0, 1),
                Qt.Key_A: (-1, 0), Qt.Key_Left: (-1, 0),
                Qt.Key_D: (1, 0), Qt.Key_Right: (1, 0),
            }
            if k in mapping:
                self.maze.try_move(*mapping[k])
                return
            if k == Qt.Key_R:
                self.maze.reset()
                return
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.setWindowTitle(f"Legend Protocol — {CONFIG['RECIPIENT_NAME']}")
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
