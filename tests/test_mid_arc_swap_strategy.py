import math

import pytest

from evrptw import ChargingStation, Customer, MidArcSwapPlanner, RouteLeg


@pytest.fixture
def sample_nodes():
    return {
        "c1": Customer("C1", 0.0, 0.0),
        "c2": Customer("C2", 4.0, 0.0),
        "cs": ChargingStation("S1", 2.0, 2.0),
        "d": ChargingStation("Depot", -1.0, -1.0),
    }


def test_swap_event_uses_arc_midpoint(sample_nodes):
    planner = MidArcSwapPlanner(sample_nodes["cs"])
    leg = RouteLeg(sample_nodes["c1"], sample_nodes["c2"], energy_option="swap")

    event = planner.plan_leg(leg)

    assert event is not None
    assert event.event_type == "swap"
    assert math.isclose(event.location[0], 2.0)
    assert math.isclose(event.location[1], 0.0)


def test_swap_requires_customer_nodes(sample_nodes):
    planner = MidArcSwapPlanner(sample_nodes["cs"])
    non_customer_leg = RouteLeg(sample_nodes["cs"], sample_nodes["c1"], energy_option="swap")

    with pytest.raises(ValueError):
        planner.plan_leg(non_customer_leg)


def test_charge_event_uses_station_location(sample_nodes):
    planner = MidArcSwapPlanner(sample_nodes["cs"])
    leg = RouteLeg(sample_nodes["c1"], sample_nodes["c2"], energy_option="charge")

    event = planner.plan_leg(leg)

    assert event is not None
    assert event.event_type == "charge"
    assert event.station == sample_nodes["cs"]
    assert event.location == sample_nodes["cs"].position()


def test_plan_route_filters_none(sample_nodes):
    planner = MidArcSwapPlanner(sample_nodes["cs"])
    legs = [
        RouteLeg(sample_nodes["c1"], sample_nodes["c2"], energy_option="swap"),
        RouteLeg(sample_nodes["c2"], sample_nodes["cs"], energy_option="none"),
        RouteLeg(sample_nodes["cs"], sample_nodes["c1"], energy_option="charge"),
    ]

    events = planner.plan_route(legs)

    assert [event.event_type for event in events] == ["swap", "charge"]
    assert len(events) == 2
