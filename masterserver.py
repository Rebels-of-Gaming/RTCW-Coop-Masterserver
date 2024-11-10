import asyncio
import time
import subprocess
import sys
import socket
import signal
from aiohttp import web
import json

# Funktion zum Überprüfen und Installieren von Paketen
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"{package} wird installiert...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Überprüfen und Installieren von requests und aiohttp
install_package('requests')
install_package('aiohttp')
from aiohttp import web  # Nach der Installation importieren
import requests  # Nach der Installation importieren

# Speicher für Serverdaten
servers = {}

# Funktion zum Abrufen der öffentlichen IP-Adresse
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der öffentlichen IP-Adresse: {e}")
        return '0.0.0.0'

# Funktion zum Senden einer getstatus-Abfrage an den Spieleserver
def query_server(address):
    server_ip, server_port = address
    query = b"\xFF\xFF\xFF\xFFgetstatus"
    response_data = b""

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.sendto(query, (server_ip, server_port))
            while True:
                try:
                    data, _ = sock.recvfrom(4096)
                    response_data += data
                except socket.timeout:
                    break
    except Exception as e:
        print(f"Fehler bei der Abfrage von {server_ip}:{server_port} - {e}")
        return None

    if response_data.startswith(b"\xFF\xFF\xFF\xFFstatusResponse\n"):
        response_text = response_data[22:].decode('latin1', errors='ignore')
        return response_text
    else:
        print(f"Unerwartete Antwort von {server_ip}:{server_port}")
        return None

# Funktion zum Extrahieren der Spieleranzahl aus den Serverinformationen
def extract_players(info):
    # Der Info-String enthält normalerweise Informationen zu Spielern am Ende
    lines = info.splitlines()
    player_lines = lines[1:]  # Ignoriere die erste Zeile (Serverinfos)

    # Extrahiere die maximale Spieleranzahl
    max_clients = "0"
    for item in lines[0].split("\\"):
        if item == "sv_maxcoopclients":
            max_clients = lines[0].split("\\")[lines[0].split("\\").index("sv_maxcoopclients") + 1]
            break

    # Anzahl der aktiven Spieler anhand der Zeilen nach der ersten
    active_players = len(player_lines)
    return f"{active_players}/{max_clients}"

# Funktion zum Verarbeiten von TCP-Heartbeats
async def handle_tcp_heartbeat(reader, writer):
    data = await reader.read(1024)
    message = data.decode()
    
    # IP-Adresse und Port des anfragenden Servers
    addr = writer.get_extra_info('peername')
    
    # Serverinformationen durch Abfrage abrufen
    server_info = query_server(addr)
    
    if server_info:
        # Speichern oder Aktualisieren der Serverdaten mit dem aktuellen Zeitstempel
        servers[addr] = {
            "last_seen": time.time(),
            "info": server_info,
            "players": extract_players(server_info)  # Extrahiere die Spieleranzahl
        }
        print(f"TCP Heartbeat empfangen von {addr}: {server_info}")
    else:
        print(f"Fehler beim Abrufen von Informationen von {addr}")
    
    # Antwort an den Server
    writer.write(b"Heartbeat acknowledged")
    await writer.drain()
    writer.close()

# Funktion zum Verarbeiten von UDP-Heartbeats und getservers-Anfragen
class UDPServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            message = data.decode('latin1', errors='ignore')
        except UnicodeDecodeError:
            message = data.decode('latin1', errors='replace')

        # Prüfen, ob die Anfrage eine "getservers"-Anfrage ist
        if message.startswith("\xFF\xFF\xFF\xFFgetservers"):
            print(f"'getservers'-Anfrage von {addr}")
            self.send_server_list(addr)
        else:
            # Heartbeat von Server
            server_info = query_server(addr)
            if server_info:
                servers[addr] = {
                    "last_seen": time.time(),
                    "info": server_info,
                    "players": extract_players(server_info)  # Extrahiere die Spieleranzahl
                }
                print(f"UDP Heartbeat empfangen von {addr}: {server_info}")
            else:
                print(f"Fehler beim Abrufen von Informationen von {addr}")

            self.transport.sendto(b"Heartbeat acknowledged", addr)

    # Funktion zum Senden der Serverliste als Antwort auf eine getservers-Anfrage
    def send_server_list(self, addr):
        server_list = b""
        for server_addr, data in servers.items():
            ip, port = server_addr
            ip_bytes = socket.inet_aton(ip)  # Konvertiert die IP in 4 Byte
            port_bytes = port.to_bytes(2, byteorder="big")  # Konvertiert den Port in 2 Byte
            server_list += b'\\' + ip_bytes + port_bytes  # Hinzufügen der IP und Port mit Trennzeichen '\\'

        # Formatieren und Senden der Antwort als `oob`-Nachricht mit Abschluss "\\EOT\\"
        response = b"\xFF\xFF\xFF\xFFgetserversResponse" + server_list + b"\\EOT\\"
        self.transport.sendto(response, addr)

