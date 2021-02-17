import sys
import json
import time
from pathlib import Path
import tkinter as tk
import tkinter.filedialog
sys.path.insert(0, './game')
from board import Board
from singleplayer import Singleplayer

DATA_DIR = Path("./game/data")
SP_DELAY = 100
LAST_BOT = ".lastbot"

class Client:
    def __init__(self):
        self.menu = dict()
        self.root = root = tk.Tk()
        root.configure(background="black")
        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        self.m_frame = frame = tk.Frame(root, bg="black")
        frame.pack(side=tk.RIGHT, anchor="n")
        label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, fg="white", bg="gray20")
        label.pack(side=tk.TOP, anchor="n")
        filename = sys.argv[1] if len(sys.argv) == 2 else "./game/data/game.json"
        self.game = json.loads(Path(filename).read_text())
        tileset = json.loads(DATA_DIR.joinpath("tileset.json").read_text())
        tileset["data"] = DATA_DIR.joinpath(tileset["file"]).read_bytes()
        self.board = Board(tileset, canvas, label)

        lastbot = Path(LAST_BOT)
        if lastbot.exists() and Path(lastbot.read_text()).exists():
            self.bot = Path(lastbot.read_text())
        else:
            self.bot = None

        self.bot_label = tk.Label(frame, font=("TkFixedFont",),
                         justify=tk.RIGHT, bg="gray15")
        self.bot_label.pack(side=tk.TOP, anchor="n", fill="x", pady=5)
        self.bot_label["text"] = f"bot: {self.bot.stem if self.bot else 'undefined'}"
        self.bot_label["fg"] = "green" if self.bot else "red"

        self.init_level()
        self.show_menu()
        root.mainloop()

    def init_level(self):
        self.board.load(self.game.get("maps")[0], self.game.get("tiles"))

    def add_menu_button(self, name, text, handler):
        self.menu[name] = b = tk.Button(self.m_frame, text=text, fg="gray1", bg="gray30")
        b.config(command=handler)
        b.pack(side=tk.TOP, padx=1, fill="x")

    def show_menu(self):
        self.add_menu_button("change_bot", "change bot", self.change_bot)
        self.add_menu_button("sp", "single player", self.start_sp)
        self.add_menu_button("mp", "multiplayer", self.start_mp)
        self.add_menu_button("exit", "exit", lambda: self.root.destroy())

    def change_bot(self):
        newbot = tkinter.filedialog.askopenfilename(
            initialdir=Path("bots"), filetypes=[("python files", "*.py")])
        if newbot and Path(newbot).exists():
            self.bot = Path(newbot)
            self.bot_label["text"] = f"bot: {self.bot.stem}"
            self.bot_label["fg"] = "green"
            Path(LAST_BOT).write_text(str(self.bot))

    def start_sp(self):
        game = Singleplayer(self.board, DATA_DIR)
        def update():
            t = time.time()
            if game.play():
                dt = int((time.time() - t) * 1000)
                self.root.after(max(SP_DELAY - dt, 0), update)
            else:
                self.board.label["text"] += "\n\nGAME OVER!"
        self.root.after(0, update)

    def start_mp(self):
        pass

client = Client()