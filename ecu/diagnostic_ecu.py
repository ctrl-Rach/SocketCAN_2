import can
import time
from datetime import datetime

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)

print("==============================================")
print("          DIAGNOSTIC ECU STARTED")
print("==============================================")
print("Monitoring CAN network...\n")


# =========================================================
# Last message timestamps
# =========================================================

last_sensor = 0
last_controller = 0
last_power = 0

faults = []


def log_fault(message):

    timestamp = datetime.now().strftime("%H:%M:%S")

    entry = f"{timestamp} - {message}"

    if entry not in faults:

        faults.append(entry)

        print("\n" + "!" * 60)
        print("DIAGNOSTIC FAULT")
        print("!" * 60)
        print(f"Timestamp : {timestamp}")
        print(f"Fault     : {message}")
        print("!" * 60)


def send_diagnostic_status():

    # Fault count
    fault_count = min(len(faults), 255)

    # Overall status
    status = 0 if fault_count == 0 else 1

    message = can.Message(
        arbitration_id=0x400,
        data=[
            status,
            fault_count,
            1 if last_sensor else 0,
            1 if last_controller else 0,
            1 if last_power else 0
        ],
        is_extended_id=False
    )

    try:
        bus.send(message)

    except can.CanError:
        pass


while True:

    message = bus.recv(timeout=0.1)

    now = time.time()

    # =====================================================
    # Process CAN message
    # =====================================================

    if message is not None:

        # -------------------------------------------------
        # Sensor ECU
        # -------------------------------------------------

        if message.arbitration_id in [
            0x100,
            0x101,
            0x102,
            0x103
        ]:

            last_sensor = now

        # -------------------------------------------------
        # Controller ECU
        # -------------------------------------------------

        elif message.arbitration_id in [
            0x200,
            0x201,
            0x202
        ]:

            last_controller = now

        # -------------------------------------------------
        # Power Control ECU
        # -------------------------------------------------

        elif message.arbitration_id in [
            0x300,
            0x301
        ]:

            last_power = now

        # -------------------------------------------------
        # Sensor data validation
        # -------------------------------------------------

        if message.arbitration_id == 0x101:

            cell4 = (
                ((message.data[0] << 8) | message.data[1])
                / 100
            )

            temperature = message.data[2] - 40

            current = message.data[3] - 100

            if temperature > 60:

                log_fault(
                    f"Battery over-temperature: "
                    f"{temperature} °C"
                )

            elif temperature < -10:

                log_fault(
                    f"Battery temperature too low: "
                    f"{temperature} °C"
                )

            if cell4 > 4.20:

                log_fault(
                    f"Cell 4 over-voltage: "
                    f"{cell4:.2f} V"
                )

            elif cell4 < 3.00:

                log_fault(
                    f"Cell 4 under-voltage: "
                    f"{cell4:.2f} V"
                )

            if abs(current) > 50:

                log_fault(
                    f"Abnormal battery current: "
                    f"{current} A"
                )

        # -------------------------------------------------
        # Battery pack status
        # -------------------------------------------------

        elif message.arbitration_id == 0x102:

            state = message.data[0]

            if state == 2:

                log_fault("Battery pack over-temperature")

            elif state == 3:

                log_fault("Battery pack low temperature")

            elif state == 4:

                log_fault("Battery pack overvoltage")

            elif state == 5:

                log_fault("Battery pack undervoltage")

    # =====================================================
    # ECU timeout detection
    # =====================================================

    if (
        last_sensor != 0
        and now - last_sensor > 3
    ):

        log_fault("Sensor ECU timeout")

        last_sensor = now


    if (
        last_controller != 0
        and now - last_controller > 3
    ):

        log_fault("BMS Controller ECU timeout")

        last_controller = now


    if (
        last_power != 0
        and now - last_power > 3
    ):

        log_fault("Power Control ECU timeout")

        last_power = now


    # =====================================================
    # Diagnostic status message
    # =====================================================

    send_diagnostic_status()


    # =====================================================
    # Display
    # =====================================================

    sensor_status = (
        "OK"
        if last_sensor and now - last_sensor < 3
        else "WAIT"
    )

    controller_status = (
        "OK"
        if last_controller and now - last_controller < 3
        else "WAIT"
    )

    power_status = (
        "OK"
        if last_power and now - last_power < 3
        else "WAIT"
    )

    print(
        f"\rSensor: {sensor_status} | "
        f"Controller: {controller_status} | "
        f"Power: {power_status} | "
        f"Faults: {len(faults)}",
        end="",
        flush=True
    )

    time.sleep(0.1)
