import socket
import base64

class C2Server:
    def __init__(self, listen_host, listen_port):
        self.listen_host = listen_host
        self.listen_port = listen_port

    def start(self):
        """Starts the C2 server."""
        print(f"Starting C2 server on {self.listen_host}:{self.listen_port}")
        # This is a simplified C2 server for demonstration purposes.
        # A real C2 server would be more complex and robust.
        # This server does not actually handle DNS queries, but simulates it.
        
        # In a real scenario, you would use a library like Scapy or dnslib
        # to parse incoming DNS queries.
        
        # For this simulation, we'll just listen on a UDP port.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((self.listen_host, self.listen_port))
            while True:
                data, addr = s.recvfrom(1024)
                try:
                    # Attempt to decode the received data
                    encoded_data = data.decode().split('.')[0]
                    decoded_data = base64.b64decode(encoded_data).decode()
                    print(f"Received data from {addr}: {decoded_data}")
                except Exception as e:
                    print(f"Received non-base64 data from {addr}: {data.decode()}")

if __name__ == "__main__":
    listen_host = "0.0.0.0"
    listen_port = 53 # DNS port

    c2_server = C2Server(listen_host, listen_port)
    c2_server.start()
