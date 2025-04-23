import time
from Xeryon import *
from matplotlib import pyplot as plt

# 1. Setup
controller = Xeryon("COM4", 115200)           # Setup serial communication
axisX = controller.addAxis(Stage.XLA_1250_10N, "X") # Add axis with specified stage

# Error conditions to check
error_checks = [
    ("Force is Zero", axisX.isForceZero),
    ("Position Fail is triggered", axisX.isPositionFailTriggered),
    ("Error limit is reached", axisX.isErrorLimit),
    ("Encoder Error limit is reached", axisX.isEncoderError),
    ("Thermal protection 1", axisX.isThermalProtection1),
    ("Thermal protection 2", axisX.isThermalProtection2),
]

# Start the controller
controller.start()
axisX.findIndex()










# 4. Getting data back from the controller
def print_axis_status():
    print("Axis status:")
    print(f"  - Motor is on : {axisX.isMotorOn()}")  
    print(f"  - Force is Zero : {axisX.isForceZero()}")  
    print(f"  - The position is reached : {axisX.isPositionReached()}")
    print(f"  - The position Fail is trrigered : {axisX.isPositionFailTriggered()}")
    print(f"  - Encoder has reached at the index : {axisX.isEncoderAtIndex()}")
    print(f"  - Encoder is valid : {axisX.isEncoderValid()}")
    print(f"  - Searching for index : {axisX.isSearchingIndex()}")
    print(f"  - Scanning : {axisX.isScanning()}")
    print(f"  - Searching optimal frequency : {axisX.isSearchingOptimalFrequency()}")
    print(f"  - Error limit is reached: {axisX.isErrorLimit()}")
    print(f"  - Encoder Error limit is reached: {axisX.isEncoderError()}")
    print(f"  - Position reached: {axisX.isPositionReached()}")
    print(f"  - Thermal protection 1: {axisX.isThermalProtection1()}")
    print(f"  - Thermal protection 2: {axisX.isThermalProtection2()}")
    print(f"  - The Left End limit is reached: {axisX.isAtLeftEnd()}")
    print(f"  - The Right End limit is reached: {axisX.isAtRightEnd()}")



# Modified move_to_x function with error printing and plotting
def move_to_x(x_mm):
    print(f"Requested move to {x_mm} mm")
    
    # Safety check: Wait if thermal protection is active
    while axisX.isErrorLimit():
        print("⚠️  Thermal protection triggered. Cooling down...")
        time.sleep(2)  # Wait a bit before checking again

    # Re-enable the axis if needed
    axisX.sendCommand("ENBL=1")
    print("✅ Axis re-enabled after thermal check.")

    # Start logging
    axisX.startLogging()
    axisX.setUnits(Units.mm)
    axisX.setSpeed
    # Perform the move
    axisX.setDPOS(x_mm)
    
    # Wait until the desired position is reached
    while not axisX.isPositionReached():
        time.sleep(0.1)

    # End logging
    logs = axisX.endLogging()

    print(f"✅ Reached position {x_mm} mm with EPOS: {axisX.getEPOS()} mm")

    # Plot the logged data non-blocking
    unit_converted_epos = [axisX.convertEncoderUnitsToUnits(epos, axisX.units) for epos in logs["EPOS"]]
    plt.figure()
    plt.plot(unit_converted_epos)
    plt.ylabel('EPOS ('+str(axisX.units)+')')
    plt.xlabel("Sample")
    plt.title(f"Movement to {x_mm} mm")
    plt.show(block=False)

    # Check and print errors in red
    errors = [message for message, check in error_checks if check()]
    if errors:
        print("\033[91mErrors detected:\033[0m")
        for error in errors:
            print(f"\033[91m  - {error}\033[0m")
    else:
        print("No errors detected.")

    print("=========================================")

# Test movements
move_to_x(5)
move_to_x(20)
move_to_x(50)
move_to_x(0)
move_to_x(-50)

# Stop the controller
controller.stop()