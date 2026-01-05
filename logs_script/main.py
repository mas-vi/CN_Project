import json
import random
from datetime import datetime, timedelta

NUM_ENTRIES = 12 
OUTPUT_FILE = "network_logs.json"

PORTS = {80: "HTTP", 443: "HTTPS", 22: "SSH", 53: "DNS"}

def generate_logs():
    logs = []

    base_time = datetime.now() - timedelta(minutes=10)

    for i in range(NUM_ENTRIES):
        timestamp = (base_time + timedelta(seconds=i * 45)).strftime("%H:%M:%S")
        

        if 5 <= i <= 7:
            src_ip = "103.25.14.82"
            dest_ip = "192.168.1.10"
            port = random.choice([22, 23, 445]) 
            action = "DENY"
            notes = "Suspicious connection attempt"
        else:
            src_ip = f"192.168.1.{random.randint(2, 50)}"
            dest_ip = "8.8.8.8"
            port = random.choice([80, 443, 53])
            action = "ALLOW"
            notes = "Standard outgoing traffic"

        logs.append({
            "id": i + 1,
            "time": timestamp,
            "src": src_ip,
            "dst": dest_ip,
            "port": port,
            "proto": PORTS.get(port, "TCP"),
            "action": action,
            "msg": notes
        })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(logs, f, indent=2)
    
    print(f"Generated {NUM_ENTRIES} logs")

if __name__ == "__main__":
    generate_logs()