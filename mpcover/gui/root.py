import io
import tkinter as tk
from typing import Tuple
from tkinter import ttk
from logging import getLogger
from multiprocessing import Queue, Process

from PIL import Image, ImageTk

from ..controler import Controler
from ..connection import Connection

logger = getLogger(__name__)


class Root(tk.Tk):
    """
    Main graphical user inteface class.

    :arg controler: MPD controler class.
    """

    def __init__(self, address: Tuple[str, int]):
        super().__init__()
        self.__connection = Connection(*address)
        self.__controler = Controler(self.__connection)

        # Configure window.
        self.title('PyMPC')
        self.geometry('512x512')
        self.configure(background='#060606')

        # Window close hook.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Canvas for album art.
        self.__canvas = tk.Canvas(
            self, highlightthickness=0, background='#060606')
        self.__canvas.grid(
            column=0, row=0, padx=12, pady=12, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.__canvas.bind('<Configure>', self.__display_album_art)

        # Canvas size, updated on `<Configure>` events.
        self.__canvas_width = 100
        self.__canvas_height = 100

        # Max wights on canvas at (0, 0).
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Original image retrieved from MPD. Kept in order to stop repeated
        # resizing from lowering the quality of the image by always using
        # the original image when resizing instead of the displayed one.
        # Always first resized to 512x512 for better performance with rapid
        # window size changes.
        self.__album_art_original = None
        # Image rescaled for window size.
        self.__album_art = None
        # Queue for passing changes from the album process.
        self.__album_queue = Queue()
        # Album name. Used for tracking when the album changes to trigger
        # downloading new album art.
        self.__album = None
        # Check for updates when idle.
        self.after(1, self.idle_player_change)
        self.__album_connection = Connection(*address)
        self.__album_controler = Controler(self.__album_connection)
        self.__album_process = Process(
            target=self.__album_controler.idle,
            args=(self.__album_queue, 'player')
        )
        self.__album_process.start()

        # Initial album art get.
        self.__get_album_art()

    def on_close(self):
        self.__album_process.terminate()
        self.destroy()

    def idle_player_change(self):
        if not self.__album_queue.empty():
            self.__album_queue.get()
            self.__get_album_art()

        self.after(1, self.idle_player_change)

    def __get_album_art(self):
        album = self.__controler.currentsong()['Album']
        if album == self.__album:
            return
        self.__album = album

        logger.debug('Getting new album art.')

        data = self.__controler.albumart()
        if data is not None:
            self.__album_art_original = Image.open(io.BytesIO(data))
            if self.__album_art_original.size > (512, 512):
                self.__album_art_original = \
                    self.__album_art_original.resize((512, 512))
        else:
            self.__album_art_original = None
        self.__display_album_art()

    def __display_album_art(self, event = None):
        if event is not None:
            self.__canvas_width = event.width
            self.__canvas_height = event.height

        self.__canvas.delete('all')

        if self.__album_art_original is None:
            return

        size = min(self.__canvas_width, self.__canvas_height)

        self.__album_art = ImageTk.PhotoImage(
            self.__album_art_original.resize((size, size)))

        self.__canvas.create_image(
            self.__canvas_width // 2,
            self.__canvas_height // 2,
            image=self.__album_art,
        )
