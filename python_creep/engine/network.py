import socket
import json
import time
import threading

class NetworkServer:
    def __init__(self, game_engine, port=4242):
        self.engine = game_engine
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(('0.0.0.0', self.port))
        self.clients = [] # list of client sockets
        self.running = False

    def start(self):
        self.running = True
        self.server_sock.listen(5)
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()
        print(f"CreepNet TCP Server started on port {self.port}")

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, addr = self.server_sock.accept()
                print(f"Client connected: {addr}")
                self.clients.append(client_sock)
                threading.Thread(target=self._client_loop, args=(client_sock, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

    def _client_loop(self, client_sock, addr):
        f = client_sock.makefile('r')
        while self.running:
            try:
                line = f.readline()
                if not line:
                    break
                msg = json.loads(line)
                self._handle_message(msg, client_sock)
            except Exception as e:
                print(f"Client {addr} error: {e}")
                break
        
        print(f"Client disconnected: {addr}")
        if client_sock in self.clients:
            self.clients.remove(client_sock)
        client_sock.close()

    def _handle_message(self, msg, client_sock):
        msg_type = msg.get('type')
        if msg_type == 'INPUT':
            player_id = msg.get('player_id', 0)
            self.engine.handle_input(player_id, msg.get('commands', {}))

    def broadcast_state(self, state_dict):
        if not self.clients:
            return
            
        data = (json.dumps(state_dict) + "\n").encode()
        for client in list(self.clients):
            try:
                client.sendall(data)
            except:
                if client in self.clients:
                    self.clients.remove(client)
