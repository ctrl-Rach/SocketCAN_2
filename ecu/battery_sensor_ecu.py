import can
import time
import random

# Create SocketCAN interface
bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)

print("Battery Sensor ECU started")
print("Sending battery sensor data...\n")

while True:

    # Simulated battery measurements
    cell1 = round(random.uniform(3.65, 3.75), 2)
    cell2 = round(random.uniform(3.65, 3.75), 2)
    cell3 = round(random.uniform(3.65, 3.75), 2)
    cell4 = round(random.uniform(3.65, 3.75), 2)

    temperature = round(random.uniform(25, 35), 1)
    current = round(random.uniform(-30, 30), 1)

    # Convert values into integers for CAN transmission
    cell1_int = int(cell1 * 100)
    cell2_int = int(cell2 * 100)
    cell3_int = int(cell3 * 100)
    cell4_int = int(cell4 * 100)

    temperature_int = int(temperature + 40)
    current_int = int(current + 100)

    # Cell voltage message
    msg_voltage = can.Message(
        arbitration_id=0x100,
        data=[
            cell1_int >> 8, cell1_int & 0xFF,
            cell2_int >> 8, cell2_int & 0xFF,
            cell3_int >> 8, cell3_int & 0xFF
        ],
        is_extended_id=False
    )

    # Temperature + current + Cell 4
    msg_status = can.Message(
        arbitration_id=0x101,
        data=[
            cell4_int >> 8, cell4_int & 0xFF,
            temperature_int,
            current_int
        ],
        is_extended_id=False
    )

    # Send messages
    bus.send(msg_voltage)
    bus.send(msg_status)

    print(
        f"Cells: {cell1:.2f}V, "
        f"{cell2:.2f}V, "
        f"{cell3:.2f}V, "
        f"{cell4:.2f}V"
    )

    print(
        f"Temperature: {temperature:.1f}°C | "
        f"Current: {current:.1f} A"
    )

    print("-" * 50)

    time.sleep(1)
