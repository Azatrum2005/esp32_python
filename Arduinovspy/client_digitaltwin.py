# import websockets
# import asyncio
# import json
# import pybullet as p
# import pybullet_data
# import numpy as np
# import time

# # --- CONFIGURATION ---
# PHONE_IP = "192.168.70.149"  # <--- REPLACE WITH YOUR PHONE'S IP (Check 'ifconfig' in Termux)
# PHONE_PORT = 8765
# # ---------------------

# class PhoneWebSocketClient:
#     def __init__(self, uri):
#         self.uri = uri
#         self.websocket = None
#         self.running = True
        
#         self.lock = asyncio.Lock()
        
#         # IMU data
#         self.ax = 0.0  # acceleration in g
#         self.ay = 0.0
#         self.gz = 0.0  # angular velocity in deg/s
        
#         # Integration state
#         self.vx = 0.0  # velocity in m/s
#         self.vy = 0.0
#         self.x = 0.0   # position in m
#         self.y = 0.0
#         self.yaw = 0.0  # orientation in radians
#         self.last_update_time = None
        
#         # IMU calibration/bias
#         self.ax_bias = 0.0 
#         self.ay_bias = 0.0 
#         self.gz_bias = 0.0 
        
#         # Calibration mode
#         self.calibration_samples = []
#         self.is_calibrated = False
        
#         # PyBullet setup
#         self.physics_client = None
#         self.bot_id = None
#         self.walls = []
#         self.init_pybullet()
        
#     def init_pybullet(self):
#         """Initialize PyBullet simulation"""
#         self.physics_client = p.connect(p.GUI)
#         p.setAdditionalSearchPath(pybullet_data.getDataPath())
#         p.setGravity(0, 0, 0)  # No gravity - we're controlling it manually
        
#         # Load plane
#         p.loadURDF("plane.urdf")
        
#         # Create simple box robot to represent the phone
#         bot_size = [0.1, 0.2, 0.01]  # Thin phone shape
#         collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=bot_size)
#         visual_shape = p.createVisualShape(
#             p.GEOM_BOX, 
#             halfExtents=bot_size,
#             rgbaColor=[0.2, 0.5, 0.8, 1.0]
#         )
        
#         self.bot_id = p.createMultiBody(
#             baseMass=1.0,
#             baseCollisionShapeIndex=collision_shape,
#             baseVisualShapeIndex=visual_shape,
#             basePosition=[0, 0, 0.15]
#         )
        
#         # Create walls
#         wall_height = 0.5
#         wall_thickness = 0.1
#         arena_size = 5.0
        
#         wall_configs = [
#             [arena_size/2, 0, wall_thickness, arena_size],      # Right
#             [-arena_size/2, 0, wall_thickness, arena_size],     # Left
#             [0, arena_size/2, arena_size, wall_thickness],      # Front
#             [0, -arena_size/2, arena_size, wall_thickness]      # Back
#         ]
        
#         for x, y, length, width in wall_configs:
#             wall_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[length/2, width/2, wall_height/2])
#             wall_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=[length/2, width/2, wall_height/2], rgbaColor=[0.7, 0.7, 0.7, 1.0])
#             p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_shape, baseVisualShapeIndex=wall_visual, basePosition=[x, y, wall_height/2])
        
#         p.resetDebugVisualizerCamera(cameraDistance=6.0, cameraYaw=0, cameraPitch=-80, cameraTargetPosition=[0, 0, 0])
        
#         # Disable damping completely - we handle physics ourselves
#         p.changeDynamics(self.bot_id, -1, linearDamping=0.0, angularDamping=0.0)
        
#     async def connect(self):
#         print(f"Connecting to Phone at {self.uri}...")
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to Samsung A22!")
    
#     async def receive_loop(self):
#         """Receive sensor data"""
#         try:
#             while self.running:
#                 message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
#                 data = json.loads(message)
                
#                 async with self.lock:
#                     self.ax = data.get("ax", 0.0)
#                     self.ay = data.get("ay", 0.0)
#                     self.gz = data.get("gz", 0.0)
                    
#                     # Calibration logic
#                     if not self.is_calibrated:
#                         print(f"Calibrating... {len(self.calibration_samples)}/100 (Keep phone still!)")
#                         self.calibration_samples.append({'ax': self.ax, 'ay': self.ay, 'gz': self.gz})
                        
#                         if len(self.calibration_samples) >= 100:
#                             self.ax_bias = np.mean([s['ax'] for s in self.calibration_samples])
#                             self.ay_bias = np.mean([s['ay'] for s in self.calibration_samples])
#                             self.gz_bias = np.mean([s['gz'] for s in self.calibration_samples])
#                             self.is_calibrated = True
#                             print(f"\n=== CALIBRATED ===")
#                             print(f"Bias: ax={self.ax_bias:.3f}, ay={self.ay_bias:.3f}, gz={self.gz_bias:.3f}")
#                             print("==================\n")

