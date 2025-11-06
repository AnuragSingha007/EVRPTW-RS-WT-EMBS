from pathlib import Path

from evrptw import Instance, load_instance


def data_path(name: str) -> Path:
    return Path(__file__).parent / "data" / name


def test_load_instance_from_json():
    instance = load_instance(data_path("sample_instance.json"))

    assert isinstance(instance, Instance)
    assert set(instance.customers) == {"C1", "C2"}
    assert set(instance.charging_stations) == {"S1"}

    events = instance.plan_events()

    assert [event.event_type for event in events] == ["swap", "charge"]
    swap_event = events[0]
    assert swap_event.leg.start.id == "C1"
    assert swap_event.location == (2.0, 0.0)


def test_load_instance_from_text():
    instance = load_instance(data_path("sample_instance.txt"))

    assert instance.default_station.id == "S1"
    assert len(instance.legs) == 2

    planner_events = instance.plan_events()
    assert [event.event_type for event in planner_events] == ["swap", "charge"]


def test_routes_expand_to_legs(tmp_path):
    dataset = {
        "customers": {
            "C1": {"id": "C1", "x": 0.0, "y": 0.0},
            "C2": {"id": "C2", "x": 4.0, "y": 0.0},
        },
        "charging_stations": {
            "S1": {"id": "S1", "x": 2.0, "y": 2.0},
        },
        "default_station": "S1",
        "routes": [["C1", "C2", "S1"]],
    }

    path = tmp_path / "instance.json"
    path.write_text(__import__("json").dumps(dataset))

    instance = load_instance(path)
    assert [(leg.start.id, leg.end.id, leg.energy_option) for leg in instance.legs] == [
        ("C1", "C2", "none"),
        ("C2", "S1", "none"),
    ]
