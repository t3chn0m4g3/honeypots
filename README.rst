.. image:: https://raw.githubusercontent.com/qeeqbox/honeypots/main/readme/honeypots.png

23 different honeypots in a single PyPI package for monitoring network traffic, bots activities, and username \ password credentials. All honeypots are non-blocking and can be used as objects or called directly with the in-built auto-configure scripts. Also, they are easy to setup and customize, it takes 1-2 seconds to spin a honeypot up. The output can be logged to a postgres database, file[s], terminal or syslog for easy integration.

This honeypots package is the only package that contains all the following: dns, ftp, httpproxy, http, https, imap, mysql, pop3, postgres, redis, smb, smtp, socks5, ssh, telnet, vnc, mssql, elastic, ldap, ntp, memcache, snmp, and oracle.

Honeypots now is in the awesome `telekom security T-Pot project! <https://github.com/telekom-security/tpotce>`_


Install
=======

.. code:: bash

    pip3 install honeypots

Usage Example - Auto configure
==============================
Use a honeypot, or multiple honeypots separated by comma or word all

.. code:: bash

    python3 -m honeypots --setup ssh

Usage Example - Local ports needs higher privileges (use sudo -E)
=================================================================
Use as honeypot:port or multiple honeypots as honeypot:port,honeypot:port

.. code:: bash

    python3 -m honeypots --setup ssh:22

Usage Example - Auto configure with specific ports
==================================================
Use as honeypot:port or multiple honeypots as honeypot:port,honeypot:port

.. code:: bash

    python3 -m honeypots --setup imap:143,mysql:3306,redis:6379

Usage Example - Auto configure with logs location
=================================================
Use a honeypot, or multiple honeypots separated by comma or word all

.. code:: bash

    python3 -m honeypots --setup ssh --config config.json

.. code:: json

    {
        "logs":"file,terminal",
        "logs_location":"/temp/honeypots_logs/"
    }

Usage Example - Custom configure
================================
Use a honeypot, or multiple honeypots separated by comma or word all

.. code:: bash

    python3 -m honeypots --setup ssh --config config.json

config.json (Output to folder and terminal)
===========================================

.. code:: json

    {
        "logs":"file,terminal",
        "logs_location":"/temp/honeypots_logs/"
        "honeypots": {
            "ftp": {
                "port": 21,
                "ip": "0.0.0.0",
                "username": "test",
                "password": "test"
                }
            }
    }

config.json (Output to syslog)
==============================

.. code:: json

    {
        "logs":"syslog",
        "logs_location":"",
        "syslog_address": "udp://localhost:514",
        "syslog_facility": 3,
        "honeypots": {
            "ftp": {
                "port": 21,
                "ip": "0.0.0.0",
                "username": "test",
                "password": "test"
                }
            }
    }

config.json (Output to db)
==========================

.. code:: json

    {
        "logs": "db",
        "logs_location": "",
        "syslog_address":"",
        "syslog_facility":0,
        "postgres":"//username:password@172.19.0.2:9999/honeypots",
        "db_options":["drop"],
        "filter": "",
        "interface": "",
        "honeypots": {
            "ftp": {
                "port": 21,
                "username": "test",
                "password": "test"
            }
        }
    }

db structure
============

.. code:: json

    [
      {
        "id": 1,
        "date": "2021-11-18 06:06:42.304338+00",
        "data": {
          "server": "'ftp_server'",
          "action": "'process'",
          "status": "'success'",
          "ip": "'0.0.0.0'",
          "port": "21",
          "username": "'test'",
          "password": "'test'"
        }
      }
    ]

Usage Example - Import as object and auto test
==============================================

.. code:: python

    #ip= String E.g. 0.0.0.0
    #port= Int E.g. 9999
    #username= String E.g. Test
    #password= String E.g. Test
    #mocking= Boolean or String E.g OpenSSH 7.0
    #logs= String E.g db, terminal or all
    #always remember to add process=true to run_server() for non-blocking

    from honeypots import QSSHServer
    qsshserver = QSSHServer(port=9999)
    qsshserver.run_server(process=True)
    qsshserver.test_server(port=9999)
    INFO:chameleonlogger:['servers', {'status': 'success', 'username': 'test', 'ip': '127.0.0.1', 'server': 'ssh_server', 'action': 'login', 'password': 'test', 'port': 38696}]
    qsshserver.kill_server()

Usage Example - Import as object and test with external ssh command
===================================================================

.. code:: python

    from honeypots import QSSHServer
    qsshserver = QSSHServer(port=9999)
    qsshserver.run_server(process=True)

.. code:: bash

    ssh test@127.0.0.1

Honeypot answer

