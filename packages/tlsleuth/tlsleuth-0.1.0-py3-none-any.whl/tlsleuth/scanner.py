import ssl
import socket
import datetime
import logging

logger = logging.getLogger(__name__)


def scan_hosts(host, timeout=5, verbose=False):
    """
    Function to scan hosts SSL version and protocols.
    """
    logger.info(f"Starting scan for host: {host}")

    result = {
        "host": host,
        "tls_version": None,
        "cert_expired": None,
        "issuer": None,
        "valid_until": None,
        "cipher": None,
        "weak_cipher": False,
        "error": None,
    }
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
                result["tls_version"] = version
                result["cipher"] = cipher[0]

                issuer = cert.get("issuer")
                isValid = cert.get("notAfter")

                if isValid:
                    expire_date = datetime.datetime.strptime(isValid, "%b %d %H:%M:%S %Y %Z")
                    if expire_date.tzinfo is None:
                        expire_date = expire_date.replace(tzinfo=datetime.timezone.utc)
                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                    result["valid_until"] = expire_date.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
                    result["cert_expired"] = expire_date < now_utc

                if issuer:
                    issuer_str = " ".join(f"{name}={value}" for rdn in issuer for name, value in rdn)
                    result["issuer"] = issuer_str

                if verbose:
                    logger.info(f"Scanned host: {host}")
                    logger.info(f"TLS Version: {version}")
                    logger.info(f"Cipher: {cipher[0]}")
                    logger.info(f"Issuer: {result['issuer']}")
                    logger.info(f"Valid Until: {result['valid_until']}")
                    logger.info(f"Certificate Expired: {result['cert_expired']}")
                    logger.info(f"Weak Cipher: {result['weak_cipher']}")

                if result["cipher"] in ["RC4-SHA", "DES-CBC3-SHA", "AES128-SHA", "AES256-SHA"]:
                    result["weak_cipher"] = True
                    logger.warning(f"Weak cipher detected for host {host}: {cipher[0]}")

    except socket.timeout:
        logger.error(f"Connection timeout - Host {host} is not reachable (timeout after {timeout}s)")
        result["error"] = "Connection timeout"

    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for host {host}: {e}")
        result["error"] = f"DNS error: {e}"

    except ConnectionRefusedError:
        logger.error(f"Connection refused by host {host} on port 443")
        result["error"] = "Connection refused"

    except ssl.SSLError as e:
        logger.error(f"SSL/TLS error for host {host}: {e}")
        result["error"] = f"SSL error: {e}"

    except Exception as e:
        logger.error(f"Unexpected error scanning host {host}: {type(e).__name__} - {e}")
        result["error"] = str(e)

    logger.info(f"Completed scan for host: {host}")
    return result


def scan_host_list(hosts, timeout=5, verbose=False):
    results = []
    for host in hosts:
        res = scan_hosts(host, timeout, verbose)
        results.append(res)
    return results
