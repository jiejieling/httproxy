# ZZ Proxy Suite

ZZ Proxy Suite is a collection of lightweight and asynchronous proxy servers, including an HTTP proxy and a SOCKS5 proxy. It's built with Python's `asyncio` library for high performance and concurrency.

## Features

- **HTTP Proxy (`httproxy.py`)**:
  - Supports `HTTP` and `HTTPS` (via `CONNECT` method).
  - Lightweight and fast.
  - Can be run as a background daemon process.

- **SOCKS5 Proxy (`socks5.py`)**:
  - Supports SOCKS5 protocol.
  - Implements `CONNECT` command.
  - Supports both "No Authentication" and "Username/Password" authentication methods.
  - Can be run as a background daemon process.

- **Common Features**:
  - Asynchronous I/O for handling many connections concurrently.
  - Detailed logging.
  - Simple command-line interface.

## Installation

1.  Clone the repository:
    ```bash
    git clone <your-repo-url>
    cd httproxy
    ```

2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Both proxy scripts share a similar command-line interface.

### HTTP Proxy (`httproxy.py`)

To start the HTTP proxy server in the foreground:

```bash
python3 httproxy.py -H 127.0.0.1 -P 8000 -v
```

**Command-line options:**

| Flag        | Long Flag     | Description                                     | Default     |
|-------------|---------------|-------------------------------------------------|-------------|
| `-H`        | `--host`      | Host to bind to.                                | `127.0.0.1` |
| `-P`        | `--port`      | Port to bind to.                                | `8000`      |
| `-l`        | `--logfile`   | Path to the logfile.                            | `STDOUT`    |
| `-p`        | `--pidfile`   | Path to the pidfile.                            | `/tmp/zzhttproxy.pid` |
| `-d`        | `--daemon`    | Run as a daemon (requires a specified logfile). | `False`     |
| `-v`        | `--verbose`   | Enable debug logging.                           | `False`     |

### SOCKS5 Proxy (`socks5.py`)

To start the SOCKS5 proxy server without authentication:

```bash
python3 socks5.py -H 127.0.0.1 -P 1080 -v
```

To start with username/password authentication:

```bash
python3 socks5.py -H 127.0.0.1 -P 1080 --user myuser --password mypassword -v
```

**Command-line options:**

| Flag        | Long Flag     | Description                                     | Default     |
|-------------|---------------|-------------------------------------------------|-------------|
| `-H`        | `--host`      | Host to bind to.                                | `127.0.0.1` |
| `-P`        | `--port`      | Port to bind to.                                | `1080`      |
| `-u`        | `--user`      | Username for authentication.                    | `None`      |
| `-p`        | `--password`  | Password for authentication.                    | `None`      |
| `-l`        | `--logfile`   | Path to the logfile.                            | `STDOUT`    |
|             | `--pidfile`   | Path to the pidfile.                            | `/tmp/zzsocks5proxy.pid` |
| `-d`        | `--daemon`    | Run as a daemon (requires a specified logfile). | `False`     |
| `-v`        | `--verbose`   | Enable debug logging.                           | `False`     |

### Running in the Background (Daemon Mode)

To run either proxy in the background, use the `-d` or `--daemon` flag and specify a log file with `-l`.

**Example for HTTP Proxy:**

```bash
python3 httproxy.py -d -l /var/log/httproxy.log
```

**Example for SOCKS5 Proxy:**

```bash
python3 socks5.py -d --user myuser --password mypass -l /var/log/socks5.log
```

The process ID (PID) will be stored in a file (e.g., `/tmp/zzhttproxy.pid`), which you can use to stop the daemon.
```bash
kill $(cat /tmp/zzhttproxy.pid)
```
