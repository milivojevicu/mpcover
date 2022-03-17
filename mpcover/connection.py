import re
import sys
import time
import socket
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class Connection:
    """
    Connection to an MPD server.

    :arg host: String IP address.
    :arg port: Integer port.

    :var sock: Python socket to MPD using `host` and `port`.
    """

    CHUNK_SIZE = 1024

    def __init__(self, host: str, port: int):
        # Save input data.
        self.host = host
        self.port = port

        # Initialize a variable for the socket.
        self.__sock: Optional[socket.socket] = None

        # Get info about the provided address/port.
        address_info: List[Tuple] = socket.getaddrinfo(
            host, port, socket.AF_UNSPEC,
            socket.SOCK_STREAM, socket.IPPROTO_TCP,
        )

        # Try different combinations until connection is established.
        for address_family, socket_kind, protocol, _, address in address_info:
            try:
                logger.debug(
                    'Attempting to connect: %r %r %d %r.',
                    address_family, socket_kind, protocol, address
                )

                # Create a socket with data from `getaddrinfo`.
                sock = socket.socket(address_family, socket_kind, protocol)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.settimeout(1)
                sock.connect(address)
                self.__sock = sock
            except socket.error as error:
                # Failed to connect.
                logger.debug('Attempt failed: %r.', error)
                if sock is not None:
                    sock.close()
            finally:
                # If unable to establish connection, exit.
                if self.__sock is None:
                    logger.critical('Failed to connect to %s:%d.', host, port)
                    sys.exit(101)

        # If no info was found about the address/port, exit.
        if self.__sock is None:
            logger.critical('No info found for %s:%d, can\'t connect.', host, port)
            sys.exit(102)

        logger.debug('Connected.')

    def __enter__(self):
        """
        Standard Python method implemented for use with the `with` statement.
        """

        return self

    def __exit__(self, exec_type, exec_value, traceback) -> bool:
        """
        Standard Python method implemented for use with the `with` statement.

        :arg exec_type: Exception type.
        :arg exec_type: Exception value.
        :arg traceback: Traceback.
        """

        logger.debug('Connection exit: %r %r %r.', exec_type, exec_value, traceback)
        self.close()

        return False

    @property
    def timeout(self) -> Optional[int]:
        return self.__sock.gettimeout()

    @timeout.setter
    def timeout(self, timeout: Optional[int]):
        self.__sock.settimeout(timeout)

    def close(self):
        """
        Close the socket/connection.
        """

        self.__sock.close()

    def send(self, send_data: bytes):
        """
        Send bytes to MPD.

        :arg send_data: Bytes to send.
        """

        send_data = send_data + '\n'.encode()
        self.__sock.sendall(send_data)

    def recv(self) -> bytes:
        """
        Recieve bytes from MPD. Is blocking, but timeout is set to 1 second by
        default.

        :return: Recieved bytes.
        """

        recv_data = ''.encode()

        # Recieve data in chunks.
        while True:
            # Get chunk.
            recv_datum = self.__sock.recv(self.CHUNK_SIZE)
            # Append chunk.
            recv_data += recv_datum

            # Don't exit until all data has been recieved.
            if len(recv_datum) < self.CHUNK_SIZE:
                break

        return recv_data
