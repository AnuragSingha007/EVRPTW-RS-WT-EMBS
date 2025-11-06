"""Utilities for loading EVRPTW instances from lightweight datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Mapping, MutableMapping, Sequence

from .models import ChargingStation, Customer, Node, RouteLeg

if TYPE_CHECKING:
    from .strategies import EnergyEvent, MidArcSwapPlanner


@dataclass(frozen=True)
class Instance:
    """Container holding the data needed to plan energy events for a route."""

    customers: Dict[str, Customer]
    charging_stations: Dict[str, ChargingStation]
    default_station: ChargingStation
    legs: List[RouteLeg]

    def plan_events(
        self, planner: "MidArcSwapPlanner | None" = None
    ) -> List["EnergyEvent"]:
        """Plan energy events for the instance using a mid-arc swap strategy."""

        if planner is None:
            from .strategies import MidArcSwapPlanner

            planner = MidArcSwapPlanner(self.default_station)
        return planner.plan_route(self.legs)


def load_instance(path: str | Path) -> Instance:
    """Load an :class:`Instance` from a dataset file."""

    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = _parse_compact_text(text)
    else:
        data = _normalise_json_payload(data)
    return _build_instance(data)


def _build_instance(data: Mapping[str, Any]) -> Instance:
    customers = {
        cid: _build_customer(cid, spec)
        for cid, spec in _iter_node_specs(data.get("customers", {}))
    }
    charging_stations = {
        sid: _build_station(sid, spec)
        for sid, spec in _iter_node_specs(data.get("charging_stations", {}))
    }

    default_id = data.get("default_station")
    default_station: ChargingStation | None = None
    if isinstance(default_id, Mapping):
        did = _require_id(default_id, "default_station")
        default_station = _build_station(did, default_id)
        charging_stations.setdefault(default_station.id, default_station)
    elif isinstance(default_id, str):
        default_station = charging_stations.get(default_id)
    elif default_id is None and len(charging_stations) == 1:
        default_station = next(iter(charging_stations.values()))

    if default_station is None:
        raise ValueError("Dataset must define a default charging station.")

    legs: List[RouteLeg] = []
    for start_id, end_id, option in _iter_leg_specs(data):
        start_node = _lookup_node(start_id, customers, charging_stations)
        end_node = _lookup_node(end_id, customers, charging_stations)
        legs.append(RouteLeg(start_node, end_node, option))

    return Instance(customers, charging_stations, default_station, legs)


def _iter_node_specs(raw: Any) -> Iterator[tuple[str, Mapping[str, Any]]]:
    if isinstance(raw, Mapping):
        for node_id, spec in raw.items():
            if isinstance(spec, Mapping):
                yield node_id, spec
            else:
                raise TypeError("Node specification must be a mapping.")
    elif isinstance(raw, Sequence):
        for spec in raw:
            if not isinstance(spec, Mapping):
                raise TypeError("Node specification must be a mapping.")
            node_id = _require_id(spec, "node")
            yield node_id, spec
    else:
        raise TypeError("Nodes must be provided as a mapping or a sequence of mappings.")


def _iter_leg_specs(data: Mapping[str, Any]) -> Iterator[tuple[str, str, str]]:
    raw_legs = data.get("legs")
    if raw_legs is None:
        raw_routes = data.get("routes")
        if raw_routes is None:
            raise ValueError("Dataset must define either 'legs' or 'routes'.")
        for sequence in raw_routes:
            ids = _extract_id_sequence(sequence)
            for start, end in zip(ids, ids[1:]):
                yield start, end, "none"
        return

    for entry in raw_legs:
        start_id, end_id, option = _normalise_leg(entry)
        yield start_id, end_id, option


def _normalise_leg(entry: Any) -> tuple[str, str, str]:
    if isinstance(entry, Mapping):
        start_id = entry.get("start")
        end_id = entry.get("end")
        option = entry.get("energy_option", "none")
    elif isinstance(entry, Sequence):
        if len(entry) not in {2, 3}:
            raise ValueError("Leg sequence must contain two or three elements.")
        start_id, end_id, *maybe_option = entry
        option = maybe_option[0] if maybe_option else "none"
    else:
        raise TypeError("Leg entry must be a mapping or a short sequence.")

    if not isinstance(start_id, str) or not isinstance(end_id, str):
        raise TypeError("Leg start and end identifiers must be strings.")

    option = option or "none"
    if not isinstance(option, str):
        raise TypeError("Energy option must be a string.")
    option = option.lower()
    if option not in {"swap", "charge", "none"}:
        raise ValueError(f"Unsupported energy option: {option!r}")

    return start_id, end_id, option


def _extract_id_sequence(sequence: Any) -> List[str]:
    if isinstance(sequence, str):
        ids = sequence.split()
    elif isinstance(sequence, Sequence):
        ids = []
        for item in sequence:
            if not isinstance(item, str):
                raise TypeError("Route entries must be strings.")
            ids.append(item)
    else:
        raise TypeError("Route must be a whitespace separated string or a sequence of strings.")

    if len(ids) < 2:
        raise ValueError("Route definition must contain at least two nodes.")
    return ids


def _lookup_node(
    node_id: str,
    customers: Mapping[str, Customer],
    charging_stations: Mapping[str, ChargingStation],
) -> Node:
    if node_id in customers:
        return customers[node_id]
    if node_id in charging_stations:
        return charging_stations[node_id]
    raise KeyError(f"Unknown node identifier: {node_id}")


def _build_customer(node_id: str, spec: Mapping[str, Any]) -> Customer:
    x, y = _extract_coordinates(spec)
    return Customer(node_id, x, y)


def _build_station(node_id: str, spec: Mapping[str, Any]) -> ChargingStation:
    x, y = _extract_coordinates(spec)
    return ChargingStation(node_id, x, y)


def _extract_coordinates(spec: Mapping[str, Any]) -> tuple[float, float]:
    try:
        x = float(spec["x"])
        y = float(spec["y"])
    except KeyError as exc:
        raise KeyError(f"Missing coordinate component: {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("Coordinates must be numeric values.") from exc
    return x, y


def _require_id(spec: Mapping[str, Any], context: str) -> str:
    node_id = spec.get("id")
    if not isinstance(node_id, str):
        raise TypeError(f"{context} must define a string 'id' field.")
    return node_id


def _normalise_json_payload(payload: Any) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise TypeError("JSON dataset must be a mapping at the top level.")
    return dict(payload)


def _parse_compact_text(text: str) -> Mapping[str, Any]:
    customers: Dict[str, MutableMapping[str, Any]] = {}
    stations: Dict[str, MutableMapping[str, Any]] = {}
    legs: List[tuple[str, str, str]] = []
    routes: List[List[str]] = []
    default_station: str | None = None

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        keyword = tokens[0].lower()
        payload = tokens[1:]

        if keyword in {"customer", "c"}:
            if len(payload) < 3:
                raise ValueError(f"Line {line_no}: customer requires id, x, y.")
            node_id, x, y = payload[:3]
            customers[node_id] = {"id": node_id, "x": float(x), "y": float(y)}
        elif keyword in {"station", "charging_station", "cs", "depot"}:
            if len(payload) < 3:
                raise ValueError(f"Line {line_no}: station requires id, x, y.")
            node_id, x, y = payload[:3]
            stations[node_id] = {"id": node_id, "x": float(x), "y": float(y)}
        elif keyword in {"default_station", "default"}:
            if not payload:
                raise ValueError(f"Line {line_no}: default station id missing.")
            default_station = payload[0]
        elif keyword in {"leg", "arc"}:
            if len(payload) < 2:
                raise ValueError(f"Line {line_no}: leg requires start and end ids.")
            start_id, end_id = payload[:2]
            option = payload[2] if len(payload) >= 3 else "none"
            legs.append((start_id, end_id, option))
        elif keyword == "route":
            if len(payload) < 2:
                raise ValueError(f"Line {line_no}: route requires at least two nodes.")
            routes.append(payload)
        else:
            raise ValueError(f"Line {line_no}: unrecognised directive '{tokens[0]}'.")

    result: Dict[str, Any] = {
        "customers": list(customers.values()),
        "charging_stations": list(stations.values()),
        "default_station": default_station,
    }
    if legs:
        result["legs"] = [list(leg) for leg in legs]
    if routes:
        result.setdefault("routes", routes)
    return result
