import io
import tkinter as tk
from typing import Tuple, Optional
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

    :arg address: A string IP address and an integer port where MPD is running.
    :arg password: Password for auth with the MPD server.

    :var connection: Connection to MPD.
    :var controler: Interface to MPD.

    :var canvas: Cavnas on which the album art is drawn.
    :var canvas_width: Width of the canvas. Updated with window resize events.
    :var canvas_height: Height of the canvas. Updated with window resize events.

    :var album_art_original: Album art originally downloaded from MPD, resized
        to 512x512 if larger then that.
    :var album_art: Album art displayed on the canvas.
    :var album_queue: Queue used for communication between the main GUI process
        and the player change monitoring process.
    :var album: Name of the currently playing album.
    :var album_connection: Connection to MPD used for monitoring player changes.
    :var album_controler: Interface to MPD used for monitoring player changes.
    :var album_process: Process that waits for player changes using the `idle`
        command.
    """

    def __init__(self, address: Tuple[str, int], password: Optional[str]):
        super().__init__()

        # Connect to MPD.
        self.__connection: Connection = Connection(*address)
        self.__controler: Controler = Controler(self.__connection, password)

        # Configure window.
        self.title('MPCover')
        self.geometry('512x512')
        self.configure(background='#060606')

        # Window close hook.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Canvas for album art.
        self.__canvas: tk.Canvas = tk.Canvas(
            self, highlightthickness=0, background='#060606')
        self.__canvas.grid(
            column=0, row=0, padx=12, pady=12, sticky=(tk.N, tk.W, tk.E, tk.S))
        self.__canvas.bind('<Configure>', self.__display_album_art)

        # Canvas size, updated on `<Configure>` events.
        self.__canvas_width: int = 100
        self.__canvas_height: int = 100

        # Max wights on canvas at (0, 0).
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Original image retrieved from MPD. Kept in order to stop repeated
        # resizing from lowering the quality of the image by always using
        # the original image when resizing instead of the displayed one.
        # Always first resized to 512x512 for better performance with rapid
        # window size changes.
        self.__album_art_original: Optional[Image] = None
        # Image rescaled for window size.
        self.__album_art: Optional[ImageTk.PhotoImage] = None
        # Queue for passing changes from the album process.
        self.__album_queue: Queue = Queue()
        # Album name. Used for tracking when the album changes to trigger
        # downloading new album art.
        self.__album: str = ''

        # Player change detection. Starts a new process for idling while
        # waiting for a player change to occur. This process fills a queue
        # with detected changes while the `idle_player_change` constantly
        # reads and empties the queue while initiating the album art updates.
        # Check for updates when idle.
        self.after(50, self.idle_player_change)
        # New connection for idling.
        self.__album_connection: Connection = Connection(*address)
        self.__album_controler: Controler = Controler(self.__album_connection, password)
        # Process to idle independently of the main GUI process.
        self.__album_process: Process = Process(
            target=self.__album_controler.idle,
            args=(self.__album_queue, 'player', 'playlist')
        )
        self.__album_process.start()

        # Initial album art get.
        self.__get_album_art()

    def on_close(self):
        """
        Called by `tkinter` on window close. The `tkinter` window can close on
        its own, this only overrides the closing process to terminate the
        player change monitoring process before exiting.
        """

        self.__album_process.terminate()
        self.destroy()

    def idle_player_change(self):
        """
        Called by the album process when a change in the player is detected
        (seek, change song, etc.)
        """

        # Read queue if it's not empty and update album art.
        if not self.__album_queue.empty():
            self.__album_queue.get()
            self.__get_album_art()

        # Run again in .5 seconds.
        self.after(50, self.idle_player_change)

    def __get_album_art(self):
        """
        Downloads album art for the current song if the album has changed
        since the last call. Resizes the downloaded art to 512x512 if it's
        larger then that. Calls `display_album_art`.
        """

        # Don't display album art if the current song is stop.
        playback_state: str = self.__controler.status()['state']
        if playback_state == 'stop':
            logger.debug('Song is stopped, won\'t display album art.')
            self.__clear_album_art()
            return

        # Get album of the currently playing song.
        current_song_data: Dict[str, Any] = self.__controler.currentsong()
        if 'Album' not in current_song_data:
            # Song does not have an Album tag, just give up... for now?
            logger.debug('Current song does not have an album tag, giving up...')
            self.__clear_album_art()
            return
        album: str = current_song_data['Album']

        # Return if it's the same album as the currently loaded album art.
        if album == self.__album:
            return
        self.__album = album

        logger.debug('Getting new album art.')

        # Get album art from MPD.
        data: bytes = self.__controler.albumart()
        if data is not None:
            # Open as Pillow image.
            self.__album_art_original = Image.open(io.BytesIO(data))
            # Resize if image is large.
            if self.__album_art_original.size > (512, 512):
                self.__album_art_original = \
                    self.__album_art_original.resize((512, 512))
        else:
            self.__album_art_original = None

        # Display the new album art.
        self.__display_album_art()

    def __display_album_art(self, event: Optional[tk.Event] = None):
        """
        Displays album art. Called by `get_album_art` and by `tkinter` on
        window resize.

        :arg event: Info about the window resize event.
        """

        # Get canvas size if it was resized.
        if event is not None:
            self.__canvas_width = event.width
            self.__canvas_height = event.height

        self.__clear_album_art()

        # If no album art is available, leave the canvas blank.
        if self.__album_art_original is None:
            return

        # Get square dimentions (assuming that album art is square).
        size = min(self.__canvas_width, self.__canvas_height)

        # Convert the album art image to a Tk Photo Image and resize
        # to match canvas size.
        self.__album_art = ImageTk.PhotoImage(
            self.__album_art_original.resize((size, size)))

        # Draw album art to canvas.
        self.__canvas.create_image(
            self.__canvas_width // 2,
            self.__canvas_height // 2,
            image=self.__album_art,
        )

    def __clear_album_art(self):
        self.__album = None
        self.__canvas.delete('all')
