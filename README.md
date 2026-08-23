# EV Battery Monitoring System Using SocketCAN

A software-based **EV Battery Monitoring System (BMS)** developed using **Python, SocketCAN, and virtual CAN (`vcan0`)**.

## Features

* Battery cell voltage monitoring
* Temperature and current monitoring
* SOC estimation
* Charge/discharge control
* Cooling control
* CAN communication
* ECU fault detection and diagnostics
* Node failure detection and recovery

## ECUs

* **Battery Sensor ECU** – Generates battery measurements
* **BMS Controller ECU** – Processes data and makes safety decisions
* **Power Control ECU** – Simulates contactors and cooling fan
* **Diagnostic ECU** – Monitors CAN communication and detects faults

## Technology

* Python 3
* `python-can`
* Linux SocketCAN
* Virtual CAN (`vcan0`)

## Project Structure

```text
SocketCAN_2/
└── ecu/
    ├── battery_sensor_ecu.py
    ├── bms_controller_ecu.py
    ├── power_control_ecu.py
    └── diagnostic_ecu.py
```

## Run

Start the four ECUs using:

```bash
python3 ecu/battery_sensor_ecu.py
python3 ecu/bms_controller_ecu.py
python3 ecu/power_control_ecu.py
python3 ecu/diagnostic_ecu.py
```

Monitor CAN traffic with:

```bash
candump vcan0
```

## Testing

The system was verified for:

* Normal operation
* Missing CAN message detection
* Sensor fault detection
* ECU/node failure
* ECU recovery

This project demonstrates a distributed automotive system using SocketCAN.
