import json
import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:5000/api/run', 
    data=b'{"profile":"medium_apartment", "attack_mode":"encapsulation", "scenario":"defence"}', 
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())

print(f"Detection Rate: {data['summary']['detection_rate']}")
print(f"FPR: {data['summary']['false_positive_rate']}")

alerts = {'HOP': 0, 'RTT': 0, 'STRETCH': 0, 'INCONSISTENCY': 0, 'SPIKE': 0}
for p in data['packets']:
    if p['is_attack']:
        for a in p['alerts']:
            if 'HOP' in a: alerts['HOP'] += 1
            if 'RTT' in a: alerts['RTT'] += 1
            if 'STRETCH' in a: alerts['STRETCH'] += 1
            if 'INCONSISTENCY' in a: alerts['INCONSISTENCY'] += 1
            if 'SPIKE' in a: alerts['SPIKE'] += 1
            
print('\nAttack Packets Alerts triggered:', alerts)

# Let's look at the first few undetected attack packets
print("\nSample Undetected Attack Packets:")
count = 0
for p in data['packets']:
    if p['is_attack'] and not p['detected']:
        print(f"Packet {p['id']}: Path={p['path']}, Hops={p['hop_count']}, Delay={p['delay']:.2f}ms")
        count += 1
        if count >= 3: break
