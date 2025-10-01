import network
import espnow

PEERS_FILE = "/peers.txt"

def load_peers():
    try:
        with open(PEERS_FILE) as f:
            return [line.strip() for line in f if line.strip()]
    except OSError:
        return []

class ESPNowMessenger:
    def __init__(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        self.e = espnow.ESPNow()
        self.e.active(True)
        self.peers = set()
        self.load_peers_from_file()

    def load_peers_from_file(self):
        macs = load_peers()
        for mac_str in macs:
            try:
                mac = self.mac_str_to_bytes(mac_str)
                self.add_peer(mac)
            except Exception as e:
                print("Invalid MAC in peers.txt:", mac_str, e)

    def add_peer(self, mac):
        """Add a peer MAC address (as bytes)."""
        if mac not in self.peers:
            self.e.add_peer(mac)
            self.peers.add(mac)

    def send(self, topic, value):
        """Send a message to all peers with a topic and value."""
        msg = f"{topic}:{value}".encode()
        for mac in self.peers:
            self.e.send(mac, msg)

    def send_to(self, mac, topic, value):
        """Send a message to a specific peer."""
        msg = f"{topic}:{value}".encode()
        self.e.send(mac, msg)

    @staticmethod
    def mac_str_to_bytes(mac_str):
        """Convert MAC string (e.g. 'AA:BB:CC:DD:EE:FF') to bytes."""
        return bytes(int(b, 16) for b in mac_str.split(':'))