from guards.guard_engine import guard_manager, register_guard, report, status_all_guards

def test_guard_registration_and_reporting():
    # register a guard
    g = register_guard('guard-A', thresholds={'hop_min': 2, 'rtthresh_factor': 2.0})
    assert g is not None
    # report a simple event that should be suspicious by hop threshold
    event = {
        'route_id': 'r1',
        'src': 1,
        'dst': 2,
        'hops': 2,
        'rtt': 0.5,
        'neighbors': [2,3],
        'detected': False,
    }
    res = g.process_event(event)
    assert isinstance(res, dict)
    # status should reflect at least one guard
    all_status = status_all_guards()
    assert isinstance(all_status, list)