# Cleanup-Funktion zum Entfernen inaktiver Server
async def cleanup_servers():
    while True:
        current_time = time.time()
        for addr in list(servers.keys()):
            if current_time - servers[addr]["last_seen"] > 300:  # z.B. 5 Minuten Inaktivität
                print(f"Entferne inaktiven Server {addr}")
                del servers[addr]
        await asyncio.sleep(60)  # Alle 60 Sekunden aufräumen

# Funktion zur Umwandlung von Gametype-Codes in Namen
def get_gametype_name(gametype_code):
    gametype_map = {
        "0": "battle",
        "1": "speed",
        "2": "coop"
    }
    return gametype_map.get(gametype_code, "Unknown")

# HTML-Handler für die Serverliste als Tabelle
async def render_server_list(request):
    # HTML-Template für die Serverliste
    html = """
    <html>
    <head>
        <title>RTCW Master-Server</title>
        <meta http-equiv="refresh" content="10">
        <style>
            table {
                width: 80%;
                margin: 20px auto;
                border-collapse: collapse;
            }
            table, th, td {
                border: 1px solid black;
            }
            th, td {
                padding: 10px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h2 style="text-align: center;">RTCW Server Browser</h2>
        <table>
            <tr>
                <th>NAME</th>
                <th>ADDRESS</th>
                <th>MAP</th>
                <th>MOD</th>
                <th>GAMETYPE</th>
                <th>PLAYERS</th>
            </tr>
    """

    # Erzeuge eine Tabellenzeile für jeden Server in der Liste
    for addr, data in servers.items():
        # Parsing der server_info aus data["info"]
        info = data["info"]
        info_dict = {}
        
        # Parse den `info`-String und füge nur gültige Paare hinzu
        items = info.split("\\")
        for i in range(0, len(items) - 1, 2):
            key, value = items[i], items[i + 1]
            info_dict[key] = value

        # Extrahiere Serverinformationen aus info_dict
        name = info_dict.get("sv_hostname", "Unknown")
        address = f"{addr[0]}:{addr[1]}"
        map_name = info_dict.get("mapname", "Unknown")
        mod = info_dict.get("gamename", "Unknown")
        gametype_code = info_dict.get("g_gametype", "Unknown")
        gametype = get_gametype_name(gametype_code)  # Verwende die Mapping-Funktion
        players = data["players"]

        # Füge eine Tabellenzeile hinzu
        html += f"""
            <tr>
                <td>{name}</td>
                <td>{address}</td>
                <td>{map_name}</td>
                <td>{mod}</td>
                <td>{gametype}</td>
                <td>{players}</td>
            </tr>
        """

    # Schließe das HTML-Dokument
    html += """
        </table>
    </body>
    </html>
    """

    return web.Response(text=html, content_type='text/html')

# Startet den HTTP-Server
async def start_http_server():
    app = web.Application()
    app.add_routes([web.get('/', render_server_list)])      # Standard-Route für HTML-Tabelle hinzufügen
    app.add_routes([web.get('/servers', render_server_list)])  # Alternative Route für HTML-Tabelle
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)  # HTTP-Server auf Port 80
    print("HTTP-Server läuft auf Port 80")
    await site.start()

# Signal-Handler für sauberen Shutdown
def signal_handler(loop):
    print("\nBeende den Server...")
    for task in asyncio.all_tasks(loop):
        task.cancel()
    loop.stop()

# Server-Start
async def main():
    public_ip = get_public_ip()
    print(f"Master-Server wird auf öffentlicher IP {public_ip} und Port 27950 gestartet")
    
    # TCP-Server starten
    tcp_server = await asyncio.start_server(handle_tcp_heartbeat, public_ip, 27950)

    # UDP-Server starten
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: UDPServerProtocol(),
        local_addr=(public_ip, 27950)
    )

    # Signal-Handler hinzufügen
    loop.add_signal_handler(signal.SIGINT, lambda: signal_handler(loop))
    loop.add_signal_handler(signal.SIGTERM, lambda: signal_handler(loop))

    # Startet den HTTP-Server und Cleanup-Tasks gleichzeitig
    await asyncio.gather(
        tcp_server.serve_forever(),
        cleanup_servers(),
        start_http_server()
    )

# Starten des Servers
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
except (asyncio.CancelledError, KeyboardInterrupt):
    pass
finally:
    # Stelle sicher, dass alle Tasks beendet werden, bevor das Event-Loop geschlossen wird
    pending = asyncio.all_tasks(loop)
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()
    print("Server wurde beendet.")
