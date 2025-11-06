"""Data models used to describe the EVRPTW energy planning problem."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Node:
    """Basic network node with Euclidean coordinates."""

    id: str
    x: float
    y: float

    def position(self) -> tuple[float, float]:
        """Return the coordinates of the node as a tuple."""

        return (self.x, self.y)


@dataclass(frozen=True)
class Customer(Node):
    """Customer node in the distribution network."""


@dataclass(frozen=True)
class ChargingStation(Node):
    """Charging station that can be used for conductive recharging."""


EnergyOption = Literal["swap", "charge", "none"]


@dataclass(frozen=True)
class RouteLeg:
    """A directed arc in a vehicle route.

    Attributes
    ----------
    start:
        Node where the leg begins.
    end:
        Node where the leg ends.
    energy_option:
        Desired energy action for the leg. ``"swap"`` indicates that a
        battery swapping event should happen while travelling between the
        two nodes. ``"charge"`` indicates a conductive charging stop.
        ``"none"`` skips any energy related activity on the leg.
    """

    start: Node
    end: Node
    energy_option: EnergyOption = "none"
