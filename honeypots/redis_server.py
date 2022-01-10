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
from redis import StrictRedis
from twisted.python import log as tlog
from subprocess import Popen
from os import path
from honeypots.helper import close_port_wrapper, get_free_port, kill_server_wrapper, server_arguments, setup_logger, disable_logger, set_local_vars, check_if_server_is_running, set_local_vars
from uuid import uuid4


class QRedisServer():
    def __init__(self, ip=None, port=None, username=None, password=None, mocking=False, config=''):
        self.auto_disabled = None
        self.mocking = mocking or ''
        self.process = None
        self.uuid = 'redis.log'
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
        self.port = port or self.port or 6379
        self.username = username or self.username or 'test'
        self.password = password or self.password or 'test'
        disable_logger(1, tlog)

    def redis_server_main(self):
        _q_s = self

        class CustomRedisProtocol(Protocol):

            def check_bytes(self, string):
                if isinstance(string, bytes):
                    return string.decode()
                else:
                    return str(string)

            def get_command(self, data):
                try:
                    _data = data.decode('utf-8').split('\x0d\x0a')
                    if _data[0][0] == '*':
                        _count = int(_data[0][1]) - 1
                        _data.pop(0)
                        if _data[0::2][0][0] == '$' and len(_data[1::2][0]) == int(_data[0::2][0][1]):
                            return _count, _data[1::2][0]
                except Exception as e:
                    print(e)

                return 0, ''

            def parse_data(self, c, data):
                _data = data.decode('utf-8').split('\r\n')[3::]
                username, password = '', ''
                if c == 2:
                    _ = 0
                    if _data[0::2][_][0] == '$' and len(_data[1::2][_]) == int(_data[0::2][_][1]):
                        username = (_data[1::2][_])
                    _ = 1
                    if _data[0::2][_][0] == '$' and len(_data[1::2][_]) == int(_data[0::2][_][1]):
                        password = (_data[1::2][_])
                if c == 1:
                    _ = 0
                    if _data[0::2][_][0] == '$' and len(_data[1::2][_]) == int(_data[0::2][_][1]):
                        password = (_data[1::2][_])
                if c == 2 or c == 1:
                    username = self.check_bytes(username)
                    password = self.check_bytes(password)
                    status = 'failed'
                    if username == _q_s.username and password == _q_s.password:
                        username = _q_s.username
                        password = _q_s.password
                        status = 'success'
                    _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'redis', 'action': 'login', 'status': status, 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port, 'username': user, 'password': password}))

            def connectionMade(self):
                self._state = 1
                self._variables = {}
                _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'redis', 'action': 'connection', 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port}))

            def dataReceived(self, data):
                c, command = self.get_command(data)
                if command == 'AUTH':
                    self.parse_data(c, data)
                    self.transport.write(b'-ERR invalid password\r\n')
                else:
                    self.transport.write(b'-ERR unknown command "{}"\r\n'.format(command))
                self.transport.loseConnection()

        factory = Factory()
        factory.protocol = CustomRedisProtocol
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

            self.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'redis', 'action': 'process', 'status': status, 'ip': self.ip, 'port': self.port, 'username': self.username, 'password': self.password}))

            if status == 'success':
                return True
            else:
                self.kill_server()
                return False
        else:
            self.redis_server_main()

    def test_server(self, ip=None, port=None, username=None, password=None):
        try:
            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            r = StrictRedis.from_url('redis://{}:{}@{}:{}/1'.format(_username, _password, _ip, _port))
            for key in r.scan_iter('user:*'):
                pass
        except BaseException:
            pass

    def close_port(self):
        ret = close_port_wrapper('redis_server', self.ip, self.port, self.logs)
        return ret

    def kill_server(self):
        ret = kill_server_wrapper('redis_server', self.uuid, self.process)
        return ret


if __name__ == '__main__':
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qredisserver = QRedisServer(ip=parsed.ip, port=parsed.port, username=parsed.username, password=parsed.password, mocking=parsed.mocking, config=parsed.config)
        qredisserver.run_server()
