import pybullet as p
import pybullet_data
import serial
import time
import math
import tempfile
import os

COM_PORT = "COM10"    
BAUDRATE = 115200
SERIAL_TIMEOUT = 0.5

ADC_MAX = 4095.0
DEG_MIN = -90.0
DEG_MAX = 90.0

# Segment lengths (meters)
L0 = 0.25   # seg0 length
L1 = 0.25   # seg1 length
L2 = 0.25   # seg2 length

# Visual dimensions (thickness)
HEIGHT = 0.03
WIDTH  = 0.04

# PyBullet simulation rate
TIMESTEP = 1.0 / 240.0

def write_urdf(path):
    urdf = f"""<?xml version="1.0" ?>
<robot name="three_segment_arm">
  <!-- base (seg0) -->
  <link name="base_link">
    <visual>
      <origin xyz="{L0/2} 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="{L0} {WIDTH} {HEIGHT}"/>
      </geometry>
      <material name="gray"><color rgba="0.6 0.6 0.6 1"/></material>
    </visual>
    <inertial>
      <origin xyz="{L0/2} 0 0" rpy="0 0 0"/>
      <mass value="0.0"/>
      <inertia ixx="0.0" ixy="0.0" ixz="0.0" iyy="0.0" iyz="0.0" izz="0.0"/>
    </inertial>
  </link>

  <!-- seg1 -->
  <link name="link1">
    <visual>
      <origin xyz="{L1/2} 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="{L1} {WIDTH} {HEIGHT}"/>
      </geometry>
      <material name="blue"><color rgba="0.2 0.4 1 1"/></material>
    </visual>
    <inertial>
      <origin xyz="{L1/2} 0 0"/>
      <mass value="0.5"/>
      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>
    </inertial>
  </link>

  <!-- seg2 -->
  <link name="link2">
    <visual>
      <origin xyz="{L2/2} 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="{L2} {10*WIDTH} {HEIGHT}"/>
      </geometry>
      <material name="green"><color rgba="0.2 1 0.2 1"/></material>
    </visual>
    <inertial>
      <origin xyz="{L2/2} 0 0"/>
      <mass value="0.4"/>
      <inertia ixx="0.0008" ixy="0.0" ixz="0.0" iyy="0.0008" iyz="0.0" izz="0.0008"/>
    </inertial>
  </link>

  <!-- joint between base and link1 at x = L0 -->
  <joint name="joint1" type="revolute">
    <parent link="base_link"/>
    <child link="link1"/>
    <origin xyz="{L0} 0 0" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit effort="10.0" lower="-1.57079632679" upper="1.57079632679" velocity="5.0"/>
  </joint>

  <!-- joint between link1 and link2 at x = L0 + L1 -->
  <joint name="joint2" type="revolute">
    <parent link="link1"/>
    <child link="link2"/>
    <origin xyz="{L1} 0 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <limit effort="10.0" lower="-1.57079632679" upper="1.57079632679" velocity="5.0"/>
  </joint>
</robot>
"""
    with open(path, "w") as f:
        f.write(urdf)

def adc_to_radians(adc):
    """Map adc (0..ADC_MAX) to radians (-90..90 deg)."""
    ratio = max(0.0, min(1.0, adc / ADC_MAX))
    deg = DEG_MIN + ratio * (DEG_MAX - DEG_MIN)
    return math.radians(deg)

def main():
    # tmpdir = tempfile.gettempdir()
    urdf_path = os.path.join("three_segment_arm.urdf")
    write_urdf(urdf_path)

    # Connect to PyBullet GUI
    physics_client = p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.resetSimulation()
    # p.setGravity(0, 0, -9.81)
    p.setTimeStep(TIMESTEP)
    # p.loadURDF("plane.urdf")

    # Position the camera for a good view
    p.resetDebugVisualizerCamera(cameraDistance=1.0, cameraYaw=0, cameraPitch=-89,
                                 cameraTargetPosition=[L0*2, 0, 0])  #L0 + L1/2

    # Load the arm URDF. base position anchors the base_link origin at world origin.
    start_pos = [0, 0, 0.02]
    arm_id = p.loadURDF("three_segment_arm.urdf", basePosition=start_pos, useFixedBase=True)

    # Joints: expect joint indices 0 and 1 maps to joint1 and joint2
    n_joints = p.getNumJoints(arm_id)
    print("Loaded arm id", arm_id, "num joints", n_joints)
    for i in range(n_joints):
        info = p.getJointInfo(arm_id, i)
        print(" joint", i, info[1].decode(), "type", info[2], "limits", info[8], info[9])

    # Initialize joint state
    p.resetJointState(arm_id, 0, targetValue=0.0)  # joint1
    p.resetJointState(arm_id, 1, targetValue=0.0)  # joint2

    # Open serial
    ser = None
    try:
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT)
        time.sleep(2.0)  # wait for ESP32 reset on open
        print(f"Opened serial port {COM_PORT} at {BAUDRATE} baud.")
    except Exception as e:
        print(f"Warning: Could not open serial port {COM_PORT}: {e}")
        print("You can still run simulation; ADC values will remain 0 until serial is available.")

    # State for latest ADCs
    adc1 = 0
    adc2 = 0

    # Disable built-in motors and enable position control later:
    p.setJointMotorControlArray(arm_id, [0,1], p.VELOCITY_CONTROL, forces=[0,0])

    print("Starting simulation loop. Press Ctrl+C to stop.")
    try:
        while True:
            # Read from serial if available
            if ser is not None and ser.is_open:
                try:
                    raw = ser.readline()
                except Exception:
                    raw = b""
                if raw:
                    try:
                        line = raw.decode('utf-8', errors='ignore').strip()
                    except Exception:
                        line = ""
                    if line:
                        first = line[0]
                        payload = line[1:].strip()
                        if first == '1':
                            try:
                                val = int(payload)
                                val = max(0, min(int(ADC_MAX), val))
                                adc1 = val
                            except:
                                pass
                        elif first == '2':
                            try:
                                val = int(payload)
                                val = max(0, min(int(ADC_MAX), val))
                                adc2 = val
                            except:
                                pass
            # Map ADCs to joint target angles (radians)
            target1 = adc_to_radians(adc1)
            target2 = adc_to_radians(adc2)

            # Apply position control to joints 0 and 1
            p.setJointMotorControl2(bodyUniqueId=arm_id,
                                    jointIndex=0,
                                    controlMode=p.POSITION_CONTROL,
                                    targetPosition=target1,
                                    force=10.0,
                                    maxVelocity=5.0)

            p.setJointMotorControl2(bodyUniqueId=arm_id,
                                    jointIndex=1,
                                    controlMode=p.POSITION_CONTROL,
                                    targetPosition=target2,
                                    force=10.0,
                                    maxVelocity=5.0)

            # Step simulation and sleep to limit CPU
            p.stepSimulation()
            time.sleep(TIMESTEP)

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received: exiting...")

    finally:
        # Close serial cleanly
        if ser is not None:
            try:
                if ser.is_open:
                    ser.close()
                    print("Serial port closed.")
            except Exception as e:
                print("Error closing serial:", e)

        # Disconnect PyBullet
        p.disconnect()
        print("PyBullet disconnected. Exiting.")

if __name__ == "__main__":
    main()
