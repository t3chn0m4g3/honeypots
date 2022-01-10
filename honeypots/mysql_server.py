'''
//  -------------------------------------------------------------
//  author        Giga
//  project       qeeqbox/honeypots
//  email         gigaqeeq@gmail.com
//  description   app.py (CLI)
//  licensee      AGPL-3.0
//  -------------------------------------------------------------
//  contributors list qeeqbox/honeypots/graphs/contributors
//  -------------------------------------------------------------
'''

from datetime import datetime
from json import dumps
from warnings import filterwarnings
filterwarnings(action='ignore', module='.*OpenSSL.*')

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.python import log as tlog
from struct import pack
from hashlib import sha1
from mysql.connector import connect as mysqlconnect
from subprocess import Popen
from os import path
from honeypots.helper import close_port_wrapper, get_free_port, kill_server_wrapper, server_arguments, setup_logger, disable_logger, set_local_vars, check_if_server_is_running
from uuid import uuid4


class QMysqlServer():
    def __init__(self, ip=None, port=None, username=None, password=None, mocking=False, dict_=None, config=''):
        self.auto_disabled = None
        self.mocking = mocking or ''
        self.file_name = dict_ or None
        self.process = None
        self.uuid = 'mysql.log'
        self.config = config
        self.ip = None
        self.port = None
        self.username = None
        self.password = None
        if config:
            self.logs = setup_logger(self.uuid, config)
            set_local_vars(self, config)
        else:
            self.logs = setup_logger(self.uuid, None)
        self.ip = ip or self.ip or '0.0.0.0'
        self.port = port or self.port or 3306
        self.username = username or self.username or 'test'
        self.password = password or self.password or 'test'

        if not dict_:
            self.words = [self.password.encode()]
        else:
            self.load_words()

        disable_logger(1, tlog)

    def load_words(self,):
        with open(self.file_name, 'r', encoding='utf-8') as file:
            self.words = file.read().splitlines()

    def greeting(self):
        base = ['\x0a', '5.7.00' + '\0', '\x36\x00\x00\x00', '12345678' + '\0', '\xff\xf7', '\x21', '\x02\x00', '\x0f\x81', '\x15', '\0' * 10, '123456789012' + '\0', 'mysql_native_password' + '\0']
        payload_len = list(pack('<I', len(''.join(base))))
        #payload_len[3] = '\x00'
        string_ = chr(payload_len[0]) + chr(payload_len[1]) + chr(payload_len[2]) + '\x00' + ''.join(base)
        string_ = bytes([ord(c) for c in string_])
        return string_

    def too_many(self):
        base = ['\xff', '\x10\x04', '#08004', 'Too many connections']
        payload_len = list(pack('<I', len(''.join(base))))
        #payload_len[3] = '\x02'
        string_ = chr(payload_len[0]) + chr(payload_len[1]) + chr(payload_len[2]) + '\x02' + ''.join(base)
        string_ = bytes([ord(c) for c in string_])
        return string_

    def access_denied(self):
        base = ['\xff', '\x15\x04', '#28000', 'Access denied..']
        payload_len = list(pack('<I', len(''.join(base))))
        #payload_len[3] = '\x02'
        string_ = chr(payload_len[0]) + chr(payload_len[1]) + chr(payload_len[2]) + '\x02' + ''.join(base)
        string_ = bytes([ord(c) for c in string_])
        return string_

    def parse_data(self, data):
        username, password = '', ''
        try:
            username_len = data[36:].find(b'\x00')
            username = data[36:].split(b'\x00')[0]
            password_len = data[36 + username_len + 1]
            password = data[36 + username_len + 2:36 + username_len + 2 + password_len]
            rest_ = data[36 + username_len + 2 + password_len:]
            if len(password) == 20:
                return username, password, True
        except BaseException:
            pass
        return username, password, False

    def decode(self, hash):
        try:
            for word in self.words:
                temp = word
                word = word.strip(b'\n')
                hash1 = sha1(word).digest()
                hash2 = sha1(hash1).digest()
                encrypted = [((a) ^ (b)) for a, b in zip(hash1, sha1(b'12345678123456789012' + hash2).digest())]
                if encrypted == list([(i) for i in hash]):
                    return temp
        except BaseException:
            pass

        return None

    def mysql_server_main(self):
        _q_s = self

        class CustomMysqlProtocol(Protocol):

            _state = None

            def check_bytes(self, string):
                try:
                    if isinstance(string, bytes):
                        return string.decode('utf-8', 'ignore')
                    else:
                        return str(string)
                except Exception as e:
                    return string

            def connectionMade(self):
                self._state = 1
                self.transport.write(_q_s.greeting())
                _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'mysql', 'action': 'connection', 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port}))

            def dataReceived(self, data):
                try:
                    if self._state == 1:
                        ret_access_denied = False
                        username, password, good = _q_s.parse_data(data)
                        username = self.check_bytes(username)
                        status = 'failed'
                        if good:
                            if password:
                                password_decoded = _q_s.decode(password)
                                if password_decoded is not None and username == _q_s.username:
                                    password = self.check_bytes(password_decoded)
                                    status = 'success'
                                else:
                                    password = password.hex()
                                    ret_access_denied = True
                            else:
                                ret_access_denied = True
                                password = ':'.join(hex((c))[2:] for c in data)
                        _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'mysql', 'action': 'login', 'status': status, 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port, 'username': 'UnKnown', 'password': password}))

                        if ret_access_denied:
                            self.transport.write(_q_s.access_denied())
                        else:
                            self.transport.write(_q_s.too_many())
                    else:
                        self.transport.loseConnection()
                except BaseException as e:
                    self.transport.write(_q_s.too_many())
                    self.transport.loseConnection()

            def connectionLost(self, reason):
                self._state = None

        factory = Factory()
        factory.protocol = CustomMysqlProtocol
        reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        reactor.run()

    def run_server(self, process=False, auto=False):
        status = 'error'
        run = False
        if process:
            if auto and not self.auto_disabled:
                port = get_free_port()
                if port > 0:
                    self.port = port
                    run = True
            elif self.close_port() and self.kill_server():
                run = True

            if run:
                self.process = Popen(['python3', path.realpath(__file__), '--custom', '--ip', str(self.ip), '--port', str(self.port), '--username', str(self.username), '--password', str(self.password), '--mocking', str(self.mocking), '--config', str(self.config), '--uuid', str(self.uuid)])
                if self.process.poll() is None and check_if_server_is_running(self.uuid):
                    status = 'success'

            self.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'mysql', 'action': 'process', 'status': status, 'ip': self.ip, 'port': self.port, 'username': self.username, 'password': self.password}))

            if status == 'success':
                return True
            else:
                self.kill_server()
                return False
        else:
            self.mysql_server_main()

    def test_server(self, ip=None, port=None, username=None, password=None):
        try:
            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            cnx = mysqlconnect(user=_username, password=_password, host=_ip, port=_port, database='test', connect_timeout=1000)
        except Exception as e:
            pass

    def close_port(self):
        ret = close_port_wrapper('mysql_server', self.ip, self.port, self.logs)
        return ret

    def kill_server(self):
        ret = kill_server_wrapper('mysql_server', self.uuid, self.process)
        return ret


if __name__ == '__main__':
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qmysqlserver = QMysqlServer(ip=parsed.ip, port=parsed.port, username=parsed.username, password=parsed.password, mocking=parsed.mocking, config=parsed.config)
        qmysqlserver.run_server()
