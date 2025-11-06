# EVRPTW Energy Planning Utilities

This repository provides a light-weight Python package that captures the
behaviour described in *Coordinated routing of electric commercial vehicles with
intra-route recharging and en-route battery swapping*. The implementation adapts
the battery swapping decision so that swaps happen at the midpoint of the arc
connecting two customer nodes, instead of at the downstream customer. Conductive
recharging still occurs at a designated charging station.

## Running the tests

```bash
pytest
```
