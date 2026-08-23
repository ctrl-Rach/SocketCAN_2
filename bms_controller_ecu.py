import can
import time

# ---------------------------------------------------------
# BMS CONTROLLER ECU
# ---------------------------------------------------------
# Responsibilities:
# 1. Receive battery sensor data
# 2. Decode cell voltages, temperature and current
# 3. Calculate battery voltage and SOC
# 4. Check battery safety conditions
# 5. Send control commands to Power Control ECU
# ---------------------------------------------------------


# Create SocketCAN interface
bus = can.Bus(
    interface="socketcan",
    channel="vcan0"
)


print("==============================================")
print("       BMS CONTROLLER ECU STARTED")
print("==============================================")
print("Waiting for battery sensor data...\n")


# ---------------------------------------------------------
# Latest sensor values
# ---------------------------------------------------------

cell1 = 0.0
cell2 = 0.0
cell3 = 0.0
cell4 = 0.0

temperature = 0.0
current = 0.0


# ---------------------------------------------------------
# SOC Calculation
# ---------------------------------------------------------

def calculate_soc(average_voltage):
    """
    Simple educational SOC estimation.

    3.60 V = 0% SOC
    4.20 V = 100% SOC
    """

    soc = ((average_voltage - 3.60) / 0.60) * 100

    # Keep SOC between 0 and 100
    soc = max(0, min(100, soc))

    return soc


# ---------------------------------------------------------
# Send control command to Power Control ECU
# CAN ID: 0x200
#
# Byte 0 = Charge Contactor
# Byte 1 = Discharge Contactor
# Byte 2 = Cooling Fan
# Byte 3 = System Mode
#
# Mode:
# 0 = IDLE
# 1 = CHARGING
# 2 = DISCHARGING
# 3 = SAFE MODE
# ---------------------------------------------------------

def send_control_command(charge, discharge, cooling, mode):

    message = can.Message(
        arbitration_id=0x200,
        data=[
            charge,
            discharge,
            cooling,
            mode
        ],
        is_extended_id=False
    )

    try:

        bus.send(message)

    except can.CanError:

        print("ERROR: Failed to send control command")


# ---------------------------------------------------------
# Main Loop
# ---------------------------------------------------------

while True:

    # Wait for CAN message
    message = bus.recv(timeout=1)

    # -----------------------------------------------------
    # No CAN message received
    # -----------------------------------------------------

    if message is None:

        print("WARNING: No CAN message received")

        continue


    # =====================================================
    # CAN ID 0x100
    #
    # Contains:
    # Cell 1 voltage
    # Cell 2 voltage
    # Cell 3 voltage
    # =====================================================

    if message.arbitration_id == 0x100:

        # Decode Cell 1
        cell1_raw = (
            (message.data[0] << 8)
            | message.data[1]
        )

        cell1 = cell1_raw / 100.0


        # Decode Cell 2
        cell2_raw = (
            (message.data[2] << 8)
            | message.data[3]
        )

        cell2 = cell2_raw / 100.0


        # Decode Cell 3
        cell3_raw = (
            (message.data[4] << 8)
            | message.data[5]
        )

        cell3 = cell3_raw / 100.0


    # =====================================================
    # CAN ID 0x101
    #
    # Contains:
    # Cell 4 voltage
    # Temperature
    # Current
    # =====================================================

    elif message.arbitration_id == 0x101:

        # Decode Cell 4
        cell4_raw = (
            (message.data[0] << 8)
            | message.data[1]
        )

        cell4 = cell4_raw / 100.0


        # Decode temperature
        #
        # Sensor ECU:
        # temperature + 40
        #
        # Controller:
        # received value - 40

        temperature = message.data[2] - 40


        # Decode current
        #
        # Sensor ECU:
        # current + 100
        #
        # Controller:
        # received value - 100

        current = message.data[3] - 100


        # =================================================
        # Calculate battery parameters
        # =================================================

        total_voltage = (
            cell1 +
            cell2 +
            cell3 +
            cell4
        )

        average_voltage = total_voltage / 4


        # Calculate SOC

        soc = calculate_soc(
            average_voltage
        )


        # =================================================
        # Battery Safety Checks
        # =================================================

        battery_status = "NORMAL"


        # Over-temperature
        if temperature > 50:

            battery_status = "OVERHEAT"


        # Low temperature
        elif temperature < 0:

            battery_status = "LOW TEMPERATURE"


        # Cell over-voltage
        elif any(
            cell > 4.20
            for cell in [cell1, cell2, cell3, cell4]
        ):

            battery_status = "OVERVOLTAGE"


        # Cell under-voltage
        elif any(
            cell < 3.00
            for cell in [cell1, cell2, cell3, cell4]
        ):

            battery_status = "UNDERVOLTAGE"


        # =================================================
        # Display Battery Information
        # =================================================

        print("\n" + "=" * 60)

        print("             BMS BATTERY STATUS")

        print("=" * 60)


        print(
            f"Cell 1 Voltage : {cell1:.2f} V"
        )

        print(
            f"Cell 2 Voltage : {cell2:.2f} V"
        )

        print(
            f"Cell 3 Voltage : {cell3:.2f} V"
        )

        print(
            f"Cell 4 Voltage : {cell4:.2f} V"
        )


        print("-" * 60)


        print(
            f"Battery Voltage : {total_voltage:.2f} V"
        )

        print(
            f"Average Voltage : {average_voltage:.2f} V"
        )

        print(
            f"Temperature     : {temperature:.1f} °C"
        )

        print(
            f"Current         : {current:.1f} A"
        )

        print(
            f"Estimated SOC   : {soc:.1f} %"
        )

        print(
            f"Battery Status  : {battery_status}"
        )


        # =================================================
        # Determine Power Control Command
        # =================================================

        if battery_status != "NORMAL":

            # ---------------------------------------------
            # Unsafe battery
            #
            # Charging OFF
            # Discharging OFF
            # Cooling ON
            # SAFE MODE
            # ---------------------------------------------

            send_control_command(
                charge=0,
                discharge=0,
                cooling=1,
                mode=3
            )

            print(
                "Operation       : SAFE MODE"
            )


        elif temperature > 40:

            # ---------------------------------------------
            # Battery temperature is getting high
            #
            # Charging OFF
            # Discharging OFF
            # Cooling ON
            # ---------------------------------------------

            send_control_command(
                charge=0,
                discharge=0,
                cooling=1,
                mode=3
            )

            print(
                "Operation       : COOLING"
            )


        elif current > 0:

            # ---------------------------------------------
            # Battery charging
            #
            # Charging ON
            # Discharging OFF
            # Cooling OFF
            # CHARGING MODE
            # ---------------------------------------------

            send_control_command(
                charge=1,
                discharge=0,
                cooling=0,
                mode=1
            )

            print(
                "Operation       : CHARGING"
            )


        elif current < 0:

            # ---------------------------------------------
            # Battery discharging
            #
            # Charging OFF
            # Discharging ON
            # Cooling OFF
            # DISCHARGING MODE
            # ---------------------------------------------

            send_control_command(
                charge=0,
                discharge=1,
                cooling=0,
                mode=2
            )

            print(
                "Operation       : DISCHARGING"
            )


        else:

            # ---------------------------------------------
            # Battery idle
            #
            # Everything OFF
            # IDLE MODE
            # ---------------------------------------------

            send_control_command(
                charge=0,
                discharge=0,
                cooling=0,
                mode=0
            )

            print(
                "Operation       : IDLE"
            )


        print("=" * 60)


        # Small delay
        time.sleep(0.1)
