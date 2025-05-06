import os
import socket
import time
from packet import Packet

class UDPServer:
    def __init__(self, port, max_payload=1465, delay=0.00):
        self.server_ip = "0.0.0.0"
        self.port = port
        self.max_payload = max_payload
        self.delay = delay
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.server_ip, self.port))
        print(f"Servidor UDP iniciado em {self.server_ip}:{self.port}")

    def send_error(self, client_address, message):
        error_packet = Packet(0, 2, message.encode())
        self.socket.sendto(error_packet.to_bytes(), client_address)
        print(f"[ERRO] Enviado para {client_address}: {message}")

    def send_file(self, client_address, file_path):
        if not os.path.exists(file_path):
            self.send_error(client_address, "Arquivo nao encontrado")
            return

        with open(file_path, 'rb') as file:
            seq = 0
            while chunk := file.read(self.max_payload):
                data_packet = Packet(seq, 1, chunk)
                self.socket.sendto(data_packet.to_bytes(), client_address)
                print(f"[ENVIO] Pacote {seq} enviado para {client_address} ({len(chunk)} bytes)")
                seq += 1
                time.sleep(self.delay)

    def retransmit_missing(self, client_address, file_path, missing_seqs):
        if not os.path.exists(file_path):
            self.send_error(client_address, "Arquivo nao encontrado")
            return

        with open(file_path, 'rb') as file:
            for seq in missing_seqs:
                file.seek(seq * self.max_payload)
                chunk = file.read(self.max_payload)
                if chunk:
                    data_packet = Packet(seq, 1, chunk)
                    self.socket.sendto(data_packet.to_bytes(), client_address)
                    print(f"[RETRANSMISSÃO] Pacote {seq} retransmitido para {client_address} ({len(chunk)} bytes)")
                    time.sleep(self.delay)

    def handle_request(self, client_address, request_packet):
        try:
            request = request_packet.data.decode()
            print(f"[REQUISIÇÃO] Recebida de {client_address}: {request}")
            if request.startswith("GET "):
                file_path = request[4:].strip()
                self.send_file(client_address, file_path)
            elif request.startswith("MISSING "):
                parts = request[8:].strip().split(",")
                file_path = parts[0]
                missing_seqs = list(map(int, parts[1:]))
                self.retransmit_missing(client_address, file_path, missing_seqs)
            else:
                self.send_error(client_address, "Requisição inválida")
        except Exception as e:
            print(f"[ERRO] Falha ao processar requisição de {client_address}: {e}")
            self.send_error(client_address, "Erro interno no servidor")

    def start(self):
        print("Servidor aguardando conexões...")
        connected_clients = set()  # Para rastrear clientes conectados
        while True:
            try:
                packet_bytes, client_address = self.socket.recvfrom(1500)
                if client_address not in connected_clients:
                    connected_clients.add(client_address)
                    print(f"[CONEXÃO] Novo cliente conectado: {client_address}")
                print(f"[RECEBIDO] Pacote de {client_address} ({len(packet_bytes)} bytes)")
                request_packet = Packet.from_bytes(packet_bytes)
                self.handle_request(client_address, request_packet)
            except Exception as e:
                print(f"[ERRO] {e}")

if __name__ == "__main__":
    port = int(input("Digite a porta do servidor (>1024): "))
    server = UDPServer(port=port)
    server.start()