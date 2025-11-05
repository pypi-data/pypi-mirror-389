from datetime import datetime
import json

def print_in_json(scanResult):
    """Print scan results in JSON format.
    
    Args:
        scanResult (list): List of scan result dictionaries.

    Returns:
        None
    """

    print(json.dumps(scanResult, indent=4))


def print_in_html(scanResult):
    html_report = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TLSleuth Security Report</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-height: 100vh; }
            .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); overflow: hidden; }
            .header { background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; padding: 40px; text-align: center; }
            .header h1 { font-size: 2.5em; margin-bottom: 10px; letter-spacing: 2px; }
            .header p { font-size: 1.1em; opacity: 0.9; }
            .content { padding: 40px; }
            .summary { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
            .summary-card { flex: 1; min-width: 200px; padding: 20px; border-radius: 8px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-left: 4px solid #667eea; }
            .summary-card h3 { font-size: 0.9em; color: #666; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
            .summary-card p { font-size: 2em; font-weight: bold; color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
            thead { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            th { padding: 15px; text-align: left; font-weight: 600; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; }
            td { padding: 15px; border-bottom: 1px solid #e0e0e0; }
            tbody tr { transition: background-color 0.3s ease; }
            tbody tr:hover { background-color: #f5f7fa; }
            tbody tr:nth-child(even) { background-color: #fafafa; }
            .status-badge { display: inline-block; padding: 5px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
            .status-true { background-color: #fee; color: #c33; }
            .status-false { background-color: #efe; color: #3c3; }
            .status-warning { background-color: #ffeaa7; color: #d63031; }
            .error-text { color: #e74c3c; font-style: italic; }
            .footer { text-align: center; padding: 20px; background: #f5f7fa; color: #666; font-size: 0.9em; }
            .tls-version { font-weight: 600; color: #667eea; }
            @media (max-width: 768px) { .header h1 { font-size: 1.8em; } .content { padding: 20px; } table { font-size: 0.9em; } th, td { padding: 10px 5px; } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>TLSleuth Security Report</h1><p>SSL/TLS Configuration Analysis</p></div>
            <div class="content">
                <div class="summary">
                    <div class="summary-card"><h3>Total Hosts</h3><p>""" + str(len(scanResult)) + """</p></div>
                    <div class="summary-card"><h3>Scan Date</h3><p style="font-size: 1.2em;">""" + str(datetime.now().strftime("%Y-%m-%d %H:%M")) + """</p></div>
                </div>
                <table>
                    <thead><tr><th>Host</th><th>TLS Version</th><th>Cipher</th><th>Issuer</th><th>Valid Until</th><th>Cert Expired</th><th>Weak Cipher</th><th>Error</th></tr></thead>
                    <tbody>
    """
    for result in scanResult:
        cert_expired = result.get('cert_expired')
        weak_cipher = result.get('weak_cipher')
        error = result.get('error')
        cert_status = f'<span class="status-badge status-true">Yes</span>' if cert_expired else f'<span class="status-badge status-false">No</span>' if cert_expired is not None else 'N/A'
        weak_status = f'<span class="status-badge status-warning">Yes</span>' if weak_cipher else f'<span class="status-badge status-false">No</span>'
        error_text = f'<span class="error-text">{error}</span>' if error else '-'
        html_report += f"""
                        <tr>
                            <td><strong>{result.get('host') or 'N/A'}</strong></td>
                            <td><span class="tls-version">{result.get('tls_version') or 'N/A'}</span></td>
                            <td>{result.get('cipher') or 'N/A'}</td>
                            <td style="font-size: 0.85em;">{result.get('issuer') or 'N/A'}</td>
                            <td>{result.get('valid_until') or 'N/A'}</td>
                            <td>{cert_status}</td>
                            <td>{weak_status}</td>
                            <td>{error_text}</td>
                        </tr>
        """
    html_report += """
                    </tbody>
                </table>
            </div>
            <div class="footer"><p>Generated by TLSleuth - SSL/TLS Security Scanner</p></div>
        </div>
    </body>
    </html>
    """
    with open("tlsleuth_report.html", "w", encoding="utf-8") as report_file:
        report_file.write(html_report)
    return html_report
