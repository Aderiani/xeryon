import RPi.GPIO as GPIO
import time

def setup_gpio():
    try:
        # Set GPIO mode to BCM numbering
        GPIO.setmode(GPIO.BCM)
        
        # Setup GPIO 23 as input with pull-up resistor
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        return True
    except Exception as e:
        print(f"Failed to setup GPIO: {e}")
        return False

def main():
    print("Press the button (GPIO 23) to test. Press Ctrl+C to exit.")
    
    try:
        button_state = GPIO.input(23)
        last_state = button_state
        
        while True:
            button_state = GPIO.input(23)
            
            # Button press detected (remember pull-up means LOW is pressed)
            if button_state == GPIO.LOW and last_state == GPIO.HIGH:
                print("Button pressed!")
                time.sleep(0.2)  # Debounce delay
            
            last_state = button_state
            time.sleep(0.05)  # Small delay to prevent CPU hogging
            
    except KeyboardInterrupt:
        print("\nExiting program...")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up.")

if __name__ == "__main__":
    if setup_gpio():
        main()
    else:
        GPIO.cleanup()
        print("Failed to initialize GPIO")