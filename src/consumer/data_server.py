"""Simple HTTP server to share data files with teammates."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os


class DataServerHandler(SimpleHTTPRequestHandler):
    """Serve files from data/raw directory."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="data/raw", **kwargs)


def run_server(port: int = 8000):
    """Start HTTP server to share data files.
    
    Args:
        port: Port number (default: 8000)
    
    Usage:
        Teammates access via: http://YOUR_IP:8000/
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, DataServerHandler)
    
    # Get local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"🌐 Data Server Running!")
    print(f"📁 Serving: data/raw/")
    print(f"🔗 Access URLs:")
    print(f"   Local:   http://localhost:{port}/")
    print(f"   Network: http://{local_ip}:{port}/")
    print(f"\n📋 Share this with teammates:")
    print(f"   http://{local_ip}:{port}/2025/11/10/events-2025-11-10.jsonl")
    print(f"\n⏹  Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Serve data files over HTTP")
    parser.add_argument('--port', type=int, default=8000, help='Port number (default: 8000)')
    args = parser.parse_args()
    run_server(port=args.port)
