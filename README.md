# Ants: A Parallel Downloader

## Installation

Requires Python 3.13 so far because of `queue.ShutDown`.

### Using `pip`

```sh
pipx install git+https://github.com/Microwave-WYB/ants.git
```

### Using `uv`

```sh
uv tool install git+https://github.com/Microwave-WYB/ants.git
```

## Usage

```
usage: ants [-h] [-n WORKERS] [-o OUTPUT] url

Download files from a URL

positional arguments:
  url                   URL to download

options:
  -h, --help            show this help message and exit
  -n, --workers WORKERS
                        Number of workers
  -o, --output OUTPUT   Output file
```

Example:

```sh
ants -n 4 -o test.txt https://example.com/test.txt
```
