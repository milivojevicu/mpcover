import re
import sys
import time
import socket
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class Connection:
    CHUNK_SIZE = 1024

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.__sock: Optional[socket.socket] = None

        address_info: List[Tuple] = socket.getaddrinfo(
            host, port, socket.AF_UNSPEC,
            socket.SOCK_STREAM, socket.IPPROTO_TCP,
        )

        for address_family, socket_kind, protocol, _, address in address_info:
            try:
                logger.debug(
                    'Attempting to connect: %r %r %d %r.',
                    address_family, socket_kind, protocol, address
                )
                sock = socket.socket(address_family, socket_kind, protocol)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                sock.settimeout(1)
                sock.connect(address)
                self.__sock = sock
            except socket.error as error:
                logger.debug('Attempt failed: %r.', error)
                if sock is not None:
                    sock.close()
            finally:
                if self.__sock is None:
                    logger.critical('Failed to connect to %s:%d.', host, port)
                    sys.exit(101)

        if self.__sock is None:
            logger.critical('No info found for %s:%d, can\'t connect.', host, port)
            sys.exit(102)

        logger.debug('Connected.')

    def __enter__(self):
        return self

    def __exit__(self, exec_type, exec_value, traceback) -> bool:
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
        self.__sock.close()

    def send(self, send_data: bytes):
        send_data = send_data + '\n'.encode()
        self.__sock.sendall(send_data)

    def recv(self) -> bytes:
        recv_data = ''.encode()
        recv_end = False

        while not recv_end:
            recv_datum = self.__sock.recv(self.CHUNK_SIZE)
            recv_data += recv_datum

            if len(recv_datum) < self.CHUNK_SIZE:
                recv_end = True

        return recv_data
