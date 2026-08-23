import can
import time
import threading


# ---------------------------------------------------------
# POWER CONTROL ECU
# ---------------------------------------------------------

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)


print("==============================================")
print("        POWER CONTROL ECU STARTED")
print("==============================================")
print("Waiting for control commands...\n")


# Current actuator states
charge_contactor = 0
discharge_contactor = 0
cooling_fan = 0
system_mode = 0


# ---------------------------------------------------------
# Send periodic heartbeat/status message
#
# CAN ID: 0x300
#
# Byte 0 = Charge contactor
# Byte 1 = Discharge contactor
# Byte 2 = Cooling fan
# Byte 3 = System mode
# ---------------------------------------------------------

def send_status():

    while True:

        message = can.Message(
            arbitration_id=0x300,
            data=[
                charge_contactor,
                discharge_contactor,
                cooling_fan,
                system_mode
            ],
            is_extended_id=False
        )

        try:

            bus.send(message)

        except can.CanError:

            print("ERROR: Failed to send status message")

        time.sleep(1)


# Start heartbeat thread
heartbeat_thread = threading.Thread(
    target=send_status,
    daemon=True
)

heartbeat_thread.start()


# ---------------------------------------------------------
# Main loop
# ---------------------------------------------------------

while True:

    message = bus.recv(timeout=1)

    if message is None:

        continue


    # -----------------------------------------------------
    # Receive command from BMS Controller
    #
    # CAN ID = 0x200
    # -----------------------------------------------------

    if message.arbitration_id == 0x200:

        charge_contactor = message.data[0]
        discharge_contactor = message.data[1]
        cooling_fan = message.data[2]
        system_mode = message.data[3]


        # Decode mode

        if system_mode == 0:

            mode_name = "IDLE"

        elif system_mode == 1:

            mode_name = "CHARGING"

        elif system_mode == 2:

            mode_name = "DISCHARGING"

        elif system_mode == 3:

            mode_name = "SAFE MODE"

        else:

            mode_name = "UNKNOWN"


        print("\n" + "=" * 55)

        print("         POWER CONTROL STATUS")

        print("=" * 55)

        print(
            f"System Mode        : {mode_name}"
        )

        print(
            f"Charge Contactor   : "
            f"{'ON' if charge_contactor else 'OFF'}"
        )

        print(
            f"Discharge Contactor: "
            f"{'ON' if discharge_contactor else 'OFF'}"
        )

        print(
            f"Cooling Fan        : "
            f"{'ON' if cooling_fan else 'OFF'}"
        )

        print("=" * 55)
