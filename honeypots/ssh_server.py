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
filterwarnings(action='ignore', module='.*paramiko.*')

from paramiko import ServerInterface, Transport, RSAKey, AutoAddPolicy
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from _thread import start_new_thread
from io import StringIO
from random import choice
from time import sleep
from paramiko import SSHClient
from subprocess import Popen
from os import path
from honeypots.helper import close_port_wrapper, get_free_port, kill_server_wrapper, server_arguments, setup_logger, disable_logger, set_local_vars, check_if_server_is_running
from uuid import uuid4


class QSSHServer():
    def __init__(self, ip=None, port=None, username=None, password=None, mocking=False, config=''):
        self.auto_disabled = None
        self.mocking = mocking or ''
        self.random_servers = ['OpenSSH 7.5', 'OpenSSH 7.3', 'Serv-U SSH Server 15.1.1.108', 'OpenSSH 6.4']
        self.process = None
        self.uuid = 'ssh.log'
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
        self.port = port or self.port or 22
        self.username = username or self.username or 'test'
        self.password = password or self.password or 'test'

    def generate_pub_pri_keys(self):
        try:
            key = RSAKey.generate(2048)
            string_io = StringIO()
            key.write_private_key(string_io)
            return key.get_base64(), string_io.getvalue()
        except BaseException:
            pass
        return None, None

    def ssh_server_main(self):
        _q_s = self

        class SSHHandle(ServerInterface):

            def __init__(self, ip, port):
                self.ip = ip
                self.port = port
                ServerInterface.__init__(self)

            def check_bytes(self, string):
                if isinstance(string, bytes):
                    return string.decode()
                else:
                    return str(string)

            def check_auth_password(self, username, password):
                username = self.check_bytes(username)
                password = self.check_bytes(password)
                status = 'failed'
                if username == _q_s.username and password == _q_s.password:
                    username = _q_s.username
                    password = _q_s.password
                    status = 'success'
                _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'ssh_server', 'action': 'login', 'status': status, 'src_ip': self.ip, 'src_port': self.port, 'dest_port': _q_s.port, 'username': username, 'password': password}))

        def ConnectionHandle(client, priv):
            try:
                t = Transport(client)
                ip, port = client.getpeername()
                _q_s.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'ssh_server', 'action': 'connection', 'src_ip': ip, 'src_port': port, 'dest_port': _q_s.port}))
                t.local_version = 'SSH-2.0-' + choice(self.random_servers)
                t.add_server_key(RSAKey(file_obj=StringIO(priv)))
                t.start_server(server=SSHHandle(ip, port))
                chan = t.accept(1)
                if not chan is None:
                    chan.close()
            except BaseException:
                pass

        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((self.ip, self.port))
        sock.listen(1)
        pub, priv = self.generate_pub_pri_keys()
        while True:
            try:
                client, addr = sock.accept()
                start_new_thread(ConnectionHandle, (client, priv,))
            except BaseException:
                pass

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

            self.logs.info(dumps({'timestamp': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'), 'protocol': 'ssh_server', 'action': 'process', 'status': status, 'ip': self.ip, 'port': self.port, 'username': self.username, 'password': self.password}))

            if status == 'success':
                return True
            else:
                self.kill_server()
                return False
        else:
            self.ssh_server_main()

    def test_server(self, ip=None, port=None, username=None, password=None):
        try:
            sleep(2)
            _ip = ip or self.ip
            _port = port or self.port
            _username = username or self.username
            _password = password or self.password
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy())  # if you have default ones, remove them before using this..
            ssh.connect(_ip, port=_port, username=_username, password=_password, banner_timeout=200)
        except BaseException:
            pass

    def close_port(self):
        ret = close_port_wrapper('ssh_server', self.ip, self.port, self.logs)
        return ret

    def kill_server(self):
        ret = kill_server_wrapper('ssh_server', self.uuid, self.process)
        return ret


if __name__ == '__main__':
    parsed = server_arguments()
    if parsed.docker or parsed.aws or parsed.custom:
        qsshserver = QSSHServer(ip=parsed.ip, port=parsed.port, username=parsed.username, password=parsed.password, mocking=parsed.mocking, config=parsed.config)
        qsshserver.run_server()
