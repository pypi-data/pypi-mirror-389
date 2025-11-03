"""
SocketDll을 위한 Python 래퍼 클래스
사용하기 쉬운 객체 지향 인터페이스 제공
"""

import ctypes
import os
import sys
import platform

class SocketDLL:
    """C++ SocketDll을 위한 Python 래퍼"""

    def __init__(self, dll_path=None):
        """
        DLL 초기화

        Args:
            dll_path: DLL 파일 경로 (None이면 자동 탐색)
        """
        if dll_path is None:
            # 패키지 내부 DLL 경로 찾기
            dll_path = self._find_dll()

        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"DLL 파일을 찾을 수 없습니다: {dll_path}")

        self.lib = ctypes.CDLL(dll_path)
        self._setup_functions()

    def _find_dll(self):
        """패키지 내부에서 DLL 찾기"""
        # 현재 파일의 디렉토리
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # bin 폴더 경로
        bin_dir = os.path.join(current_dir, 'bin')

        # 플랫폼별 DLL 이름
        if platform.system() == 'Windows':
            dll_name = 'SocketDll.dll'
        elif platform.system() == 'Linux':
            dll_name = 'libSocketDll.so'
        elif platform.system() == 'Darwin':  # macOS
            dll_name = 'libSocketDll.dylib'
        else:
            raise OSError(f"지원하지 않는 플랫폼: {platform.system()}")

        dll_path = os.path.join(bin_dir, dll_name)
        return dll_path

    def _setup_functions(self):
        """함수 시그니처 정의"""
        # create_tcp_server
        self.lib.create_tcp_server.argtypes = [ctypes.c_int]
        self.lib.create_tcp_server.restype = ctypes.c_int

        # server_close
        self.lib.server_close.argtypes = [ctypes.c_int]
        self.lib.server_close.restype = ctypes.c_int

        # server_accept
        self.lib.server_accept.argtypes = [ctypes.c_int]
        self.lib.server_accept.restype = ctypes.c_int

        # connect_tcp
        self.lib.connect_tcp.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.lib.connect_tcp.restype = ctypes.c_int

        # send_data
        self.lib.send_data.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.lib.send_data.restype = ctypes.c_int

        # receive_data
        self.lib.receive_data.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        self.lib.receive_data.restype = ctypes.c_int

        # close_socket
        self.lib.close_socket.argtypes = [ctypes.c_int]
        self.lib.close_socket.restype = ctypes.c_int

        # get_last_error
        self.lib.get_last_error.argtypes = []
        self.lib.get_last_error.restype = ctypes.c_char_p

    def create_server(self, port):
        """TCP 서버 생성"""
        return self.lib.create_tcp_server(port)

    def close_server(self, server_fd):
        """서버 닫기"""
        return self.lib.server_close(server_fd)

    def accept_client(self, server_fd):
        """클라이언트 연결 수락"""
        return self.lib.server_accept(server_fd)

    def connect(self, host, port):
        """TCP 서버에 연결"""
        return self.lib.connect_tcp(host.encode('utf-8'), port)

    def send(self, socket_fd, data):
        """데이터 전송"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self.lib.send_data(socket_fd, data, len(data))

    def receive(self, socket_fd, buffer_size=4096):
        """데이터 수신"""
        buffer = ctypes.create_string_buffer(buffer_size)
        received = self.lib.receive_data(socket_fd, buffer, buffer_size)

        if received > 0:
            return buffer.raw[:received]
        return None

    def close(self, socket_fd):
        """소켓 닫기"""
        return self.lib.close_socket(socket_fd)

    def get_error(self):
        """마지막 에러 메시지 가져오기"""
        error_msg = self.lib.get_last_error()
        if error_msg:
            try:
                return error_msg.decode('utf-8')
            except:
                return error_msg.decode('cp949', errors='ignore')
        return ""


class TCPServer:
    """사용하기 쉬운 TCP 서버 클래스"""

    def __init__(self, port, dll_path=None):
        """TCP 서버 생성"""
        self.socket_dll = SocketDLL(dll_path)
        self.port = port
        self.server_fd = -1

    def start(self):
        """서버 시작"""
        self.server_fd = self.socket_dll.create_server(self.port)
        if self.server_fd < 0:
            raise Exception(f"서버 시작 실패: {self.socket_dll.get_error()}")
        return self

    def accept(self):
        """클라이언트 연결 수락"""
        client_fd = self.socket_dll.accept_client(self.server_fd)
        if client_fd < 0:
            raise Exception(f"연결 수락 실패: {self.socket_dll.get_error()}")
        return TCPClient(client_fd, self.socket_dll)

    def close(self):
        """서버 닫기"""
        if self.server_fd >= 0:
            self.socket_dll.close_server(self.server_fd)
            self.server_fd = -1


class TCPClient:
    """사용하기 쉬운 TCP 클라이언트 클래스"""

    def __init__(self, socket_fd=None, socket_dll=None, host=None, port=None, dll_path=None):
        """TCP 클라이언트 생성"""
        if socket_dll:
            self.socket_dll = socket_dll
        else:
            self.socket_dll = SocketDLL(dll_path)

        self.socket_fd = socket_fd if socket_fd is not None else -1

        if host and port and self.socket_fd < 0:
            self.connect(host, port)

    def connect(self, host, port):
        """서버에 연결"""
        self.socket_fd = self.socket_dll.connect(host, port)
        if self.socket_fd < 0:
            raise Exception(f"연결 실패: {self.socket_dll.get_error()}")
        return self

    def send(self, data):
        """데이터 전송"""
        sent = self.socket_dll.send(self.socket_fd, data)
        if sent < 0:
            raise Exception(f"전송 실패: {self.socket_dll.get_error()}")
        return sent

    def receive(self, buffer_size=4096):
        """데이터 수신"""
        data = self.socket_dll.receive(self.socket_fd, buffer_size)
        if data is None:
            raise Exception(f"수신 실패: {self.socket_dll.get_error()}")
        return data

    def close(self):
        """연결 닫기"""
        if self.socket_fd >= 0:
            self.socket_dll.close(self.socket_fd)
            self.socket_fd = -1
