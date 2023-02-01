httproxy
========

This module implements a tiny threaded HTTP proxy by extending
``HTTPServer``.  Supports the ``GET``, ``HEAD``, ``POST``, ``PUT``,
``DELETE`` and ``CONNECT`` methods.


Quickstart
----------

Usage::

  httproxy [options]

Options::

  -h, --help                   Show this screen.
  --version                    Show version and exit.
  -H, --host HOST              Host to bind to [default: 127.0.0.1].
  -p, --port PORT              Port to bind to [default: 8000].
  -l, --logfile PATH           Path to the logfile [default: STDOUT].
  -i, --pidfile PIDFILE        Path to the pidfile [default: httproxy.pid].
  -d, --daemon                 Daemonize (run in the background). The
                               default logfile path is httproxy.log in
                               this case.
  -v, --verbose                Log headers.

To start the proxy server and bind it to port 22222 (the port on which it will
listen and accept connections)::

    httproxy -p 22222

To start the proxy server, bind it to port 22222 and tell it to log all requests
to the file ``httproxy.log``::

    httproxy -p 22222 -l httproxy.log

To start the proxy server so it only allows connections from IP
``123.123.123.123``::

    httproxy 123.123.123.123

To start the proxy server bound to port 22222, log to file ``httproxy.log`` and run
the server in the background (as a daemon)::

    httproxy -p 22222 -l httproxy.log -d

Change Log
----------
1.2
~~~~~

* Change I/O model by selectors module

1.1
~~~~~

* Change I/O model to epoll

1.0
~~~~~

* Make compatibility with Python 3

0.9.1
~~~~~

* fixed `issue #2 <https://github.com/ambv/httproxy/pull/2>`_: ``KeyError`` if
  there's no ``[main]`` section in ``~/.httproxy/config``. Thanks to Rune
  Hansen for the report and initial patch.

* fixed hang on shutdown due to blocking ``handle_request()``

* fixed installability on PyPy

* removed the unholy frame-walking signal handling

* updated the test suite so it works with new virtualenvs

0.9.0
~~~~~

* ability to read configuration from a file (``--configfile``)

* ability to specify the address the proxy will bind to (``--host``)

* ability to log headers sent and received (``--verbose``)

* better process management: pidfile support, a more descriptive process title
  (with the optional ``setproctitle`` dependency)

* fixed spurious ``[Errno 54] Connection reset by peer`` tracebacks

* properly shuts down when receiving ``SIGHUP``, ``SIGINT`` or ``SIGTERM``

* major code refactoring

* compatible with Python 2.6 and 2.7 only: requires ``docopt`` and ``configparser``

0.3.1
~~~~~

* added rudimentary FTP file retrieval

* added custom logging methods

* added code to make it run as a standalone application

Upgraded by `Mitko Haralanov
<http://www.voidtrance.net/2010/01/simple-python-http-proxy/>`_ in 2009.

0.2.1
~~~~~

* basic version hosted in 2006 by the original author at
  http://www.oki-osk.jp/esc/python/proxy/

Authors
-------

Script based on work by Suzuki Hisao and Mitko Haralanov, currently maintained
by `Łukasz Langa <mailto:lukasz@langa.pl>`_.
