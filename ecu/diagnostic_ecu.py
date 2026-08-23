import can
import time
from datetime import datetime


# ---------------------------------------------------------
# DIAGNOSTIC ECU
# ---------------------------------------------------------

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)


print("==============================================")
print("          DIAGNOSTIC ECU STARTED")
print("==============================================")
print("Monitoring CAN network...\n")


# ---------------------------------------------------------
# Last received message times
# ---------------------------------------------------------

last_sensor_message = 0
last_controller_message = 0
last_power_message = 0


# ---------------------------------------------------------
# Fault logging
# ---------------------------------------------------------

fault_log = []


def log_fault(fault):

    timestamp = datetime.now().strftime(
        "%H:%M:%S"
    )

    entry = f"{timestamp} - {fault}"

    fault_log.append(entry)

    print("\n" + "!" * 60)

    print("DIAGNOSTIC FAULT")

    print("!" * 60)

    print(f"Timestamp : {timestamp}")
    print(f"Fault     : {fault}")

    print("!" * 60 + "\n")


# ---------------------------------------------------------
# Monitor CAN messages
# ---------------------------------------------------------

while True:

    message = bus.recv(timeout=0.1)

    current_time = time.time()


    # -----------------------------------------------------
    # Process received message
    # -----------------------------------------------------

    if message is not None:

        # -----------------------------------------------
        # Sensor ECU messages
        # -----------------------------------------------

        if message.arbitration_id == 0x100:

            last_sensor_message = current_time


        elif message.arbitration_id == 0x101:

            last_sensor_message = current_time

            # Decode Cell 4
            cell4_raw = (
                (message.data[0] << 8)
                | message.data[1]
            )

            cell4 = cell4_raw / 100.0

            # Decode temperature
            temperature = message.data[2] - 40

            # Decode current
            current = message.data[3] - 100


            # -------------------------------------------
            # Sensor validation
            # -------------------------------------------

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


        # -----------------------------------------------
        # BMS Controller message
        # -----------------------------------------------

        elif message.arbitration_id == 0x200:

            last_controller_message = current_time


        # -----------------------------------------------
        # Power Control ECU heartbeat
        # -----------------------------------------------

        elif message.arbitration_id == 0x300:

            last_power_message = current_time


    # -----------------------------------------------------
    # Check for ECU timeouts
    # -----------------------------------------------------

    # Sensor ECU timeout
    if (
        last_sensor_message != 0
        and current_time - last_sensor_message > 3
    ):

        log_fault(
            "Sensor ECU timeout"
        )

        last_sensor_message = current_time


    # Controller ECU timeout
    if (
        last_controller_message != 0
        and current_time - last_controller_message > 3
    ):

        log_fault(
            "BMS Controller ECU timeout"
        )

        last_controller_message = current_time


    # Power Control ECU timeout
    if (
        last_power_message != 0
        and current_time - last_power_message > 3
    ):

        log_fault(
            "Power Control ECU timeout"
        )

        last_power_message = current_time


    # -----------------------------------------------------
    # Display monitoring status
    # -----------------------------------------------------

    print(
        f"\rMonitoring CAN network | "
        f"Sensor: {'OK' if last_sensor_message and current_time-last_sensor_message < 3 else 'WAIT'} | "
        f"Controller: {'OK' if last_controller_message and current_time-last_controller_message < 3 else 'WAIT'} | "
        f"Power: {'OK' if last_power_message and current_time-last_power_message < 3 else 'WAIT'}",
        end="",
        flush=True
    )
