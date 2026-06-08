# Prediction — Desktop

Aggregator scripts that install, launch, and remove all desktop prediction modules.

## Install (Mac / Linux)

```bash
./install.sh              # install all modules + download data
./install.sh --skip-data  # install dependencies only (no data download)
```

## Launch

```bash
./start.sh
```

## Uninstall

```bash
./uninstall.sh
```

## Windows

```bat
install.bat
start.bat
uninstall.bat
```

## Modules

| Module       | Location                                                               |
|--------------|------------------------------------------------------------------------|
| Stock Market | `../../domains/finance/projects/stock-market/development/software/desktop/` |

## Adding a Module

In `install.sh` / `install.bat`, add a block that calls the new module's install script. In `start.sh` / `start.bat`, add a launch command.
