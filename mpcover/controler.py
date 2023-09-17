from __future__ import annotations

import logging
import re
import sys
from multiprocessing import Queue
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Union

from .connection import Connection

logger = logging.getLogger(__name__)


def generic_command(method: Callable) -> Callable:
    """
    Decorator for generic command methods. Uses the method name as the
        command.

    :arg method: The method being decorated.

    :return: Lambda function for running the generic command and parsing its
        output.
    """

    return lambda self: self.parse_items(list(self.run(method.__code__.co_name)))


class Controler:
    """
    MPD controler class. Containes methods that send commands and return
    parsed responses.

    :var connection: Connection to the MPD server.
    :var mpd_version: Version of the MPD server, recieved on connection open
        from the server.
    """

    # Item regex. Group 1 is the key and group 2 is the value.
    RE_ITEM = re.compile("^([A-Za-z-_]*): (.*)$")
    # Regex patterns for primitive data types. Used when parsing response items.
    RE_INTEGER = re.compile("^[0-9]+$")
    RE_FLOATING = re.compile("^[0-9.]+$")

    def __init__(self, connection: Connection, password: Optional[str] = None):
        self.__connection = connection
        self.__password = password

        self.__mpd_version = self.__connection.recv()[7:-1].decode()
        logging.info("MPD %s", self.__mpd_version)
        self.__auth()

    def __del__(self):
        """Destructor, closes connection to MPD server."""

        self.__connection.close()

    def __auth(self):
        """
        Perform authentication.

        :arg password: Optional password.
        """

        if self.__password is not None:
            self.__connection.send(f'password "{self.__password}"'.encode())
            response = self.__connection.recv().decode()
            if response != "OK\n":
                logger.critical("Failed to authenticate with message: %s", response[:-1])
                logger.critical("Exiting...")
                sys.exit(201)
            else:
                logger.info("Successful authentication.")
        else:
            logger.info("No password provided, assuming successful connection.")

    def run(self, command: str, *args: str) -> Iterable[bytes]:
        """
        Encode and send a command to the MPD server, then deocde and yeild
        the response.

        :arg command: Command string.
        :arg *args: Positional arguments for the command.

        :return: Yeilds bytes. Finished when success or error item is
            encounterd.
        """

        # Encode command string.
        data = command.encode()

        # Iterate of arguments.
        for arg in args:
            # If an argument is not a string, convert it to a string.
            if not isinstance(arg, str):
                arg = str(arg)

            # If an argument contains space characters, put it in quotes.
            if " " in arg:
                arg = '"' + arg + '"'

            # Encode and append argument to command.
            data += b" " + arg.encode()

        attempts = 0

        # Set default value of respnse to an empty string,
        # equates it with getting no respnose from `recv`
        # in case of broken pipe.
        response = "".encode("UTF-8")
        while attempts < 3:
            try:
                # Send command to MPD.
                self.__connection.send(data)
                # Gather response.
                response = self.__connection.recv()
            except BrokenPipeError as error:
                logger.error(error)
            except OSError as error:
                logger.error(error)

            # No respnse, try again.
            if len(response) == 0:
                logger.debug("Got no response, attempting to reconnect.")
                attempts += 1
                # Reconnect.
                self.__connection = Connection(self.__connection.host, self.__connection.port)
                # Flush MPD version output.
                self.__connection.recv()
                # Authenticate.
                self.__auth()
                continue

            break

        yield from self.__parse_response(response)

    def __parse_item(self, item: bytes) -> Tuple[str, Union[str, int, float, bytes]]:
        """
        Generic parser for single items from a response.

        :return: A tuple of key and value.
        """

        # Handle binary items.
        if item[:13] == b"binary_data: ":
            return "binary_data", item[13:]

        # Get groups.
        match = self.RE_ITEM.match(item.decode())

        if match is None:
            return "", ""

        # Evaluate value.
        value = match.group(2)
        if self.RE_INTEGER.match(value):
            value = int(value)
        elif self.RE_FLOATING.match(value):
            value = float(value)

        return match.group(1), value

    def parse_items(self, items: List[bytes]) -> Dict[str, Union[str, int, float, bytes]]:
        """
        Generic response item parser.

        :return: A dictionary with parsed items.
        """

        return dict([self.__parse_item(item) for item in items])

    def __parse_response(self, response: bytes) -> Iterable[bytes]:
        """
        Processs the response sent by MPD. Yields items.

        :arg response: Response from MPD. Can be empty in case of connection issues.

        :return: Yeilds byte arrays, one per item in response. No response from MPD returns an
            empty list.
        """

        # Items are spearated by '\n' characters.
        # Last item is either 'OK' on success or 'ACK ...' on error.
        # Iterate over response data.

        item = b""  # Curently processed item.
        size = -1  # Size used when reading binary items.

        for i in range(len(response)):
            # Get byte from response. Can't use for each loop because it
            # returns integers instead of bytes. Indexing without a range
            # also returns integers instead of bytes.
            byte = response[i : i + 1]

            # End of an item.
            if size < 0 and byte == b"\n":
                # Last item, command success.
                if item == b"OK":
                    return

                # Last item, command error.
                if item[:3] == b"ACK":
                    if b"you don't have permission for" in item:
                        # No password provided but auth required.
                        logger.critical(item[3:].decode())
                        sys.exit(202)
                    else:
                        # Log error and return.
                        logger.error(item[3:].decode())
                        return

                # Handle binary items.
                if item[:8] == b"binary: ":
                    yield item
                    size = int(item[8:].decode()) - 1
                    item = b"binary_data: "
                    continue

                # Not an end response item, yield.
                yield item

                # Reset item buffer and continue.
                item = b""
                continue

            # Append byte to buffer.
            item += byte
            size -= 1

        # Removed when fixing issue #6 in pull request #53. Missing album art
        # causes MPD to not return anything, so this is a workaround. The accompanying
        # change to the `run` method cathes the `OSErrror`s produced by the socket
        # and in that case this method gets no repsonse, and an empty response is passed on.
        """
        logger.critical(
            "Should not be possible to get to this point with a valid"
            " response from the server, exiting..."
        )
        sys.exit(203)
        """

        return []

    @generic_command
    def stats(self):
        """
        Get statistics.

        :return: Dictionary with statistics (`Dict[str, int]`).
        """

    @generic_command
    def status(self):
        """
        Get player and volume status.

        :return: Dictionary with status (`Dict[str, Union[str, int]]`).
        """

    @generic_command
    def currentsong(self):
        """
        Get current song info.

        :return: Dictionary with information about the currently active song (`Dict[str, Union[str, int]]`).
        """

    def albumart(self, path: Optional[str] = None) -> Optional[bytes]:
        """
        Get album art. MPD looks for a `cover.[png|jpg|tiff|bmp]` file.

        :arg path: Path to an audio file or album directory. If none is
            specified, album art for the current song will be returned.

        :return: Album art as bytes or `None` if album art does not exist.
        """

        # Get current song path if no path was provided.
        real_path: str
        if path is None:
            real_path = self.currentsong()["file"]
        else:
            real_path = path

        # Initliaize offset counter, total size and result buffer.
        offset: int = 0
        size: int = 1
        result: bytes = b""

        # Load chunks until offset reaches end of file.
        while offset < size:
            # Run command with offset.
            items = list(self.run("albumart", real_path, str(offset)))
            # If length of items is 0, an error occured. Requested album art
            # probably does not exist.
            if len(items) == 0:
                return None

            # Parse items.
            items = self.parse_items(items)
            # Get data from parsed items.
            items_binary: int = items["binary"]  # type: ignore
            items_binary_data: bytes = items["binary_data"]  # type: ignore
            items_size: int = items["size"]  # type: ignore

            # Increase offset with size of recieved binary data.
            offset += items_binary
            # Update size again since it's probably faster then an if
            # statement and MPD always returns the same size.
            size = items_size
            # Append new binary data to result.
            result += items_binary_data

        return result

    def idle(self, queue: Queue, *subsystems: str):
        """
        Removes the connection timeout and runs an `idle` command to monitor
        specified subsystems. Put the detected change on the provided queue.
        Blocking, never exits.
        """

        self.__connection.timeout = None
        while True:
            result = self.parse_items(list(self.run("idle", *subsystems)))
            logger.debug("Subsystem change detected, puting on queue.")
            queue.put(result["changed"])
