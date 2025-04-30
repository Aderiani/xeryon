import RPi.GPIO as GPIO
import time

# Set GPIO mode to BCM numbering
GPIO.setmode(GPIO.BCM)

# Set GPIO 17 as output
GPIO.setup(17, GPIO.OUT)

try:
    while True:
        # Toggle GPIO 17 high
        GPIO.output(17, GPIO.HIGH)
        time.sleep(1)
        
        # Toggle GPIO 17 low
        GPIO.output(17, GPIO.LOW)
        time.sleep(1)

except KeyboardInterrupt:
    # Clean up GPIO on program exit
    print("\nProgram stopped by user")
    GPIO.cleanup()