import json
import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:5000/api/run', 
    data=b'{"profile":"large_house", "attack_mode":"encapsulation", "scenario":"defence"}', 
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

alerts = {'HOP': 0, 'RTT': 0, 'STRETCH': 0, 'INCONSISTENCY': 0, 'SPIKE': 0}
num_attack = 0

for p in data['packet_feed']:
    num_attack += 1
    # Check alerts (now a comma-separated string)
    al_str = p.get('alerts', '')
    if 'HOP' in al_str: alerts['HOP'] += 1
    if 'RTT' in al_str: alerts['RTT'] += 1
    if 'STRETCH' in al_str: alerts['STRETCH'] += 1
    if 'INCONSISTENCY' in al_str: alerts['INCONSISTENCY'] += 1
    if 'SPIKE' in al_str: alerts['SPIKE'] += 1
            
out_data = {
    "total_attack": num_attack,
    "alerts": alerts,
    "sample_undetected": []
}

for p in data['packet_feed']:
    if not p['detected']:
        out_data["sample_undetected"].append(f"ID:{p['id']} H={p['hops']} D={p['delay']:.0f}")
        if len(out_data["sample_undetected"]) >= 5: break

with open("encap_debug.json", "w") as f:
    json.dump(out_data, f, indent=2)