.. code:: python

    INFO:chameleonlogger:['servers', {'status': 'success', 'username': 'test', 'ip': '127.0.0.1', 'server': 'ssh_server', 'action': 'login', 'password': 'test', 'port': 38696}]

Close the honeypot

.. code:: python

    qsshserver.kill_server()

Current Servers/Emulators
=========================
- QDNSServer
    - Server: DNS 
    - Port: 53
    - Lib: Twisted
    - Logs: ip, port
- QFTPServer
    - Server: FTP 
    - Port: 21
    - Lib: Twisted
    - Logs: ip, port, username and password
- QHTTPProxyServer
    - Server: HTTP Proxy
    - Port: 8080
    - Lib: Twisted
    - Logs: ip, port and data
- QHTTPServer
    - Server: HTTP
    - Port: 80
    - Lib: Twisted
    - Logs: ip, port, username and password
- QHTTPSServer
    - Server: HTTPS
    - Port: 443
    - Lib: Twisted
    - Logs: ip, port, username and password
- QIMAPServer
    - Server: IMAP
    - Port: 143
    - Lib: Twisted
    - Logs: ip, port, username and password
- QMysqlServer
    - Emulator: Mysql
    - Port: 3306
    - Lib: Twisted
    - Logs: ip, port, username and password
- QPOP3Server
    - Server: POP3
    - Port: 110
    - Lib: Twisted
    - Logs: ip, port, username and password
- QPostgresServer
    - Emulator: Postgres
    - Port: 5432
    - Lib: Twisted
    - Logs: ip, port, username and password
- QRedisServer
    - Emulator: Redis
    - Port: 6379
    - Lib: Twisted
    - Logs: ip, port, username and password
- QSMBServer
    - Server: Redis
    - Port: 445
    - Lib: impacket
    - Logs: ip, port and username
- QSMTPServer
    - Server: SMTP
    - Port: 25
    - Lib: smtpd
    - Logs: ip, port, username and password
- QSOCKS5Server
    - Server: SOCK5
    - Port: 1080
    - Lib: socketserver
    - Logs: ip, port, username and password
- QSSHServer
    - Server: SSH
    - Port: 22
    - Lib: paramiko
    - Logs: ip, port, username and password
- QTelnetServer
    - Server: Telnet
    - Port: 23
    - Lib: Twisted
    - Logs: ip, port, username and password
- QVNCServer
    - Emulator: VNC
    - Port: 5900
    - Lib: Twisted
    - Logs: ip, port, username and password
- QMSSQLServer
    - Emulator: MSSQL
    - Port: 1433
    - Lib: Twisted
    - Logs: ip, port, username and password or hash
- QElasticServer
    - Emulator: Elastic
    - Port: 9200
    - Lib: http.server
    - Logs: ip, port and data
- QLDAPServer
    - Emulator: LDAP
    - Port: 389
    - Lib: Twisted
    - Logs: ip, port, username and password
- QNTPServer
    - Emulator: NTP
    - Port: 123
    - Lib: Twisted
    - Logs: ip, port and data
- QMemcacheServer
    - Emulator: Memcache
    - Port: 11211
    - Lib: Twisted
    - Logs: ip, port and data
- QOracleServer
    - Emulator: Oracle
    - Port: 1521
    - Lib: Twisted
    - Logs: ip, port and connet data
- QSNMPServer
    - Emulator: SNMP
    - Port: 161
    - Lib: Twisted
    - Logs: ip, port and data

acknowledgement
===============
- By using this framework, you are accepting the license terms of all these packages: `pipenv twisted psutil psycopg2-binary dnspython requests impacket paramiko redis mysql-connector pycryptodome vncdotool service_identity requests[socks] pygments http.server`
- Let me know if I missed a reference or resource!

Some Articles
=============
- `securityonline <https://securityonline.info/honeypots-16-honeypots-in-a-single-pypi-package/>`_

Notes
=====
- Almost all servers and emulators are stripped-down - You can adjust that as needed

Other projects
==============
.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//social-analyzer.png
    :target: https://github.com/qeeqbox/social-analyzer

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//analyzer.png
    :target: https://github.com/qeeqbox/analyzer

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//chameleon.png
    :target: https://github.com/qeeqbox/chameleon

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//osint.png
    :target: https://github.com/qeeqbox/osint

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//url-sandbox.png
    :target: https://github.com/qeeqbox/url-sandbox

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//mitre-visualizer.png
    :target: https://github.com/qeeqbox/mitre-visualizer

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//woodpecker.png
    :target: https://github.com/qeeqbox/woodpecker

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//docker-images.png
    :target: https://github.com/qeeqbox/docker-images

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//seahorse.png
    :target: https://github.com/qeeqbox/seahorse

.. image:: https://raw.githubusercontent.com/qeeqbox/.github/main/data//rhino.png
    :target: https://github.com/qeeqbox/rhino
