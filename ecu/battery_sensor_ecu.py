import can
import time
import random

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)

print("==============================================")
print("       BATTERY SENSOR ECU STARTED")
print("==============================================")
print("Sending battery sensor data...\n")

while True:

    # Simulated measurements
    cell1 = round(random.uniform(3.65, 3.75), 2)
    cell2 = round(random.uniform(3.65, 3.75), 2)
    cell3 = round(random.uniform(3.65, 3.75), 2)
    cell4 = round(random.uniform(3.65, 3.75), 2)

    temperature = round(random.uniform(25, 35), 1)
    current = round(random.uniform(-30, 30), 1)

    # Encoding
    c1 = int(cell1 * 100)
    c2 = int(cell2 * 100)
    c3 = int(cell3 * 100)
    c4 = int(cell4 * 100)

    temp = int(temperature + 40)
    curr = int(current + 100)

    total_voltage = cell1 + cell2 + cell3 + cell4
    average_voltage = total_voltage / 4

    soc = ((average_voltage - 3.60) / 0.60) * 100
    soc = max(0, min(100, soc))

    # Battery state
    if temperature > 50:
        state = 2
    elif temperature < 0:
        state = 3
    elif any(x > 4.20 for x in [cell1, cell2, cell3, cell4]):
        state = 4
    elif any(x < 3.00 for x in [cell1, cell2, cell3, cell4]):
        state = 5
    else:
        state = 1

    # -----------------------------------------------------
    # 0x100 - Cell 1, 2, 3
    # -----------------------------------------------------

    msg100 = can.Message(
        arbitration_id=0x100,
        data=[
            c1 >> 8, c1 & 0xFF,
            c2 >> 8, c2 & 0xFF,
            c3 >> 8, c3 & 0xFF
        ],
        is_extended_id=False
    )

    # -----------------------------------------------------
    # 0x101 - Cell 4 + Temperature + Current
    # -----------------------------------------------------

    msg101 = can.Message(
        arbitration_id=0x101,
        data=[
            c4 >> 8, c4 & 0xFF,
            temp,
            curr
        ],
        is_extended_id=False
    )

    # -----------------------------------------------------
    # 0x102 - Battery Pack Status
    # Byte 0 = state
    # Byte 1 = SOC
    # Byte 2-3 = total battery voltage * 10
    # -----------------------------------------------------

    pack_voltage = int(total_voltage * 10)

    msg102 = can.Message(
        arbitration_id=0x102,
        data=[
            state,
            int(soc),
            pack_voltage >> 8,
            pack_voltage & 0xFF
        ],
        is_extended_id=False
    )

    # -----------------------------------------------------
    # 0x103 - Sensor Health
    # -----------------------------------------------------

    msg103 = can.Message(
        arbitration_id=0x103,
        data=[
            1,  # Sensor ECU
            1,  # Voltage sensor
            1,  # Temperature sensor
            1   # Current sensor
        ],
        is_extended_id=False
    )

    # Send all sensor messages
    bus.send(msg100)
    bus.send(msg101)
    bus.send(msg102)
    bus.send(msg103)

    print("=" * 55)
    print(
        f"Cells: {cell1:.2f}V | "
        f"{cell2:.2f}V | "
        f"{cell3:.2f}V | "
        f"{cell4:.2f}V"
    )
    print(f"Temperature    : {temperature:.1f} °C")
    print(f"Current        : {current:.1f} A")
    print(f"Battery Voltage: {total_voltage:.2f} V")
    print(f"SOC            : {soc:.1f} %")
    print(f"Battery State  : {state}")
    print("Sensor Health  : OK")
    print("=" * 55)

    time.sleep(1)

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
