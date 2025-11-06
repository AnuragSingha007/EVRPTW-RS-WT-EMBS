"""Energy planning strategies based on the referenced research paper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from .models import ChargingStation, Customer, Node, RouteLeg


@dataclass(frozen=True)
class EnergyEvent:
    """Represents an energy related event along a vehicle route."""

    event_type: str
    location: Tuple[float, float]
    leg: RouteLeg
    station: Optional[ChargingStation] = None


class MidArcSwapPlanner:
    """Planner that sets swap events at arc midpoints and charges at stations.

    The implementation follows the idea from *Coordinated routing of electric
    commercial vehicles with intra-route recharging and en-route battery
    swapping*. The original model performs battery swapping operations at the
    downstream customer. This planner adapts the behaviour so that swapping
    happens at the midpoint of the travelled arc between two consecutive
    customers. Conductive charging events continue to use the provided charging
    station as their physical location.
    """

    def __init__(self, default_station: ChargingStation):
        self._default_station = default_station

    @staticmethod
    def _midpoint(a: Node, b: Node) -> Tuple[float, float]:
        """Return the midpoint between two nodes."""

        return ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)

    def plan_leg(self, leg: RouteLeg) -> Optional[EnergyEvent]:
        """Generate an energy event for a single route leg.

        Parameters
        ----------
        leg:
            The route leg under consideration.

        Returns
        -------
        Optional[EnergyEvent]
            ``EnergyEvent`` if the leg requires an energy operation, otherwise
            ``None``.

        Raises
        ------
        ValueError
            If swapping is requested for a leg that is not bounded by two
            customer nodes.
        """

        if leg.energy_option == "swap":
            if not isinstance(leg.start, Customer) or not isinstance(leg.end, Customer):
                raise ValueError(
                    "Battery swapping at mid-arc is only defined between customer nodes."
                )
            midpoint = self._midpoint(leg.start, leg.end)
            return EnergyEvent("swap", midpoint, leg)

        if leg.energy_option == "charge":
            return EnergyEvent(
                "charge",
                self._default_station.position(),
                leg,
                station=self._default_station,
            )

        return None

    def plan_route(self, legs: Iterable[RouteLeg]) -> List[EnergyEvent]:
        """Produce energy events for an entire route."""

        events: List[EnergyEvent] = []
        for leg in legs:
            event = self.plan_leg(leg)
            if event is not None:
                events.append(event)
        return events
