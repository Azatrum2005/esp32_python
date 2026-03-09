from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from pynput import keyboard

print("Connecting...")
client = RemoteAPIClient()
sim = client.getObject('sim')

# 1. SETUP SYNCHRONOUS MODE (Crucial for Physics stability)
# This forces the simulator to wait for our Python command before advancing
client.setStepping(True)

box = sim.getObject('/MyBox')

# 2. TUNING PARAMETERS (Increase these if still stuck!)
MASS_MULTIPLIER = 5.0  # Multiplier to overcome friction (F = ma * multiplier)
KP_ROT = 5.0           # Torque power to correct rotation

# State
inputs = {'ax': 0.0, 'ay': 0.0, 'gyro_z': 0.0}

def on_press(key):
    try:
        if key.char == 'w': inputs['ax'] = 1.0
        if key.char == 's': inputs['ax'] = -1.0
        if key.char == 'a': inputs['gyro_z'] = 1.0
        if key.char == 'd': inputs['gyro_z'] = -1.0
    except AttributeError:
        pass

def on_release(key):
    if hasattr(key, 'char'):
        if key.char in ['w', 's']: inputs['ax'] = 0.0
        if key.char in ['a', 'd']: inputs['gyro_z'] = 0.0
    if key == keyboard.Key.esc:
        return False

# Start Simulation
sim.startSimulation()
print("Running. W/S to push, A/D to rotate. ESC to stop.")

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    while True:
        # Get physics state
        m = sim.getObjectMatrix(box, -1) # Returns [Xx, Xy, Xz, Px, Yx, Yy, Yz, Py, ...]
        lin_vel, ang_vel = sim.getObjectVelocity(box)
        
        # --- 1. CALCULATE FORCES (Corrected Math) ---
        # We want to push "Forward" relative to the box.
        # Box X-axis vector is (m[0], m[1], m[2])
        # Force_World_X = Input_Forward * Box_X_Axis_X
        # Force_World_Y = Input_Forward * Box_X_Axis_Y
        
        fx = (inputs['ax'] * m[0]) * MASS_MULTIPLIER
        fy = (inputs['ax'] * m[1]) * MASS_MULTIPLIER
        
        # --- 2. CALCULATE TORQUE (Stabilized) ---
        # Error = Target_Gyro - Current_Gyro
        error = inputs['gyro_z'] - ang_vel[2]
        torque_z = -error * KP_ROT

        # --- 3. APPLY & STEP ---
        # Apply force at the center of the object
        sim.addForceAndTorque(box, [fx, fy, 0], [0, 0, torque_z])
        
        # Advance the simulation by exactly one step (usually 50ms)
        client.step()
        
        # Check if user stopped sim from UI
        if sim.getSimulationState() == sim.simulation_stopped:
            break

except KeyboardInterrupt:
    pass
finally:
    sim.stopSimulation()
    listener.stop()
    print("Ended.")