#         except asyncio.TimeoutError:
#             print("No data received from phone (Timeout)")
#         except websockets.exceptions.ConnectionClosed:
#             print("Phone disconnected")
#             self.running = False
    
#     async def simulation_loop(self):
#         """Update PyBullet simulation with direct velocity control"""
#         try:
#             self.last_update_time = time.time()
            
#             while self.running:
#                 if not self.is_calibrated:
#                     await asyncio.sleep(0.05)
#                     p.stepSimulation()
#                     continue
                
#                 current_time = time.time()
#                 dt = current_time - self.last_update_time
#                 self.last_update_time = current_time
#                 dt = min(dt, 0.05)  # Clamp dt to prevent huge jumps
                
#                 async with self.lock:
#                     # Apply bias correction
#                     ax_corrected = self.ax - self.ax_bias
#                     ay_corrected = self.ay - self.ay_bias
#                     gz_corrected = self.gz - self.gz_bias
                
#                 # Convert to simulation units
#                 ax_ms2 = ax_corrected * 9.81
#                 ay_ms2 = ay_corrected * 9.81
#                 gz_rads = np.radians(gz_corrected)
                
#                 # Deadzones (reduce these for more sensitivity)
#                 deadzone_accel = 0.001  # Reduced from 0.02
#                 deadzone_gyro = 0.002   # Reduced from 0.05
                
#                 if abs(ax_corrected) < deadzone_accel: ax_ms2 = 0.0
#                 if abs(ay_corrected) < deadzone_accel: ay_ms2 = 0.0
#                 if abs(gz_corrected) < deadzone_gyro: gz_rads = 0.0
                
#                 # Update Yaw
#                 self.yaw += gz_rads * dt
#                 self.yaw = np.arctan2(np.sin(self.yaw), np.cos(self.yaw))
                
#                 # Transform acceleration to world frame
#                 ax_world = ax_ms2 * np.cos(self.yaw) - ay_ms2 * np.sin(self.yaw)
#                 ay_world = ax_ms2 * np.sin(self.yaw) + ay_ms2 * np.cos(self.yaw)
                
#                 # Update Velocity (with higher gain for more movement)
#                 gain = 1.0  # Increase this to make it more responsive
#                 self.vx += ax_world * dt * gain
#                 self.vy += ay_world * dt * gain
                
#                 # Damping (less aggressive)
#                 self.vx *= 0.98  # Changed from 0.95
#                 self.vy *= 0.98
                
#                 # Update Position
#                 self.x += self.vx * dt
#                 self.y += self.vy * dt
                
#                 # Wall collisions
#                 max_pos = 2.4
#                 if abs(self.x) > max_pos:
#                     self.x = np.sign(self.x) * max_pos
#                     self.vx = -self.vx * 0.3  # Bounce back
                    
#                 if abs(self.y) > max_pos:
#                     self.y = np.sign(self.y) * max_pos
#                     self.vy = -self.vy * 0.3  # Bounce back
                
#                 # Update PyBullet visualization
#                 new_orn = p.getQuaternionFromEuler([0, 0, self.yaw])
                
#                 # Set velocity for smooth visual motion
#                 p.resetBaseVelocity(
#                     self.bot_id,
#                     linearVelocity=[self.vx, self.vy, 0],
#                     angularVelocity=[0, 0, gz_rads]
#                 ) 
                
#                 # Set position and orientation directly
#                 p.resetBasePositionAndOrientation(
#                     self.bot_id, 
#                     [self.x, self.y, 0.0], 
#                     new_orn
#                 )
                
#                 # Print debug info occasionally
#                 if int(current_time * 2) % 10 == 0:  # Every 5 seconds
#                     print(f"Pos: ({self.x:.2f}, {self.y:.2f}) | Vel: ({self.vx:.2f}, {self.vy:.2f}) | Accel: ({ax_corrected:.2f}, {ay_corrected:.2f})")
                
#                 p.stepSimulation()
#                 await asyncio.sleep(1./240.)
                
#         except asyncio.CancelledError:
#             pass
    
#     async def close(self):
#         self.running = False
#         if self.websocket:
#             await self.websocket.close()
#         if self.physics_client is not None:
#             p.disconnect()
#         print("Simulation closed")

# async def main():
#     # Connect to the Phone Server
#     client = PhoneWebSocketClient(f"ws://{PHONE_IP}:{PHONE_PORT}")

#     await client.connect()
#     recv_task = asyncio.create_task(client.receive_loop())
#     sim_task = asyncio.create_task(client.simulation_loop())

