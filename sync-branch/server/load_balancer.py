import requests
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn, TCPServer
import logging
import threading
import time

# Configure logging
# Setup logging
LOG_FILE = "logs/load_balancer.log"

# Create a logger
logger = logging.getLogger("SyncBranchLogger")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.propagate = False

# List of backend Flask instances
def generate_backends(start_port, end_port):
    excluded_ports = {
        20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 123, 137, 138, 139, 143,
        161, 162, 179, 194, 389, 443, 445, 465, 514, 636, 989, 990, 993, 995,
        2049, 3306, 3389, 5040, 5432, 8080, 8443
    }  # Common protocol ports
    backends = [f"http://127.0.0.1:{port}" for port in range(start_port, end_port + 1) if port not in excluded_ports]
    return backends, len(backends)


BACKENDS, port_count = generate_backends(5001, 5050)

# Index to track the current backend (Round Robin)
current_backend_index = 0
EXCLUDED_BACKENDS = {}  # Backends to exclude from health checks
RETRY_INTERVAL = 30  # Time in seconds before retrying an excluded backend


HEALTHY_BACKENDS = []
HEALTH_CHECK_INTERVAL = 10  # Time in seconds for health checks
current_backend_index = 0

def health_check():
    """Periodically check the health of backend instances."""
    global HEALTHY_BACKENDS
    while True:
        healthy = []
        current_time = time.time()

        for backend in BACKENDS:
            # Check if the backend is excluded and not ready for retry
            if backend in EXCLUDED_BACKENDS and current_time < EXCLUDED_BACKENDS[backend]:
                logger.info(f"Skipping health check for {backend} (retry after {RETRY_INTERVAL} seconds)")
                continue

            try:
                response = requests.get(f"{backend}/healthcheck", timeout=50)
                if response.status_code == 200:
                    healthy.append(backend)
                    if backend in EXCLUDED_BACKENDS:
                        del EXCLUDED_BACKENDS[backend]  # Remove from excluded if now healthy
                else:
                    logger.warning(f"Health check failed for {backend} with status code {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"Health check failed for {backend}: {e}")
                EXCLUDED_BACKENDS[backend] = current_time + RETRY_INTERVAL  # Set next retry time

        HEALTHY_BACKENDS = healthy
        logger.info(f"Updated healthy backends: {len(HEALTHY_BACKENDS)}/{port_count}")
        time.sleep(HEALTH_CHECK_INTERVAL)

class LoadBalancerHandler(BaseHTTPRequestHandler):
    def forward_request(self, method):
        global current_backend_index
        for _ in range(len(HEALTHY_BACKENDS)):
            backend_url = HEALTHY_BACKENDS[current_backend_index]
            current_backend_index = (current_backend_index + 1) % len(HEALTHY_BACKENDS)

            target_url = backend_url + self.path
            headers = {key: value for key, value in self.headers.items()}
            try:
                if method == "GET":
                    response = requests.get(target_url, headers=headers, timeout=50)
                elif method == "POST":
                    content_length = int(self.headers.get("Content-Length", 0))
                    post_data = self.rfile.read(content_length)
                    response = requests.post(target_url, headers=headers, data=post_data, timeout=50)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                self.send_response(response.status_code)
                for header, value in response.headers.items():
                    self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.content)
                return

            except requests.RequestException as e:
                logger.warning(f"Backend {backend_url} failed: {e}")
                logger.warning(f"Failed request details: URL={target_url}, Headers={headers}")
                continue

        self.send_response(503)
        self.end_headers()
        self.wfile.write(b"Service Unavailable: All backends are unreachable")

    def do_GET(self):
        if not HEALTHY_BACKENDS:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"No healthy backends available")
        else:
            self.forward_request("GET")

    def do_POST(self):
        if not HEALTHY_BACKENDS:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"No healthy backends available")
        else:
            self.forward_request("POST")
            
            
class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    PORT = 8080
    threading.Thread(target=health_check, daemon=True).start()
    with ThreadedTCPServer(("", PORT), LoadBalancerHandler) as httpd:
        logger.info(f"Load balancer running on port {PORT}")
        httpd.serve_forever()
