import can
import time
import threading

bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)

print("==============================================")
print("        POWER CONTROL ECU STARTED")
print("==============================================")
print("Waiting for control commands...\n")


charge_contactor = 0
discharge_contactor = 0
cooling_fan = 0
system_mode = 0
charging_enabled = 0
cooling_enabled = 0


def send_status_messages():

    while True:

        # =================================================
        # 0x300 - Power Control Status
        # =================================================

        msg300 = can.Message(
            arbitration_id=0x300,
            data=[
                charge_contactor,
                discharge_contactor,
                cooling_fan,
                system_mode
            ],
            is_extended_id=False
        )

        # =================================================
        # 0x301 - Contactor Status
        # =================================================

        msg301 = can.Message(
            arbitration_id=0x301,
            data=[
                charge_contactor,
                discharge_contactor,
                1
            ],
            is_extended_id=False
        )

        try:
            bus.send(msg300)
            bus.send(msg301)

        except can.CanError:
            print("ERROR: Failed to send status")

        time.sleep(1)


heartbeat_thread = threading.Thread(
    target=send_status_messages,
    daemon=True
)

heartbeat_thread.start()


while True:

    message = bus.recv(timeout=1)

    if message is None:
        continue

    # =====================================================
    # 0x200 - General Power Command
    # =====================================================

    if message.arbitration_id == 0x200:

        charge_contactor = message.data[0]
        discharge_contactor = message.data[1]
        cooling_fan = message.data[2]
        system_mode = message.data[3]

    # =====================================================
    # 0x201 - Charging Command
    # =====================================================

    elif message.arbitration_id == 0x201:

        charging_enabled = message.data[0]

    # =====================================================
    # 0x202 - Cooling Command
    # =====================================================

    elif message.arbitration_id == 0x202:

        cooling_enabled = message.data[0]

        if cooling_enabled:
            cooling_fan = 1

    # =====================================================
    # Display actuator state
    # =====================================================

    if message.arbitration_id in [0x200, 0x201, 0x202]:

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

        print(f"System Mode        : {mode_name}")

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

        print(
            f"Charging Command   : "
            f"{'ENABLED' if charging_enabled else 'DISABLED'}"
        )

        print("=" * 55)
