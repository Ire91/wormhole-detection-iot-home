import os
from data_loader.dataset_loader import load_unsw_nb15_packets


def test_loader_maps_basic_csv():
    root = os.path.join("data", "public", "unsw_nb15_test_tmp")
    os.makedirs(root, exist_ok=True)
    csv_path = os.path.join(root, "sample.csv")
    with open(csv_path, "w", newline="") as f:
        f.write("src_ip,dst_ip,duration,label\n")
        f.write("192.168.0.1,192.168.0.2,1.23,normal\n")
        f.write("10.0.0.1,10.0.0.2,0.5,attack\n")

    packets = load_unsw_nb15_packets(root, max_packets=2)
    assert isinstance(packets, list)
    assert len(packets) == 2
    # basic field checks
    first = packets[0]
    assert "packet_id" in first
    assert isinstance(first["packet_id"], int)
    assert "src" in first and "dst" in first
