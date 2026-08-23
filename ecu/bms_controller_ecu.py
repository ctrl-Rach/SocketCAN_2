import can
import time

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)

print("==============================================")
print("         BMS CONTROLLER ECU STARTED")
print("==============================================")
print("Waiting for battery sensor data...\n")

cell1 = 0.0
cell2 = 0.0
cell3 = 0.0
cell4 = 0.0
temperature = 0.0
current = 0.0
soc = 0.0
battery_state = 0


def send_message(can_id, data):
    try:
        message = can.Message(
            arbitration_id=can_id,
            data=data,
            is_extended_id=False
        )
        bus.send(message)
    except can.CanError:
        print(f"ERROR: Failed to send 0x{can_id:X}")


def calculate_soc(avg_voltage):
    soc = ((avg_voltage - 3.60) / 0.60) * 100
    return max(0, min(100, soc))


while True:

    message = bus.recv(timeout=1)

    if message is None:
        print("WARNING: No CAN message received")
        continue

    # =====================================================
    # 0x100 - Cell 1, 2, 3
    # =====================================================

    if message.arbitration_id == 0x100:

        cell1 = (
            ((message.data[0] << 8) | message.data[1])
            / 100
        )

        cell2 = (
            ((message.data[2] << 8) | message.data[3])
            / 100
        )

        cell3 = (
            ((message.data[4] << 8) | message.data[5])
            / 100
        )

    # =====================================================
    # 0x101 - Cell 4 + Temperature + Current
    # =====================================================

    elif message.arbitration_id == 0x101:

        cell4 = (
            ((message.data[0] << 8) | message.data[1])
            / 100
        )

        temperature = message.data[2] - 40
        current = message.data[3] - 100

        total_voltage = cell1 + cell2 + cell3 + cell4
        average_voltage = total_voltage / 4

        soc = calculate_soc(average_voltage)

    # =====================================================
    # 0x102 - Battery Pack Status
    # =====================================================

    elif message.arbitration_id == 0x102:

        battery_state = message.data[0]

        soc = message.data[1]

        pack_voltage = (
            ((message.data[2] << 8) | message.data[3])
            / 10
        )

    # =====================================================
    # 0x103 - Sensor Health
    # =====================================================

    elif message.arbitration_id == 0x103:

        sensor_health = message.data[0]

    # =====================================================
    # Process complete battery data after 0x101
    # =====================================================

    if message.arbitration_id == 0x101:

        cells = [cell1, cell2, cell3, cell4]

        battery_status = "NORMAL"

        if temperature > 50:
            battery_status = "OVERHEAT"

        elif temperature < 0:
            battery_status = "LOW TEMPERATURE"

        elif any(cell > 4.20 for cell in cells):
            battery_status = "OVERVOLTAGE"

        elif any(cell < 3.00 for cell in cells):
            battery_status = "UNDERVOLTAGE"

        # -------------------------------------------------
        # Determine operation
        # -------------------------------------------------

        if battery_status != "NORMAL":

            mode = 3
            charge = 0
            discharge = 0
            cooling = 1

        elif temperature > 40:

            mode = 3
            charge = 0
            discharge = 0
            cooling = 1

        elif current > 0:

            mode = 1
            charge = 1
            discharge = 0
            cooling = 0

        elif current < 0:

            mode = 2
            charge = 0
            discharge = 1
            cooling = 0

        else:

            mode = 0
            charge = 0
            discharge = 0
            cooling = 0

        # =================================================
        # 0x200 - General Power Control Command
        # =================================================

        send_message(
            0x200,
            [
                charge,
                discharge,
                cooling,
                mode
            ]
        )

        # =================================================
        # 0x201 - Charging Command
        #
        # Byte 0 = enable/disable
        # Byte 1 = requested current
        # =================================================

        charging_current = max(
            0,
            min(100, int(abs(current)))
        )

        send_message(
            0x201,
            [
                charge,
                charging_current
            ]
        )

        # =================================================
        # 0x202 - Cooling Command
        #
        # Byte 0 = fan enable
        # Byte 1 = temperature
        # =================================================

        send_message(
            0x202,
            [
                cooling,
                max(0, min(255, int(temperature + 40)))
            ]
        )

        # =================================================
        # Display
        # =================================================

        total_voltage = cell1 + cell2 + cell3 + cell4

        print("\n" + "=" * 60)
        print("             BMS BATTERY STATUS")
        print("=" * 60)

        print(f"Cell 1 Voltage : {cell1:.2f} V")
        print(f"Cell 2 Voltage : {cell2:.2f} V")
        print(f"Cell 3 Voltage : {cell3:.2f} V")
        print(f"Cell 4 Voltage : {cell4:.2f} V")

        print("-" * 60)

        print(f"Battery Voltage : {total_voltage:.2f} V")
        print(f"Temperature     : {temperature:.1f} °C")
        print(f"Current         : {current:.1f} A")
        print(f"Estimated SOC   : {soc:.1f} %")
        print(f"Battery Status  : {battery_status}")

        if mode == 1:
            print("Operation       : CHARGING")

        elif mode == 2:
            print("Operation       : DISCHARGING")

        elif mode == 3:
            print("Operation       : SAFE MODE")

        else:
            print("Operation       : IDLE")

        print("=" * 60)

        time.sleep(0.1)
