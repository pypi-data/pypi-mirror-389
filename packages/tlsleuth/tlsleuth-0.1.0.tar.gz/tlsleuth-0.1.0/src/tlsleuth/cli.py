#!/usr/bin/env python3
import argparse
import logging
import sys
from .utils import load_ascii
from .scanner import scan_host_list
from .logger_setup import setup_logging
from .output import print_in_json, print_in_html


def parse_args():
    parser = argparse.ArgumentParser(
        prog="TLSleuth",
        description="Scan hosts for weak TLS/SSL settings and certificate issues.",
    )
    parser.add_argument("--host", "-H", type=str, help="Single host to scan (ex: example.com)")
    parser.add_argument("--file", "-f", type=str, help="File with hosts, one per line")
    parser.add_argument("--timeout", "-t", type=int, default=5, help="Connection timeout in seconds")
    parser.add_argument("--json", "-j", action="store_true", help="Output results in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for debugging")
    return parser.parse_args()


def load_hosts(args, logger: logging.Logger):
    hosts = []
    if args.host:
        hosts.append(args.host.strip())
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as file:
                hosts.extend([line.strip() for line in file if line.strip()])
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
    if not hosts:
        logger.error("No hosts provided. Use --host or --file to specify targets.")
        sys.exit(1)
    return hosts


def main():
    logger = setup_logging()
    args = parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")

    logger.info("\n" + load_ascii())

    hosts = load_hosts(args, logger)
    logger.info(f"Loaded {len(hosts)} host(s) for scanning")

    logger.debug("[*] VERBOSE : Starting the scan...")
    scanResult = scan_host_list(hosts, timeout=args.timeout, verbose=args.verbose)

    logger.info("Scan completed. Processing results...")

    if args.json:
        print_in_json(scanResult)
    else:
        print_in_html(scanResult)
        logger.info("HTML report generated: tlsleuth_report.html")

    logger.debug("[*] VERBOSE : Scan completed")


if __name__ == "__main__":
    main()