#     try:
#         await asyncio.gather(recv_task, sim_task)
#     except OSError:
#         print(f"Error: Could not connect to {PHONE_IP}:{PHONE_PORT}")
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         await client.close()

# if __name__ == "__main__":
#     asyncio.run(main())

############################################################################################################

import websockets
import asyncio
import json
import pybullet as p
import pybullet_data
import numpy as np
import time

PHONE_IP = "10.30.75.221"  
PHONE_PORT = 8765

class PhoneWebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.running = True
        
        self.lock = asyncio.Lock()
        
        # IMU data
        self.ax = 0.0  # acceleration in g (with gravity)
        self.ay = 0.0
        self.gz = 0.0  # angular velocity in deg/s
        
        # Gravity data
        self.gx = 0.0  # gravity components in g
        self.gy = 0.0
        self.gz_grav = 0.0
        
        # Integration state
        self.vx = 0.0  # velocity in m/s
        self.vy = 0.0
        self.x = 0.0   # position in m
        self.y = 0.0
        self.yaw = 0.0  # orientation in radians
        self.last_update_time = None
        
        # IMU calibration/bias (now for LINEAR acceleration)
        self.ax_bias = 0.0 
        self.ay_bias = 0.0 
        self.gz_bias = 0.0 
        
        # Calibration mode
        self.calibration_samples = []
        self.is_calibrated = False
        
        # PyBullet setup
        self.physics_client = None
        self.bot_id = None
        self.walls = []
        self.init_pybullet()
        
    def init_pybullet(self):
        """Initialize PyBullet simulation"""
        self.physics_client = p.connect(p.GUI)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, 0)  # No gravity - we're controlling it manually
        
        # Load plane
        p.loadURDF("plane.urdf")
        
        # Create simple box robot to represent the phone
        bot_size = [0.1, 0.2, 0.01]  # Thin phone shape
        collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=bot_size)
        visual_shape = p.createVisualShape(
            p.GEOM_BOX, 
            halfExtents=bot_size,
            rgbaColor=[0.2, 0.5, 0.8, 1.0]
        )
        
        self.bot_id = p.createMultiBody(
            baseMass=0.5,
            baseCollisionShapeIndex=collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=[0, 0, 0.0]
        )
        
        # Create walls
        wall_height = 0.5
        wall_thickness = 0.1
        arena_size = 5.0
        
        wall_configs = [
            [arena_size/2, 0, wall_thickness, arena_size],      # Right
            [-arena_size/2, 0, wall_thickness, arena_size],     # Left
            [0, arena_size/2, arena_size, wall_thickness],      # Front
            [0, -arena_size/2, arena_size, wall_thickness]      # Back
        ]
        
        for x, y, length, width in wall_configs:
            wall_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=[length/2, width/2, wall_height/2])
            wall_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=[length/2, width/2, wall_height/2], rgbaColor=[0.7, 0.7, 0.7, 1.0])
            p.createMultiBody(baseMass=0, baseCollisionShapeIndex=wall_shape, baseVisualShapeIndex=wall_visual, basePosition=[x, y, wall_height/2])
        
        p.resetDebugVisualizerCamera(cameraDistance=6.0, cameraYaw=0, cameraPitch=-80, cameraTargetPosition=[0, 0, 0])
        
        # Disable damping completely - we handle physics ourselves
        p.changeDynamics(self.bot_id, -1, linearDamping=0.1, angularDamping=0.1)
        
    async def connect(self):
        print(f"Connecting to Phone at {self.uri}...")
        self.websocket = await websockets.connect(self.uri)
        print("Connected")
    
    async def receive_loop(self):
        """Receive sensor data"""
        try:
            while self.running:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                data = json.loads(message)
                
                async with self.lock:
                    self.ax = data.get("ax", 0.0)
                    self.ay = data.get("ay", 0.0)
                    self.gz = data.get("gz", 0.0)
                    
                    # Get gravity components
                    self.gx = data.get("gx", 0.0)
                    self.gy = data.get("gy", 0.0)
                    self.gz_grav = data.get("gz_grav", 0.0)
                    
                    # Calibration logic (now calibrate LINEAR acceleration)
                    if not self.is_calibrated:
                        # Remove gravity to get linear acceleration
                        linear_ax = self.ax - self.gx
                        linear_ay = self.ay - self.gy
                        
                        print(f"Calibrating... {len(self.calibration_samples)}/100 (Keep phone still!)")
                        self.calibration_samples.append({
                            'ax': linear_ax, 
                            'ay': linear_ay, 
                            'gz': self.gz
                        })
                        
                        if len(self.calibration_samples) >= 100:
                            self.ax_bias = np.mean([s['ax'] for s in self.calibration_samples])
                            self.ay_bias = np.mean([s['ay'] for s in self.calibration_samples])
                            self.gz_bias = np.mean([s['gz'] for s in self.calibration_samples])
                            self.is_calibrated = True
                            print(f"\n=== CALIBRATED ===")
                            print(f"Linear Accel Bias: ax={self.ax_bias:.4f}, ay={self.ay_bias:.4f}")
                            print(f"Gyro Bias: gz={self.gz_bias:.3f}")
                            print("==================\n")

        except asyncio.TimeoutError:
            print("No data received from phone (Timeout)")
        except websockets.exceptions.ConnectionClosed:
            print("Phone disconnected")
            self.running = False
    
    async def simulation_loop(self):
        """Update PyBullet simulation with gravity-compensated acceleration"""
        try:
            self.last_update_time = time.time()
            
            while self.running:
                if not self.is_calibrated:
                    await asyncio.sleep(0.05)
                    p.stepSimulation()
                    continue
                
                current_time = time.time()
                dt = current_time - self.last_update_time
                self.last_update_time = current_time
                dt = min(dt, 0.05)  # Clamp dt to prevent huge jumps
                
                async with self.lock:
                    # CRITICAL: Remove gravity from accelerometer to get LINEAR acceleration
                    linear_ax = self.ax - self.gx
                    linear_ay = self.ay - self.gy
                    
                    # Apply bias correction to linear acceleration
                    ax_corrected = linear_ax - self.ax_bias
                    ay_corrected = linear_ay - self.ay_bias
                    gz_corrected = self.gz - self.gz_bias
                
                # Convert to simulation units (m/s²)
                ax_ms2 = ax_corrected * 9.81
                ay_ms2 = ay_corrected * 9.81
                gz_rads = np.radians(gz_corrected)
                
                # Deadzones
                deadzone_accel = 0.001
                deadzone_gyro = 0.01
                
                if abs(ax_corrected) < deadzone_accel: ax_ms2 = 0.0
                if abs(ay_corrected) < deadzone_accel: ay_ms2 = 0.0
                if abs(gz_corrected) < deadzone_gyro: gz_rads = 0.0
                
                # Update Yaw
                self.yaw += gz_rads * dt
                self.yaw = np.arctan2(np.sin(self.yaw), np.cos(self.yaw))
                
                # Transform acceleration to world frame
                ax_world = ax_ms2 * np.cos(self.yaw) - ay_ms2 * np.sin(self.yaw)
                ay_world = ax_ms2 * np.sin(self.yaw) + ay_ms2 * np.cos(self.yaw)
                
                # Update Velocity with gain
                gain = 1.0  # Adjust for responsiveness
                self.vx += ax_world * dt * gain
                self.vy += ay_world * dt * gain
                
                # Damping
                self.vx *= 0.99
                self.vy *= 0.99
                
                # Update Position
                self.x += self.vx * dt
                self.y += self.vy * dt
                
                # Wall collisions
                max_pos = 2.4
                if abs(self.x) > max_pos:
                    self.x = np.sign(self.x) * max_pos
                    self.vx = -self.vx * 0.3
                    
                if abs(self.y) > max_pos:
                    self.y = np.sign(self.y) * max_pos
                    self.vy = -self.vy * 0.3
                
                # Update PyBullet visualization
                new_orn = p.getQuaternionFromEuler([0, 0, self.yaw])
                
                p.resetBasePositionAndOrientation(
                    self.bot_id, 
                    [self.x, self.y, 0.0], 
                    new_orn
                )
                
                p.resetBaseVelocity(
                    self.bot_id,
                    linearVelocity=[self.vx, self.vy, 0],
                    angularVelocity=[0, 0, gz_rads]
                )
                
                # Print debug info occasionally
                if int(current_time * 2) % 10 == 0:
                    print(f"Linear Accel: ({ax_corrected:.3f}, {ay_corrected:.3f})g | Vel: ({self.vx:.2f}, {self.vy:.2f})m/s | Pos: ({self.x:.2f}, {self.y:.2f})m")
                
                p.stepSimulation()
                await asyncio.sleep(1./240.)
                
        except asyncio.CancelledError:
            pass
    
    async def close(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
        if self.physics_client is not None:
            p.disconnect()
        print("Simulation closed")

async def main():
    client = PhoneWebSocketClient(f"ws://{PHONE_IP}:{PHONE_PORT}")

    await client.connect()
    recv_task = asyncio.create_task(client.receive_loop())
    sim_task = asyncio.create_task(client.simulation_loop())

    try:
        await asyncio.gather(recv_task, sim_task)
    except OSError:
        print(f"Error: Could not connect to {PHONE_IP}:{PHONE_PORT}")
    except KeyboardInterrupt:
        print("\nShutting down...")
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())