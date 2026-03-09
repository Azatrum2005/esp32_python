from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from pynput import keyboard

# 1. Connect to CoppeliaSim
client = RemoteAPIClient()
sim = client.getObject('sim')

# 2. Get handles for the motors
left_motor = sim.getObject('/leftMotor')
right_motor = sim.getObject('/rightMotor')

# Speed settings
speed = 2.0  # Radian/sec

# 3. Define movement logic
def move_robot(left_val, right_val):
    sim.setJointTargetVelocity(left_motor, left_val)
    sim.setJointTargetVelocity(right_motor, right_val)

def on_press(key):
    try:
        if key.char == 'w': # Forward
            move_robot(speed, speed)
        elif key.char == 's': # Backward
            move_robot(-speed, -speed)
        elif key.char == 'a': # Left
            move_robot(-speed, speed)
        elif key.char == 'd': # Right
            move_robot(speed, -speed)
    except AttributeError:
        pass

def on_release(key):
    # Stop the robot when key is released
    move_robot(0, 0)
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# 4. Run the simulation
sim.startSimulation()
print("Control the robot with W, A, S, D. Press ESC to stop.")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

sim.stopSimulation()