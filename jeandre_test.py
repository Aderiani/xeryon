import time
from Xeryon import *
import RPi.GPIO as GPIO




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
        self.axis.findIndex(True)

    def stop(self):
        self.controller.stop()

    def move_to(self, pos_mm):

        while self.axis.isErrorLimit():
            print(f"[{self.name}] ⚠️ Thermal protection triggered. Cooling down...")
            time.sleep(2)

        self.axis.sendCommand("ENBL=1")

        self.axis.setUnits(Units.mm)
        self.axis.setSpeed(20)
        self.axis.setDPOS(pos_mm)

        while not self.axis.isPositionReached():
            time.sleep(0.5)


        print(f"[{self.name}] ✅ Reached {pos_mm} mm with EPOS: {self.axis.getEPOS()} mm")



        errors = [msg for msg, chk in self.error_checks if chk()]
        if errors:
            print(f"\033[91m[{self.name}] Errors detected:\033[0m")
            for err in errors:
                print(f"\033[91m  - {err}\033[0m")
        else:
            print(f"[{self.name}] No errors detected.")
        print("=========================================")


##### SETUP #####

# Position parameters
Xin = 58      # X position for "in" position
Xin1 = Xin - 5
Xout = -45     # X position for "out" position
Zlow = 55     # Z position for "low" position
Zhigh = 28  # Z position for "high" position
Y0 = 55

try:
    # Instantiate three controllers
    z_axis = XAxisController("/dev/ttyACM0",Stage.XLA_1250_10N, "Z")
    y_axis = XAxisController("/dev/ttyACM1",  Stage.XLA_1250_10N, "Y")
    x_axis = XAxisController("/dev/ttyACM2", Stage.XLA_1250_10N, "X")
except Exception as e:
    # Sometimes when the actuators are reset but not the raspberry pi, the port numbers shifts!
    z_axis = XAxisController("/dev/ttyACM3",Stage.XLA_1250_10N, "Z")
    y_axis = XAxisController("/dev/ttyACM4",  Stage.XLA_1250_10N, "Y")
    x_axis = XAxisController("/dev/ttyACM5", Stage.XLA_1250_10N, "X")



def move_to_3d(x, y, z):
    print(f"🔄 Moving to 3D coordinate: ({x}, {y}, {z}) mm")
    # Start all moves in parallel (sequentially here, could be threaded if needed)
    x_axis.move_to(x)
    y_axis.move_to(y)
    z_axis.move_to(z)




def takefromdown_goout():
    # Go to Z low, X in
    move_to_3d(Xin, Y0, Zlow)
    # Grab the wellplate
    GPIO.output(17, GPIO.HIGH)
    # Go Back to Z low, X out
    move_to_3d(Xout, Y0, Zlow)
    time.sleep(2)

 



def gofromoutin():
    # Go back to Z high, X in
    move_to_3d(Xout, Y0, Zlow)
    # Grab the wellplate
    # Go Back to Z high, X out
    # Go to Z low, X out
    move_to_3d(Xin, Y0, Zlow)
    # Go to Z low, X in
    # Leave the wellplate
    GPIO.output(17, GPIO.LOW)
    # Go to Z low, X out



def setup_gpio():
    try:
        # Set GPIO mode to BCM numbering
        GPIO.setmode(GPIO.BCM)
        
        # Setup GPIO 23 as input with pull-up resistor
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Setup GPIO 17 as output for the actuator
        GPIO.setup(17, GPIO.OUT)
        # Make sure it's off at the start
        GPIO.output(17, GPIO.LOW)
        return True
    except Exception as e:
        print(f"Failed to setup GPIO: {e}")
        return False
def main():
    # Start all controllers
    for axis in [x_axis, y_axis, z_axis]:
        axis.start()

    # Initial position
    move_to_3d(Xout, Y0, Zlow)
    
    print("System ready. Press the button to start a cycle, or Ctrl+C to exit.")
    
    # Track the current state
    is_plate_up = False
    
    try:
        button_state = GPIO.input(23)
        last_state = button_state
        
        while True:
            button_state = GPIO.input(23)
            
            # Button press detected (remember pull-up means LOW is pressed)
            if button_state == GPIO.LOW and last_state == GPIO.HIGH:
                print("Button pressed - starting cycle!")
                
                if not is_plate_up:
                    print("Moving plate from down to up...")
                    takefromdown_goout()
                    is_plate_up = True
                else:
                    print("Moving plate from up to down...")
                    gofromoutin()
                    is_plate_up = False
                    
                time.sleep(0.2)  # Debounce delay
            
            last_state = button_state
            time.sleep(0.05)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        # Cleanup GPIO
        GPIO.cleanup()
        print("GPIO cleaned up.")
        # Cleanup all controllers
        for axis in [x_axis, y_axis, z_axis]:
            axis.stop()
        print("Controllers cleaned up.")

if __name__ == "__main__":
    setup_gpio()
    main()
    GPIO.cleanup()






