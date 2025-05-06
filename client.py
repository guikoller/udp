import socket
from packet import Packet

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(10)
        print(f"Cliente configurado para se conectar ao servidor {server_ip}:{server_port}")

    def send_request(self, filename):
        request_packet = Packet(seq=0, pkt_type=0, data=f"GET {filename}".encode())
        self.sock.sendto(request_packet.to_bytes(), (self.server_ip, self.server_port))
        print(f"[ENVIO] Requisição enviada: GET {filename}")

    def receive_file(self, filename, simulate_loss=False):
        segments = {}
        expected_seq = 0

        while True:
            try:
                packet_bytes, addr = self.sock.recvfrom(1500)
                print(f"[RECEBIDO] Pacote de {addr} ({len(packet_bytes)} bytes)")
                packet = Packet.from_bytes(packet_bytes)

                if packet.pkt_type == 2:  # Erro do servidor
                    print(f"[ERRO] Mensagem do servidor: {packet.data.decode()}")
                    return None

                if packet.pkt_type == 1:  # Pacote de dados
                    if simulate_loss and packet.seq % 2 == 0:
                        print(f"[SIMULAÇÃO] Perda do pacote {packet.seq}")
                        continue
                    segments[packet.seq] = packet.data
                    print(f"[RECEBIDO] Pacote {packet.seq} armazenado ({len(packet.data)} bytes)")
                    expected_seq = max(expected_seq, packet.seq + 1)

            except socket.timeout:
                print("[ERRO] Timeout esperando por pacotes.")
                break
            except ValueError as e:
                print(f"[ERRO] Falha ao processar pacote: {e}")
                continue

        missing_seqs = [seq for seq in range(expected_seq) if seq not in segments]
        if missing_seqs:
            print(f"[FALTA] Pacotes perdidos detectados: {missing_seqs}")
            self.request_retransmission(filename, missing_seqs)
        return segments

    def request_retransmission(self, filename, missing_seqs):
        max_seqs_per_request = 100
        for i in range(0, len(missing_seqs), max_seqs_per_request):
            chunk = missing_seqs[i:i + max_seqs_per_request]
            missing_request = f"MISSING {filename}," + ",".join(map(str, chunk))
            request_packet = Packet(seq=0, pkt_type=0, data=missing_request.encode())
            self.sock.sendto(request_packet.to_bytes(), (self.server_ip, self.server_port))
            print(f"[ENVIO] Solicitação de retransmissão enviada para pacotes: {chunk}")

    def save_file(self, segments, filename):
        with open(f"received_{filename}", 'wb') as f:
            for seq in sorted(segments.keys()):
                f.write(segments[seq])
        print(f"[SALVO] Arquivo salvo como received_{filename}")

    def run(self, filename, simulate_loss=False):
        print(f"[INÍCIO] Solicitando arquivo: {filename}")
        self.send_request(filename)
        segments = self.receive_file(filename, simulate_loss)
        if segments:
            self.save_file(segments, filename)
        print("[FINALIZADO] Transferência concluída.")

if __name__ == "__main__":
    server_ip = input("Digite o IP do servidor: ").strip()
    server_port = int(input("Digite a porta do servidor: ").strip())
    filename = input("Digite o nome do arquivo a ser solicitado: ").strip()
    simulate_loss = input("Simular perda de pacotes? (s/n): ").lower() == 's'

    client = Client(server_ip, server_port)
    client.run(filename, simulate_loss)