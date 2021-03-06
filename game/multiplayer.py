import sys
import json
import signal
import asyncio
from contextlib import suppress
from queue import Queue
from threading import Thread
from game import Game, Player
from importlib import import_module, reload

sys.path.insert(0, './bots')

class Multiplayer:
    def __init__(self, board, server, port, username):
        self.queue = Queue()
        self.board = board
        self.server = server
        self.port = port
        self.username = username
        self.loop = loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        loop.create_task(self.connect())
        loop.add_signal_handler(signal.SIGTERM, self.disconnect, loop)
        loop.add_signal_handler(signal.SIGINT,  self.disconnect, loop)
        def run_loop():
            try:
                loop.run_forever()
                loop.run_until_complete(loop.shutdown_asyncgens())
                tasks = asyncio.all_tasks(loop)
                for task in tasks:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        loop.run_until_complete(task)
            finally:
                loop.close()
        self.thread = Thread(target=run_loop)
        self.thread.start()

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(self.server, self.port)
        except:
            return self.handle_error("Can't connect to server!")
        self.writer.write("ping".encode())
        await self.writer.drain()
        data = await self.reader.read(100)
        print(f'Received: {data.decode()!r}')
        if data.decode() == "pong":
            self.queue.put(("success", "Connected!"))
            self.queue.put(("switch_tab", "mp_server"))
        else:
            self.handle_error("Failed server handshake")

    async def resp(self, message):
        self.writer.write(message.encode())
        await self.writer.drain()
        print("sent: "+message)

    async def listener(self):
        while not self.loop.is_closed():
            data = await self.reader.read()
            message = data.decode()
            if not message:
                await asyncio.sleep(.01)
                continue
            print("got: "+message)
            if message == "player":
                # server requests player info
                print(self.username)
                await self.resp(json.dumps({
                    "name": self.username,
                    "bot": self.bot,
                    "tile": self.tile
                }))
            elif message.startswith("map"):
                # server sets current map
                try:
                    data = message.split()[1]
                    self.board.load(json.loads(data))
                    self.resp("ok")
                except Exception as e:
                    print(e)
                    self.handle_error("Failed to load map")
            elif message.startswith("state"):
                # server sets current game state
                pass
            elif message == "200":
                self.queue.put(("success", "server: ok"))
            elif message == "400":
                self.queue.put(("success", "server: bad request"))
            else:
                pass

    def handle_error(self, message):
        self.queue.put(("error", message))

    async def start_game(self):
        # TODO: handle exceptions more nicely
        try:
            if self.bot in sys.modules:
                 reload(sys.modules[self.bot])
            self.script = import_module(self.bot).script
        except:
            raise Exception(f"Failed to load bot: {bot}")
        # try:
        self.writer.write("start".encode())
        await self.writer.drain()
        await self.listener()
        # except Exception as e:
        #     raise Exception(f"Failed to start server game:"+str(e))


    def play(self, player_bot, player_tile):
        self.bot = player_bot
        self.tile = player_tile
        asyncio.run_coroutine_threadsafe(self.start_game(), self.loop)

    # async def exit_loop(self):


    def disconnect(self):
        if not self.loop.is_closed():
            print("disconnecting mp")
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()
