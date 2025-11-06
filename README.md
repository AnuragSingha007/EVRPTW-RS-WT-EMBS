# EVRPTW Energy Planning Utilities

This repository provides a light-weight Python package that captures the
behaviour described in *Coordinated routing of electric commercial vehicles with
intra-route recharging and en-route battery swapping*. The implementation adapts
the battery swapping decision so that swaps happen at the midpoint of the arc
connecting two customer nodes, instead of at the downstream customer. Conductive
recharging still occurs at a designated charging station.

## Loading instance datasets

Datasets describing customers, charging stations, and route legs can be supplied
as either JSON mappings or a compact text format. Use the :func:`load_instance`
helper to read a file and then call :meth:`Instance.plan_events` to obtain the
energy events for each leg in the instance.

```python
from evrptw import load_instance

instance = load_instance("instances/example.json")
energy_events = instance.plan_events()
```

The compact text format accepts directives such as ``CUSTOMER``, ``STATION``,
``DEFAULT_STATION``, and ``LEG``. Lines starting with ``#`` are treated as
comments.

## Running the tests

```bash
pytest
```
