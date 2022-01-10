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

from warnings import filterwarnings
filterwarnings(action='ignore', module='.*OpenSSL.*')

from datetime import datetime
from json import dumps
from twisted.conch.telnet import TelnetProtocol, TelnetTransport
from twisted.internet.protocol import Factory
from twisted.internet import reactor
from telnetlib import Telnet as TTelnet
from twisted.python import log as tlog
from subprocess import Popen
from os import path
from honeypots.helper import close_port_wrapper, get_free_port, kill_server_wrapper, server_arguments, setup_logger, disable_logger, set_local_vars, check_if_server_is_running
from uuid import uuid4


class QTelnetServer():
    def __init__(self, ip=None, port=None, username=None, password=None, mocking=False, config=''):
        self.auto_disabled = None
        self.mocking = mocking or ''
        self.random_servers = ['Ubuntu 18.04 LTS', 'Ubuntu 16.04.3 LTS', 'Welcome to Microsoft Telnet Server.']
        self.process = None
        self.uuid = 'telnet.log'
        self.ip = None
        self.port = None
        self.username = None
        self.password = None
        self.config = config
        if config:
            self.logs = setup_logger(self.uuid, config)
            set_local_vars(self, config)
        else:
            self.logs = setup_logger(self.uuid, None)
        self.ip = ip or self.ip or '0.0.0.0'
        self.port = port or self.port or 23
        self.username = username or self.username or 'test'
        self.password = password or self.password or 'test'
        disable_logger(1, tlog)

    def telent_server_main(self):
        _q_s = self

        class CustomTelnetProtocol(TelnetProtocol):
            _state = None
            _user = None
            _pass = None

            def check_bytes(self, string):
                if isinstance(string, bytes):
                    return string.decode()
                else:
                    return str(string)

            def connectionMade(self):
                self._state = None
                self._user = None
                self._pass = None
                self.transport.write(b'PC login: ')
                self._state = b'Username'
                _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'telnet', 'action': 'connection', 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port}))
            def dataReceived(self, data):
                data = data.strip()
                if self._state == b'Username':
                    self._user = data
                    self._state = b'Password'
                    self.transport.write(b'Password: ')
                elif self._state == b'Password':
                    username = self.check_bytes(self._user)
                    password = self.check_bytes(data)
                    status = 'failed'
                    # may need decode
                    if username == _q_s.username and password == _q_s.password:
                        username = _q_s.username
                        password = _q_s.password
                        status = 'success'
                    _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'telnet', 'action': 'login', 'status': status, 'src_ip': self.transport.getPeer().host, 'src_port': self.transport.getPeer().port, 'dest_port': _q_s.port, 'username': self._user, 'password': self._pass}))
                    self.transport.loseConnection()
                else:
                    self.transport.loseConnection()

            def connectionLost(self, reason):
                self._state = None
                self._user = None
                self._pass = None

        factory = Factory()
        factory.protocol = lambda: TelnetTransport(CustomTelnetProtocol)
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

            self.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'telnet', 'action': 'process', 'status': status, 'ip': self.ip, 'port': self.port, 'username': self.username, 'password': self.password}))

            if status == 'success':
                return True
            else:
                self.kill_server()
                return False
        else:
            self.telent_server_main()

    def test_server(self, ip=None, port=None, username=None, password=None):
        try:
            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            _username = _username.encode('utf-8')
            _password = _password.encode('utf-8')
            t = TTelnet(_ip, _port)
            t.read_until(b'login: ')
            t.write(_username + b'\n')
            t.read_until(b'Password: ')
            t.write(_password + b'\n')
        except Exception as e:
            print(e)
            pass

    def close_port(self):
        ret = close_port_wrapper('telnet_server', self.ip, self.port, self.logs)
        return ret

    def kill_server(self):
        ret = kill_server_wrapper('telnet_server', self.uuid, self.process)
        return ret


if __name__ == '__main__':
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qtelnetserver = QTelnetServer(ip=parsed.ip, port=parsed.port, username=parsed.username, password=parsed.password, mocking=parsed.mocking, config=parsed.config)
        qtelnetserver.run_server()
