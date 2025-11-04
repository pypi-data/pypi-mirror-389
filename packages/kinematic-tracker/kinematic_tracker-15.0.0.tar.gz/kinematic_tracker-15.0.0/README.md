# Kinematic Tracker

This tracker is based on kinematic Kalman filters. The system state can consist of multiple components,
each defined by its kinematic order and dimensionality. The tracker supports various process noise models,
including a custom adaptive process noise model based on a white-noise assumption.

## Tutorial Examples

Simple, reusable examples are available in the `test/tutorials` folder.

## Installation

After installing the `uv` package manager, run:

```shell
uv sync --no-dev
```

## Development Installation

For development setup instructions, please refer to the maintainers' README.
