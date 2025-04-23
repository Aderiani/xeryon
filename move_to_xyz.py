import time
from Xeryon import *
from matplotlib import pyplot as plt


class XAxisController:
    def __init__(self, port, stage, name):
        self.controller = Xeryon(port, 115200)
        self.axis = self.controller.addAxis(stage, name)
        self.name = name
        self.error_checks = [
            ("Force is Zero", self.axis.isForceZero),
            ("Position Fail is triggered", self.axis.isPositionFailTriggered),
            ("Error limit is reached", self.axis.isErrorLimit),
            ("Encoder Error limit is reached", self.axis.isEncoderError),
            ("Thermal protection 1", self.axis.isThermalProtection1),
            ("Thermal protection 2", self.axis.isThermalProtection2),
        ]

    def start(self):
        self.controller.start()
        self.axis.findIndex()

    def stop(self):
        self.controller.stop()

    def move_to(self, pos_mm):
        print(f"[{self.name}] Requested move to {pos_mm} mm")

        while self.axis.isErrorLimit():
            print(f"[{self.name}] ⚠️ Thermal protection triggered. Cooling down...")
            time.sleep(2)

        self.axis.sendCommand("ENBL=1")
        print(f"[{self.name}] ✅ Axis re-enabled.")

        self.axis.startLogging()
        self.axis.setUnits(Units.mm)
        self.axis.setDPOS(pos_mm)

        while not self.axis.isPositionReached():
            time.sleep(0.1)

        logs = self.axis.endLogging()

        print(f"[{self.name}] ✅ Reached {pos_mm} mm with EPOS: {self.axis.getEPOS()} mm")

        unit_converted_epos = [self.axis.convertEncoderUnitsToUnits(epos, self.axis.units) for epos in logs["EPOS"]]
        plt.figure()
        plt.plot(unit_converted_epos)
        plt.ylabel(f'EPOS ({self.axis.units})')
        plt.xlabel("Sample")
        plt.title(f"[{self.name}] Move to {pos_mm} mm")
        plt.show(block=False)

        errors = [msg for msg, chk in self.error_checks if chk()]
        if errors:
            print(f"\033[91m[{self.name}] Errors detected:\033[0m")
            for err in errors:
                print(f"\033[91m  - {err}\033[0m")
        else:
            print(f"[{self.name}] No errors detected.")
        print("=========================================")

# Instantiate three controllers
x_axis = XAxisController("COM4", Stage.XLA_1250_10N, "X")
y_axis = XAxisController("COM5", Stage.XLA_1250_10N, "Y")
z_axis = XAxisController("COM6", Stage.XLA_1250_10N, "Z")

# Start all controllers
for axis in [x_axis, y_axis, z_axis]:
    axis.start()

def move_to_3d(x, y, z):
    print(f"🔄 Moving to 3D coordinate: ({x}, {y}, {z}) mm")
    # Start all moves in parallel (sequentially here, could be threaded if needed)
    x_axis.move_to(x)
    y_axis.move_to(y)
    z_axis.move_to(z)
    print("✅ Move to 3D coordinate complete.")

# Example usage
move_to_3d(10, 20, 5)
move_to_3d(30, 0, -10)
move_to_3d(0, 0, 0)

# Stop all controllers
for axis in [x_axis, y_axis, z_axis]:
    axis.stop()


