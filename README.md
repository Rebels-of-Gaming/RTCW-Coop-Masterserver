# RTCW Coop Master Server

Dieser Master-Server ermöglicht es, für das Spiel *Return to Castle Wolfenstein: Coop* eine zentrale Serverliste bereitzustellen. Das Projekt verwendet Python und stellt einen Master-Server sowie eine HTML-Seite zur Anzeige der Serverliste zur Verfügung.

## Voraussetzungen

- **Python 3.6+** (Python 3.11 wird empfohlen)
- **Internetverbindung**, um die benötigten Python-Pakete herunterzuladen

## Installation

### 1. Python und Pip installieren

Falls Python 3 und Pip noch nicht installiert sind:

# Aktualisieren Sie die Paketliste
```sudo apt update```

# Installieren Sie Python 3 und Pip (Python-Paketmanager)
```sudo apt install -y python3 python3-pip```


## 2. Benötigte Python-Pakete installieren
Die folgenden Python-Module werden benötigt: aiohttp und requests.

# Installieren der Python-Module aiohttp und requests
```pip3 install aiohttp requests```
Falls das Skript auf einem Server läuft, der keine automatische Installation von Paketen zulässt, können Sie diese Installationsanweisungen direkt im Skript integrieren (siehe Code im Repository).

## 3. Skript herunterladen und konfigurieren
Klonen Sie das Repository oder laden Sie das Skript herunter:

```git clone <repository-url>```
```cd <repository-folder>```
# Fügen Sie das Skript in eine Datei namens masterserver.py ein (falls Sie den Code manuell kopieren).

## 4. Firewall konfigurieren (optional)
Falls eine Firewall aktiv ist, müssen die benötigten Ports freigegeben werden. Dies sind standardmäßig 27950 (UDP und TCP) für den Master-Server und 80 (TCP) für den HTTP-Server.


# Erlaubt eingehenden Verkehr auf Port 27950 (UDP und TCP) und Port 80 (TCP)
```sudo ufw allow 27950/tcp```
```sudo ufw allow 27950/udp```
```sudo ufw allow 80/tcp```
## 5. Master-Server starten
Starten Sie den Master-Server:

```python3 masterserver.py```
Die Konsole zeigt dann eine Ausgabe wie:

```Master-Server wird auf öffentlicher IP <Ihre IP> und Port 27950 gestartet```
```HTTP-Server läuft auf Port 80```

Der HTTP-Server stellt eine HTML-Seite zur Verfügung, die eine Übersicht aller registrierten Server bietet. Sie können diese Seite im Browser über die IP-Adresse Ihres Servers aufrufen (z. B. http://<Ihre IP>).

# Testen und Überwachen
RTCW Coop Spielclient: Starten Sie das Spiel und stellen Sie sicher, dass der Master-Server erreichbar ist und die Serverliste angezeigt wird.
Web-Browser: Überprüfen Sie die HTML-Seite, um sicherzustellen, dass registrierte Server korrekt angezeigt werden.
Server beenden
Um den Server zu stoppen, drücken Sie CTRL+C in der Konsole. Das Skript ist so konfiguriert, dass es alle laufenden Tasks ordnungsgemäß beendet.

## Zusammenfassung der Schritte
Python 3 installieren: ```sudo apt install -y python3 python3-pip```
Python-Pakete installieren: ```pip3 install aiohttp requests```
Skript speichern: ```nano masterserver.py```
Firewall konfigurieren (optional): ```sudo ufw allow 27950/tcp && sudo ufw allow 27950/udp && sudo ufw allow 80/tcp```
Server starten: ```python3 masterserver.py```
Testen: Überprüfen Sie, ob der Master-Server im Spiel und im Browser angezeigt wird.


## Lizenz
Dieses Projekt steht unter der MIT-Lizenz.
