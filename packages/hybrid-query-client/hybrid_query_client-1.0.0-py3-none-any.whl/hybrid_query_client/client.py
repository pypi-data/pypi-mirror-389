import socket
import json

HOST = '127.0.0.1'
PORT = 9000

def send_query(query, host=HOST, port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(query.encode())
        data = s.recv(65536)

        try:
            return json.loads(data.decode())
        except json.JSONDecodeError:
            return {"error": "Failed to parse response"}
