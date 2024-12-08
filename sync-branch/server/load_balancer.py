import http.server
import socketserver
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of backend Flask instances
BACKENDS = [
    "http://127.0.0.1:5001",
    "http://127.0.0.1:5002",
    "http://127.0.0.1:5003",
    "http://127.0.0.1:5004",
    "http://127.0.0.1:5005",
    "http://127.0.0.1:5006",
    "http://127.0.0.1:5007",
    "http://127.0.0.1:5008",
    "http://127.0.0.1:5009",
    "http://127.0.0.1:5010",
    "http://127.0.0.1:5011",
    "http://127.0.0.1:5012",
    "http://127.0.0.1:5013",
    "http://127.0.0.1:5014",
    "http://127.0.0.1:5015",
    "http://127.0.0.1:5016"
]

# Index to track the current backend (Round Robin)
current_backend_index = 0


class LoadBalancerHandler(http.server.BaseHTTPRequestHandler):
    def forward_request(self, method):
        """Forward the request to a backend instance."""
        global current_backend_index
        for attempt in range(len(BACKENDS)):
            backend_url = BACKENDS[current_backend_index]
            current_backend_index = (current_backend_index + 1) % len(BACKENDS)
            
            # Construct the target URL
            target_url = backend_url + self.path
            headers = {key: value for key, value in self.headers.items()}
            
            try:
                if method == "GET":
                    response = requests.get(target_url, headers=headers, timeout=10)
                elif method == "POST":
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    response = requests.post(target_url, headers=headers, data=post_data, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # If the response is successful, forward it to the client
                self.send_response(response.status_code)
                for header, value in response.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.content)
                return

            except requests.exceptions.RequestException as e:
                logger.warning(f"Backend {backend_url} failed: {e}")
                continue  # Try the next backend

        # If all backends fail, return a 503 Service Unavailable
        self.send_response(503)
        self.end_headers()
        self.wfile.write(b"Service Unavailable: All backends are unreachable")

    def do_GET(self):
        """Handle GET requests."""
        self.forward_request("GET")

    def do_POST(self):
        """Handle POST requests."""
        self.forward_request("POST")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """A threaded TCP server to handle concurrent requests."""
    allow_reuse_address = True


if __name__ == "__main__":
    PORT = 8080
    with ThreadedTCPServer(("", PORT), LoadBalancerHandler) as httpd:
        logger.info(f"Load balancer running on port {PORT}")
        httpd.serve_forever()
