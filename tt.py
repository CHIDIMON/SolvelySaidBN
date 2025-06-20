import ssl
import socket

hostname = "ac-wmwxpav-shard-00-00.c6sojky.mongodb.net"
port = 27017

context = ssl.create_default_context()
with socket.create_connection((hostname, port), timeout=10) as sock:
    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
        print("SSL established. Peer:", ssock.getpeercert())
