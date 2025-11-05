# TLSleuth

TLSleuth scans hosts for weak TLS/SSL settings and common certificate issues (expiry, issuer, cipher strength), and produces JSON or a polished HTML report.

## Features

- Detects TLS protocol version negotiated (e.g., TLSv1.2, TLSv1.3)
- Extracts cipher suite and issuer information
- Checks certificate expiry against current UTC time
- Flags weak cipher suites (basic list included)
- Outputs: JSON (stdout) or pretty HTML report (`tlsleuth_report.html`)
- Verbose logging with rotating file logs in `./logs/`

## Installation

From PyPI (after publishing):

```bash
pip install tlsleuth
```

From source (editable/development mode):

```bash
pip install -e .
```

## Quick start

Scan a single host and open the HTML report:

```bash
tlsleuth --host example.com
```

JSON output instead of HTML:

```bash
tlsleuth --host example.com --json
```

Scan a list of hosts from a file:

```bash
tlsleuth --file hosts.txt
```

Enable verbose logging:

```bash
tlsleuth --host example.com --verbose
```

You can also run as a module:

```bash
python -m tlsleuth --host example.com
```

## CLI options

- `--host, -H` Single host to scan (e.g., example.com)
- `--file, -f` File containing hosts (one per line)
- `--timeout, -t` Connection timeout in seconds (default: 5)
- `--json, -j` Print JSON to stdout instead of generating HTML
- `--verbose, -v` Enable verbose logging

## HTML report

When not using `--json`, TLSleuth writes `tlsleuth_report.html` to the current directory. It includes:

- Summary (host count, scan date)
- Per-host table with TLS version, cipher, issuer, validity, and flags

## Logging

- Console logs are INFO by default, DEBUG with `--verbose`.
- File logs are written to `./logs/tlsleuth.log` with daily rotation.

## Development

Recommended local run:

```bash
python -m tlsleuth --host example.com
```

Project uses a `src/` layout and `setuptools` packaging. The package is `tlsleuth`.

## License

MIT © Rafael Fron

