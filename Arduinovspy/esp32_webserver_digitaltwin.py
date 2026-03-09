# import websockets
# import asyncio
# import json
# import time

# class ESP32WebSocketClient:
#     def __init__(self, uri="ws://192.168.1.100:81"):
#         self.uri = uri
#         self.websocket = None
#         self.running = True
        
#         self.speedL = 1500
#         self.speedR = 1500
#         self.lock = asyncio.Lock()

#     async def connect(self):
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to ESP32")

#     async def send_loop(self):
#         """Send motor commands at fixed rate"""
#         try:
#             while self.running:
#                 async with self.lock:
#                     message = {
#                         "action": "move",
#                         "speedL": self.speedL,
#                         "speedR": self.speedR
#                     }

#                 await self.websocket.send(json.dumps(message))
#                 await asyncio.sleep(0.02)  # 50 Hz
#         except asyncio.CancelledError:
#             pass

#     async def receive_loop(self):
#         """Receive sensor data"""
#         try:
#             while self.running:
#                 message = await asyncio.wait_for(
#                     self.websocket.recv(), timeout=0.1
#                 )
#                 data = json.loads(message)
#                 print(
#                     data["data"],
#                     "ax:", data["ax"],
#                     "ay:", data["ay"],
#                     "az:", data["az"],
#                     "gx:", data["gx"],
#                     "gy:", data["gy"],
#                     "gz:", data["gz"]
#                 )
#         except asyncio.TimeoutError:
#             pass
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed")

#     async def update_speed(self, speedL=None, speedR=None):
#         async with self.lock:
#             if speedL is not None:
#                 self.speedL = speedL
#             if speedR is not None:
#                 self.speedR = speedR

#     async def close(self):
#         self.running = False
#         await self.websocket.close()
#         print("WebSocket closed")

# async def main():
#     client = ESP32WebSocketClient()
#     await client.connect()

#     send_task = asyncio.create_task(client.send_loop())
#     recv_task = asyncio.create_task(client.receive_loop())

#     try:
#         await asyncio.gather(send_task, recv_task)
#     except KeyboardInterrupt:
#         await client.close()
#         send_task.cancel()
#         recv_task.cancel()

# if __name__ == "__main__":
#     asyncio.run(main())


########################################################################################################################################

# import asyncio
# import websockets
# import json
# import cv2

# STEP = 10
# MIN_SPEED = 1000
# MAX_SPEED = 2000

# class ESP32WebSocketClient:
#     def __init__(self, uri="ws://192.168.1.100:81"):
#         self.uri = uri
#         self.websocket = None
#         self.running = True

#         self.speedL = 1500
#         self.speedR = 1500
#         self.selected = "L"  # L or R

#         self.lock = asyncio.Lock()

#     async def connect(self):
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to ESP32")

#     async def send_loop(self):
#         try:
#             while self.running:
#                 async with self.lock:
#                     msg = {
#                         "action": "move",
#                         "speedL": self.speedL,
#                         "speedR": self.speedR
#                     }
#                 await self.websocket.send(json.dumps(msg))
#                 await asyncio.sleep(0.02)  # 50 Hz
#         except asyncio.CancelledError:
#             pass

#     async def receive_loop(self):
#         try:
#             while self.running:
#                 msg = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
#                 data = json.loads(msg)
#                 print("IMU:", data)
#         except asyncio.TimeoutError:
#             pass
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed")

#     async def keyboard_loop(self):
#         cv2.namedWindow("Control", cv2.WINDOW_NORMAL)
#         cv2.resizeWindow("Control", 400, 200)

#         while self.running:
#             img = self.render_ui()
#             cv2.imshow("Control", img)

#             key = cv2.waitKey(1) & 0xFF

#             async with self.lock:
#                 if key == ord("a"):      # LEFT
#                     self.selected = "L"
#                 elif key == ord("d"):    # RIGHT
#                     self.selected = "R"
#                 elif key == ord("w"):    # UP
#                     if self.selected == "L":
#                         self.speedL = min(self.speedL + STEP, MAX_SPEED)
#                     else:
#                         self.speedR = min(self.speedR + STEP, MAX_SPEED)
#                 elif key == ord("s"):    # DOWN
#                     if self.selected == "L":
#                         self.speedL = max(self.speedL - STEP, MIN_SPEED)
#                     else:
#                         self.speedR = max(self.speedR - STEP, MIN_SPEED)
#                 elif key == ord('q'):
#                     self.running = False
#                     break

#             await asyncio.sleep(0.01)

#         cv2.destroyAllWindows()

#     def render_ui(self):
#         import numpy as np
#         img = np.zeros((200, 400, 3), dtype=np.uint8)

#         colorL = (0, 255, 0) if self.selected == "L" else (200, 200, 200)
#         colorR = (0, 255, 0) if self.selected == "R" else (200, 200, 200)

#         cv2.putText(img, f"Speed L: {self.speedL}", (20, 70),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, colorL, 2)
#         cv2.putText(img, f"Speed R: {self.speedR}", (20, 120),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, colorR, 2)

#         cv2.putText(img, "a / d Select Motor", (20, 160),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
#         cv2.putText(img, "w / s Change Speed | q Quit", (20, 185),
#                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

#         return img

#     async def close(self):
#         self.running = False
#         await self.websocket.close()
#         print("WebSocket closed")

# async def main():
#     client = ESP32WebSocketClient()
#     await client.connect()

#     tasks = [
#         asyncio.create_task(client.send_loop()),
#         asyncio.create_task(client.receive_loop()),
#         asyncio.create_task(client.keyboard_loop())
#     ]

#     try:
#         await asyncio.gather(*tasks)
#     finally:
#         await client.close()
#         for t in tasks:
#             t.cancel()

# if __name__ == "__main__":
#     asyncio.run(main())


###############################################################################################################################################################

# import websockets
# import asyncio
# import json
# import pybullet as p
# import pybullet_data
# import numpy as np
# import time

# class ESP32WebSocketClient:
#     def __init__(self, uri="ws://192.168.1.100:81"):
#         self.uri = uri
#         self.websocket = None
#         self.running = True
        
#         self.speedL = 1500
#         self.speedR = 1500
#         self.lock = asyncio.Lock()
        
#         # IMU data
#         self.ax = 0.0  # acceleration in g
#         self.ay = 0.0
#         self.gz = 0.0  # angular velocity in deg/s
        
#         # PyBullet setup
#         self.physics_client = None
#         self.bot_id = None
#         self.walls = []
#         self.init_pybullet()
        
#     def init_pybullet(self):
#         """Initialize PyBullet simulation"""
#         self.physics_client = p.connect(p.GUI)
#         p.setAdditionalSearchPath(pybullet_data.getDataPath())
#         p.setGravity(0, 0, -9.81)
        
#         # Load plane
#         p.loadURDF("plane.urdf")
        
#         # Create simple box robot
#         bot_size = [0.2, 0.2, 0.1]  # length, width, height
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
#             basePosition=[0, 0, 0.05]
#         )
        
#         # Create walls around the origin (5m x 5m arena)
#         wall_height = 0.5
#         wall_thickness = 0.1
#         arena_size = 5.0
        
#         wall_configs = [
#             # [x, y, length, width]
#             [arena_size/2, 0, wall_thickness, arena_size],      # Right wall
#             [-arena_size/2, 0, wall_thickness, arena_size],     # Left wall
#             [0, arena_size/2, arena_size, wall_thickness],      # Front wall
#             [0, -arena_size/2, arena_size, wall_thickness]      # Back wall
#         ]
        
#         for x, y, length, width in wall_configs:
#             wall_shape = p.createCollisionShape(
#                 p.GEOM_BOX, 
#                 halfExtents=[length/2, width/2, wall_height/2]
#             )
#             wall_visual = p.createVisualShape(
#                 p.GEOM_BOX,
#                 halfExtents=[length/2, width/2, wall_height/2],
#                 rgbaColor=[0.7, 0.7, 0.7, 1.0]
#             )
#             wall_id = p.createMultiBody(
#                 baseMass=0,
#                 baseCollisionShapeIndex=wall_shape,
#                 baseVisualShapeIndex=wall_visual,
#                 basePosition=[x, y, wall_height/2]
#             )
#             self.walls.append(wall_id)
        
#         # Set camera
#         p.resetDebugVisualizerCamera(
#             cameraDistance=6.0,
#             cameraYaw=0,
#             cameraPitch=-89,
#             cameraTargetPosition=[0, 0, 0]
#         )
        
#         # Add velocity damping for more realistic movement
#         p.changeDynamics(self.bot_id, -1, linearDamping=0.0, angularDamping=0.0)
        
#     async def connect(self):
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to ESP32")
    
#     async def send_loop(self):
#         """Send motor commands at fixed rate"""
#         try:
#             while self.running:
#                 async with self.lock:
#                     message = {
#                         "action": "move",
#                         "speedL": self.speedL,
#                         "speedR": self.speedR
#                     }
#                 await self.websocket.send(json.dumps(message))
#                 await asyncio.sleep(0.02)  # 50 Hz
#         except asyncio.CancelledError:
#             pass
    
#     async def receive_loop(self):
#         """Receive sensor data"""
#         try:
#             while self.running:
#                 message = await asyncio.wait_for(
#                     self.websocket.recv(), timeout=0.1
#                 )
#                 data = json.loads(message)
                
#                 # Update IMU data
#                 async with self.lock:
#                     self.ax = data.get("ax", 0.0)
#                     self.ay = data.get("ay", 0.0)
#                     self.gz = data.get("gz", 0.0)
                
#                 print(
#                     data["data"],
#                     "ax:", data["ax"],
#                     "ay:", data["ay"],
#                     "az:", data["az"],
#                     "gx:", data["gx"],
#                     "gy:", data["gy"],
#                     "gz:", data["gz"]
#                 )
#         except asyncio.TimeoutError:
#             pass
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed")
#             self.running = False
    
#     async def simulation_loop(self):
#         """Update PyBullet simulation"""
#         try:
#             while self.running:
#                 async with self.lock:
#                     ax = self.ax
#                     ay = self.ay
#                     gz = self.gz
                
#                 # Update physics with current IMU values
#                 if self.bot_id is None:
#                     await asyncio.sleep(1./240.)
#                     continue
                
#                 # Get current bot state
#                 pos, orn = p.getBasePositionAndOrientation(self.bot_id)
#                 vel, ang_vel = p.getBaseVelocity(self.bot_id)
                
#                 # Convert orientation to Euler angles
#                 euler = p.getEulerFromQuaternion(orn)
#                 yaw = euler[2]
                
#                 # Convert accelerations from g to m/s²
#                 ax_ms2 = ax * 9.81
#                 ay_ms2 = ay * 9.81
                
#                 # Convert gz from deg/s to rad/s
#                 gz_rads = np.radians(gz)
                
#                 # Transform accelerations to world frame based on current yaw
#                 ax_world = ax_ms2 * np.cos(yaw) - ay_ms2 * np.sin(yaw)
#                 ay_world = ax_ms2 * np.sin(yaw) + ay_ms2 * np.cos(yaw)
                
#                 # Apply force based on acceleration (F = ma)
#                 mass = 10.0
#                 force_x = mass * ax_world
#                 force_y = mass * ay_world
                
#                 # Apply force to the bot
#                 p.applyExternalForce(
#                     self.bot_id,
#                     -1,
#                     [force_x, force_y, 0],
#                     pos,
#                     p.WORLD_FRAME
#                 )
                
#                 # Apply torque based on angular velocity
#                 current_ang_vel_z = ang_vel[2]
#                 ang_vel_error = gz_rads - current_ang_vel_z
#                 torque_z = ang_vel_error * 10.0
                
#                 p.applyExternalTorque(
#                     self.bot_id,
#                     -1,
#                     [0, 0, torque_z],
#                     p.WORLD_FRAME
#                 )
                
#                 # Step simulation
#                 p.stepSimulation()
#                 await asyncio.sleep(1./240.)
#         except asyncio.CancelledError:
#             pass
    
#     async def update_speed(self, speedL=None, speedR=None):
#         async with self.lock:
#             if speedL is not None:
#                 self.speedL = speedL
#             if speedR is not None:
#                 self.speedR = speedR
    
#     async def close(self):
#         self.running = False
#         if self.websocket:
#             await self.websocket.close()
#         if self.physics_client is not None:
#             p.disconnect()
#         print("WebSocket and PyBullet closed")

# async def main():
#     client = ESP32WebSocketClient()
#     await client.connect()
    
#     send_task = asyncio.create_task(client.send_loop())
#     recv_task = asyncio.create_task(client.receive_loop())
#     sim_task = asyncio.create_task(client.simulation_loop())
    
#     try:
#         await asyncio.gather(send_task, recv_task, sim_task)
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         await client.close()
#         sim_task.cancel()
#         send_task.cancel()
#         recv_task.cancel()

# if __name__ == "__main__":
#     asyncio.run(main())

##################################################################################################################################################

# import websockets
# import asyncio
# import json
# import pybullet as p
# import pybullet_data
# import numpy as np
# import time

# class ESP32WebSocketClient:
#     def __init__(self, uri="ws://192.168.1.100:81"):
#         self.uri = uri
#         self.websocket = None
#         self.running = True
        
#         self.speedL = 1500
#         self.speedR = 1500
#         self.lock = asyncio.Lock()
        
#         # IMU data
#         self.ax = 0.0  # acceleration in g
#         self.ay = 0.0
#         self.gz = 0.0  # angular velocity in deg/s
        
#         # Integration state
#         self.vx = 0.0  # velocity in m/s
#         self.vy = 0.0
#         self.yaw = 0.0  # orientation in radians
#         self.last_update_time = None
        
#         # IMU calibration/bias (calculated from stationary readings)
#         self.ax_bias = -0.084  # Average stationary ax
#         self.ay_bias = -0.016  # Average stationary ay
#         self.gz_bias = 0.25    # Average stationary gz
        
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
#         p.setGravity(0, 0, -9.81)
        
#         # Load plane
#         p.loadURDF("plane.urdf")
        
#         # Create simple box robot
#         bot_size = [0.1, 0.2, 0.1]  # length, width, height
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
        
#         # Create walls around the origin (5m x 5m arena)
#         wall_height = 0.5
#         wall_thickness = 0.1
#         arena_size = 5.0
        
#         wall_configs = [
#             # [x, y, length, width]
#             [arena_size/2, 0, wall_thickness, arena_size],      # Right wall
#             [-arena_size/2, 0, wall_thickness, arena_size],     # Left wall
#             [0, arena_size/2, arena_size, wall_thickness],      # Front wall
#             [0, -arena_size/2, arena_size, wall_thickness]      # Back wall
#         ]
        
#         for x, y, length, width in wall_configs:
#             wall_shape = p.createCollisionShape(
#                 p.GEOM_BOX, 
#                 halfExtents=[length/2, width/2, wall_height/2]
#             )
#             wall_visual = p.createVisualShape(
#                 p.GEOM_BOX,
#                 halfExtents=[length/2, width/2, wall_height/2],
#                 rgbaColor=[0.7, 0.7, 0.7, 1.0]
#             )
#             wall_id = p.createMultiBody(
#                 baseMass=0,
#                 baseCollisionShapeIndex=wall_shape,
#                 baseVisualShapeIndex=wall_visual,
#                 basePosition=[x, y, wall_height/2]
#             )
#             self.walls.append(wall_id)
        
#         # Set camera
#         p.resetDebugVisualizerCamera(
#             cameraDistance=6.0,
#             cameraYaw=0,
#             cameraPitch=-89,
#             cameraTargetPosition=[0, 0, 0]
#         )
        
#         # Add velocity damping for more realistic movement
#         p.changeDynamics(self.bot_id, -1, linearDamping=0.5, angularDamping=0.5)
        
#     async def connect(self):
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to ESP32")
    
#     async def send_loop(self):
#         """Send motor commands at fixed rate"""
#         try:
#             while self.running:
#                 async with self.lock:
#                     message = {
#                         "action": "move",
#                         "speedL": self.speedL,
#                         "speedR": self.speedR
#                     }
#                 await self.websocket.send(json.dumps(message))
#                 await asyncio.sleep(0.02)  # 50 Hz
#         except asyncio.CancelledError:
#             pass
    
#     async def receive_loop(self):
#         """Receive sensor data"""
#         try:
#             while self.running:
#                 message = await asyncio.wait_for(
#                     self.websocket.recv(), timeout=0.1
#                 )
#                 data = json.loads(message)
                
#                 # Update IMU data
#                 async with self.lock:
#                     self.ax = data.get("ax", 0.0)
#                     self.ay = data.get("ay", 0.0)
#                     self.gz = data.get("gz", 0.0)
                    
#                     # Collect calibration samples (first 100 samples)
#                     if not self.is_calibrated and len(self.calibration_samples) < 100:
#                         self.calibration_samples.append({
#                             'ax': self.ax,
#                             'ay': self.ay,
#                             'gz': self.gz
#                         })
#                         if len(self.calibration_samples) == 100:
#                             # Calculate bias from samples
#                             self.ax_bias = np.mean([s['ax'] for s in self.calibration_samples])
#                             self.ay_bias = np.mean([s['ay'] for s in self.calibration_samples])
#                             self.gz_bias = np.mean([s['gz'] for s in self.calibration_samples])
#                             self.is_calibrated = True
#                             print(f"\n=== IMU CALIBRATED ===")
#                             print(f"ax_bias: {self.ax_bias:.6f}")
#                             print(f"ay_bias: {self.ay_bias:.6f}")
#                             print(f"gz_bias: {self.gz_bias:.6f}")
#                             print("======================\n")
#                             await asyncio.sleep(2)
                
#                 # print(
#                 #     data["data"],
#                 #     "ax:", data["ax"],
#                 #     "ay:", data["ay"],
#                 #     "az:", data["az"],
#                 #     "gx:", data["gx"],
#                 #     "gy:", data["gy"],
#                 #     "gz:", data["gz"]
#                 # )
#                 print(
#                     data["data"],
#                     "ax:", data["ax"],
#                     "aangx:", data["aangx"],
#                     "angx:", data["angx"],
#                     "ay:", data["ay"],
#                     "aangy:", data["aangy"],
#                     "angy:", data["angy"],
#                     "gz:", data["gz"]
#                 )
#         except asyncio.TimeoutError:
#             pass
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed")
#             self.running = False
    
#     async def simulation_loop(self):
#         """Update PyBullet simulation"""
#         try:
#             self.last_update_time = time.time()
            
#             while self.running:
#                 # Wait for calibration to complete
#                 if not self.is_calibrated:
#                     await asyncio.sleep(0.1)
#                     continue
                
#                 current_time = time.time()
#                 dt = current_time - self.last_update_time
#                 self.last_update_time = current_time
                
#                 # Clamp dt to prevent large jumps
#                 dt = min(dt, 0.1)
                
#                 async with self.lock:
#                     ax = self.ax
#                     ay = self.ay
#                     gz = self.gz
                
#                 if self.bot_id is None:
#                     await asyncio.sleep(1./240.)
#                     continue
                
#                 # Remove bias from IMU readings
#                 ax_corrected = ax - self.ax_bias
#                 ay_corrected = ay - self.ay_bias
#                 gz_corrected = gz - self.gz_bias
                
#                 # Convert units
#                 ax_ms2 = ax_corrected * 9.81  # g to m/s²
#                 ay_ms2 = ay_corrected * 9.81
#                 gz_rads = np.radians(gz_corrected)  # deg/s to rad/s
                
#                 # Apply deadzone to reduce drift from sensor noise
#                 # Lower thresholds since we've removed bias
#                 deadzone_accel = 0.01  # 0.01g threshold
#                 deadzone_gyro = 0.1    # 0.5 deg/s threshold
                
#                 if abs(ax_corrected) < deadzone_accel:
#                     ax_ms2 = 0.0
#                 if abs(ay_corrected) < deadzone_accel:
#                     ay_ms2 = 0.0
#                 if abs(gz_corrected) < deadzone_gyro:
#                     gz_rads = 0.0
                
#                 # Update yaw (orientation) by integrating angular velocity
#                 self.yaw += gz_rads * dt
#                 # Normalize yaw to [-pi, pi]
#                 self.yaw = np.arctan2(np.sin(self.yaw), np.cos(self.yaw))
                
#                 # Transform accelerations from body frame to world frame
#                 ax_world = ax_ms2 * np.cos(self.yaw) - ay_ms2 * np.sin(self.yaw)
#                 ay_world = ax_ms2 * np.sin(self.yaw) + ay_ms2 * np.cos(self.yaw)
                
#                 # Apply acceleration gain for more responsiveness
#                 accel_gain = 1.0  # Amplify acceleration response
#                 ax_world *= accel_gain
#                 ay_world *= accel_gain
                
#                 # Update velocity by integrating acceleration
#                 self.vx += ax_world * dt
#                 self.vy += ay_world * dt
                
#                 # Apply velocity damping only when no significant acceleration
#                 if abs(ax_corrected) < deadzone_accel and abs(ay_corrected) < deadzone_accel:
#                     damping_factor = 0.92  # Stronger damping when coasting
#                     self.vx *= damping_factor
#                     self.vy *= damping_factor
#                 else:
#                     # Lighter damping during active acceleration
#                     damping_factor = 0.98
#                     self.vx *= damping_factor
#                     self.vy *= damping_factor
                
#                 # Apply velocity limits to prevent unrealistic speeds
#                 max_velocity = 10.0  # m/s
#                 current_speed = np.sqrt(self.vx**2 + self.vy**2)
#                 if current_speed > max_velocity:
#                     scale = max_velocity / current_speed
#                     self.vx *= scale
#                     self.vy *= scale
                
#                 # Get current position
#                 pos, _ = p.getBasePositionAndOrientation(self.bot_id)
                
#                 # Update position by integrating velocity
#                 new_x = pos[0] + self.vx * dt
#                 new_y = pos[1] + self.vy * dt
#                 new_z = pos[2]  # keep z constant
                
#                 # Clamp position to arena bounds
#                 max_pos = 2.0  # slightly inside the 5m arena
#                 new_x = np.clip(new_x, -max_pos, max_pos)
#                 new_y = np.clip(new_y, -max_pos, max_pos)
                
#                 # If hit wall, stop velocity in that direction
#                 if abs(new_x) >= max_pos:
#                     self.vx = 0.0
#                 if abs(new_y) >= max_pos:
#                     self.vy = 0.0
                
#                 # Convert yaw to quaternion
#                 new_orn = p.getQuaternionFromEuler([0, 0, self.yaw])
                
#                 # Set new position and orientation
#                 p.resetBasePositionAndOrientation(
#                     self.bot_id,
#                     [new_x, new_y, new_z],
#                     new_orn
#                 )
                
#                 # Set velocity for physics engine (for collisions)
#                 p.resetBaseVelocity(
#                     self.bot_id,
#                     linearVelocity=[self.vx, self.vy, 0],
#                     angularVelocity=[0, 0, gz_rads]
#                 )
                
#                 # Step simulation
#                 p.stepSimulation()
#                 await asyncio.sleep(1./240.)
#         except asyncio.CancelledError:
#             pass
    
#     async def update_speed(self, speedL=None, speedR=None):
#         async with self.lock:
#             if speedL is not None:
#                 self.speedL = speedL
#             if speedR is not None:
#                 self.speedR = speedR
    
#     async def close(self):
#         self.running = False
#         if self.websocket:
#             await self.websocket.close()
#         if self.physics_client is not None:
#             p.disconnect()
#         print("WebSocket and PyBullet closed")

# async def main():
#     client = ESP32WebSocketClient()
#     await client.connect()
    
#     send_task = asyncio.create_task(client.send_loop())
#     recv_task = asyncio.create_task(client.receive_loop())
#     sim_task = asyncio.create_task(client.simulation_loop())
    
#     try:
#         await asyncio.gather(send_task, recv_task, sim_task)
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         await client.close()
#         send_task.cancel()
#         recv_task.cancel()
#         sim_task.cancel()

# if __name__ == "__main__":
#     asyncio.run(main())


#########################################################################################################################################

# import websockets
# import asyncio
# import json
# import pybullet as p
# import pybullet_data
# import numpy as np
# import time

# class ESP32WebSocketClient:
#     def __init__(self, uri="ws://192.168.1.100:81"):
#         self.uri = uri
#         self.websocket = None
#         self.running = True
        
#         self.speedL = 1500
#         self.speedR = 1500
#         self.lock = asyncio.Lock()
        
#         # IMU data
#         self.ax = 0.0  # acceleration in g
#         self.ay = 0.0
#         self.gz = 0.0  # angular velocity in deg/s
#         self.aangx = 0.0  # acceleration angle X in degrees
#         self.aangy = 0.0  # acceleration angle Y in degrees
#         self.angx = 0.0  # orientation angle X in degrees
#         self.angy = 0.0  # orientation angle Y in degrees
        
#         # Integration state
#         self.vx = 0.0  # velocity in m/s
#         self.vy = 0.0
#         self.yaw = 0.0  # orientation in radians
#         self.last_update_time = None
        
#         # IMU calibration/bias (calculated from stationary readings)
#         self.ax_bias = -0.084  # Average stationary ax
#         self.ay_bias = -0.016  # Average stationary ay
#         self.gz_bias = 0.25    # Average stationary gz
#         self.angx_bias = 0.0   # Orientation angle X bias
#         self.angy_bias = 0.0   # Orientation angle Y bias
        
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
#         p.setGravity(0, 0, -9.81)
        
#         # Load plane
#         p.loadURDF("plane.urdf")
        
#         # Create simple box robot
#         bot_size = [0.1, 0.2, 0.1]  # length, width, height
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
        
#         # Create walls around the origin (5m x 5m arena)
#         wall_height = 0.5
#         wall_thickness = 0.1
#         arena_size = 5.0
        
#         wall_configs = [
#             # [x, y, length, width]
#             [arena_size/2, 0, wall_thickness, arena_size],      # Right wall
#             [-arena_size/2, 0, wall_thickness, arena_size],     # Left wall
#             [0, arena_size/2, arena_size, wall_thickness],      # Front wall
#             [0, -arena_size/2, arena_size, wall_thickness]      # Back wall
#         ]
        
#         for x, y, length, width in wall_configs:
#             wall_shape = p.createCollisionShape(
#                 p.GEOM_BOX, 
#                 halfExtents=[length/2, width/2, wall_height/2]
#             )
#             wall_visual = p.createVisualShape(
#                 p.GEOM_BOX,
#                 halfExtents=[length/2, width/2, wall_height/2],
#                 rgbaColor=[0.7, 0.7, 0.7, 1.0]
#             )
#             wall_id = p.createMultiBody(
#                 baseMass=0,
#                 baseCollisionShapeIndex=wall_shape,
#                 baseVisualShapeIndex=wall_visual,
#                 basePosition=[x, y, wall_height/2]
#             )
#             self.walls.append(wall_id)
        
#         # Set camera
#         p.resetDebugVisualizerCamera(
#             cameraDistance=6.0,
#             cameraYaw=0,
#             cameraPitch=-89,
#             cameraTargetPosition=[0, 0, 0]
#         )
        
#         # Add velocity damping for more realistic movement
#         p.changeDynamics(self.bot_id, -1, linearDamping=0.0, angularDamping=0.5)
        
#     async def connect(self):
#         self.websocket = await websockets.connect(self.uri)
#         print("Connected to ESP32")
    
#     async def send_loop(self):
#         """Send motor commands at fixed rate"""
#         try:
#             while self.running:
#                 async with self.lock:
#                     message = {
#                         "action": "move",
#                         "speedL": self.speedL,
#                         "speedR": self.speedR
#                     }
#                 await self.websocket.send(json.dumps(message))
#                 await asyncio.sleep(0.02)  # 50 Hz
#         except asyncio.CancelledError:
#             pass
    
#     async def receive_loop(self):
#         """Receive sensor data"""
#         try:
#             while self.running:
#                 message = await asyncio.wait_for(
#                     self.websocket.recv(), timeout=0.1
#                 )
#                 data = json.loads(message)
                
#                 # Update IMU data
#                 async with self.lock:
#                     self.ax = data.get("ax", 0.0)
#                     self.ay = data.get("ay", 0.0)
#                     self.gz = data.get("gz", 0.0)
#                     self.aangx = data.get("aangx", 0.0)
#                     self.aangy = data.get("aangy", 0.0)
#                     self.angx = data.get("angx", 0.0)
#                     self.angy = data.get("angy", 0.0)
                    
#                     # Collect calibration samples (first 100 samples)
#                     if not self.is_calibrated and len(self.calibration_samples) < 100:
#                         self.calibration_samples.append({
#                             'ax': self.ax,
#                             'ay': self.ay,
#                             'gz': self.gz,
#                             'angx': self.angx,
#                             'angy': self.angy
#                         })
#                         if len(self.calibration_samples) == 100:
#                             # Calculate bias from samples
#                             self.ax_bias = np.mean([s['ax'] for s in self.calibration_samples])
#                             self.ay_bias = np.mean([s['ay'] for s in self.calibration_samples])
#                             self.gz_bias = np.mean([s['gz'] for s in self.calibration_samples])
#                             self.angx_bias = np.mean([s['angx'] for s in self.calibration_samples])
#                             self.angy_bias = np.mean([s['angy'] for s in self.calibration_samples])
#                             self.is_calibrated = True
#                             print(f"\n=== IMU CALIBRATED ===")
#                             print(f"ax_bias: {self.ax_bias:.6f}")
#                             print(f"ay_bias: {self.ay_bias:.6f}")
#                             print(f"gz_bias: {self.gz_bias:.6f}")
#                             print(f"angx_bias: {self.angx_bias:.6f}")
#                             print(f"angy_bias: {self.angy_bias:.6f}")
#                             print("======================\n")
#                             await asyncio.sleep(2)
                
#                 print(
#                     data["data"],
#                     "ax:", data["ax"],
#                     "aangx:", data.get("aangx", 0),
#                     "angx:", data.get("angx", 0),
#                     "ay:", data["ay"],
#                     "aangy:", data.get("aangy", 0),
#                     "angy:", data.get("angy", 0),
#                     "gz:", data["gz"]
#                 )
#         except asyncio.TimeoutError:
#             pass
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed")
#             self.running = False
    
#     async def simulation_loop(self):
#         """Update PyBullet simulation"""
#         try:
#             self.last_update_time = time.time()
            
#             while self.running:
#                 # Wait for calibration to complete
#                 if not self.is_calibrated:
#                     await asyncio.sleep(0.1)
#                     continue
                
#                 current_time = time.time()
#                 dt = current_time - self.last_update_time
#                 self.last_update_time = current_time
                
#                 # Clamp dt to prevent large jumps
#                 # dt = min(dt, 0.1)
                
#                 async with self.lock:
#                     ax = self.ax
#                     ay = self.ay
#                     gz = self.gz
#                     aangx = self.aangx
#                     aangy = self.aangy
#                     angx = self.angx
#                     angy = self.angy
                
#                 if self.bot_id is None:
#                     await asyncio.sleep(1./100.)
#                     continue
                
#                 # Remove bias from IMU readings
#                 ax_corrected = ax - self.ax_bias
#                 ay_corrected = ay - self.ay_bias
#                 gz_corrected = gz - self.gz_bias
#                 angx_corrected = angx - self.angx_bias
#                 angy_corrected = angy - self.angy_bias
                
#                 # Calculate pitch and roll from angles (in radians)
#                 pitch = np.radians(angx_corrected)  # rotation around X
#                 roll = np.radians(angy_corrected)   # rotation around Y
                
#                 # Remove gravity component from accelerations using pitch and roll
#                 # This gives us the actual linear acceleration
#                 gravity = 1.0  # 1g
#                 ax_linear = ax_corrected + gravity * np.sin(roll)
#                 ay_linear = ay_corrected - gravity * np.sin(pitch)
                
#                 # Convert linear accelerations to m/s²
#                 ax_ms2 = ax_linear * 9.81
#                 ay_ms2 = ay_linear * 9.81
#                 gz_rads = np.radians(gz_corrected)
                
#                 # Apply deadzone - much tighter now with gravity compensation
#                 deadzone_accel = 0.08  # 0.008g threshold
#                 deadzone_gyro = 0.3     # 0.3 deg/s threshold
                
#                 if abs(ax_linear) < deadzone_accel:
#                     ax_ms2 = 0.0
#                 if abs(ay_linear) < deadzone_accel:
#                     ay_ms2 = 0.0
#                 if abs(gz_corrected) < deadzone_gyro:
#                     gz_rads = 0.0
                
#                 # Update yaw (orientation) by integrating angular velocity
#                 self.yaw += gz_rads * dt
#                 # Normalize yaw to [-pi, pi]
#                 self.yaw = np.arctan2(np.sin(self.yaw), np.cos(self.yaw))
                
#                 # Transform accelerations from body frame to world frame
#                 # Only use yaw for 2D movement (robot stays flat on ground)
#                 ax_world = ax_ms2 * np.cos(self.yaw) - ay_ms2 * np.sin(self.yaw)
#                 ay_world = ax_ms2 * np.sin(self.yaw) + ay_ms2 * np.cos(self.yaw)
                
#                 # Apply acceleration gain for more responsiveness
#                 accel_gain = 2.0  # Increased from 3.0
#                 ax_world *= accel_gain
#                 ay_world *= accel_gain
                
#                 # Update velocity by integrating acceleration
#                 self.vx += ax_world * dt
#                 self.vy += ay_world * dt
                
#                 # Apply velocity damping
#                 if abs(ax_linear) < deadzone_accel and abs(ay_linear) < deadzone_accel:
#                     damping_factor = 0.90  # Stronger damping when coasting
#                     self.vx *= damping_factor
#                     self.vy *= damping_factor
#                 else:
#                     # Lighter damping during active acceleration
#                     damping_factor = 0.999
#                     self.vx *= damping_factor
#                     self.vy *= damping_factor
                
#                 # Apply velocity limits
#                 max_velocity = 10.0  # m/s
#                 current_speed = np.sqrt(self.vx**2 + self.vy**2)
#                 if current_speed > max_velocity:
#                     scale = max_velocity / current_speed
#                     self.vx *= scale
#                     self.vy *= scale
                
#                 # Get current position
#                 pos, _ = p.getBasePositionAndOrientation(self.bot_id)
                
#                 # Update position by integrating velocity
#                 new_x = pos[0] + self.vx * dt
#                 new_y = pos[1] + self.vy * dt
#                 new_z = pos[2]  # keep z constant
                
#                 # Clamp position to arena bounds
#                 max_pos = 2.5
#                 new_x = np.clip(new_x, -max_pos, max_pos)
#                 new_y = np.clip(new_y, -max_pos, max_pos)
                
#                 # If hit wall, stop velocity in that direction
#                 if abs(new_x) >= max_pos:
#                     self.vx = 0.0
#                 if abs(new_y) >= max_pos:
#                     self.vy = 0.0
                
#                 # Create quaternion from yaw only (keep robot flat)
#                 new_orn = p.getQuaternionFromEuler([0, 0, self.yaw])
                
#                 # Set new position and orientation
#                 p.resetBasePositionAndOrientation(
#                     self.bot_id,
#                     [new_x, new_y, new_z],
#                     new_orn
#                 )
                
#                 # Set velocity for physics engine
#                 p.resetBaseVelocity(
#                     self.bot_id,
#                     linearVelocity=[self.vx, self.vy, 0],
#                     angularVelocity=[0, 0, gz_rads]
#                 )
                
#                 # Step simulation
#                 p.stepSimulation()
#                 await asyncio.sleep(1./500.)
#         except asyncio.CancelledError:
#             pass
    
#     async def update_speed(self, speedL=None, speedR=None):
#         async with self.lock:
#             if speedL is not None:
#                 self.speedL = speedL
#             if speedR is not None:
#                 self.speedR = speedR
    
#     async def close(self):
#         self.running = False
#         if self.websocket:
#             await self.websocket.close()
#         if self.physics_client is not None:
#             p.disconnect()
#         print("WebSocket and PyBullet closed")

# async def main():
#     client = ESP32WebSocketClient()
#     await client.connect()
    
#     send_task = asyncio.create_task(client.send_loop())
#     recv_task = asyncio.create_task(client.receive_loop())
#     sim_task = asyncio.create_task(client.simulation_loop())
    
#     try:
#         await asyncio.gather(send_task, recv_task, sim_task)
#     except KeyboardInterrupt:
#         print("\nShutting down...")
#         await client.close()
#         send_task.cancel()
#         recv_task.cancel()
#         sim_task.cancel()

# if __name__ == "__main__":
#     asyncio.run(main())


#####################################################################################################################################

import websockets
import asyncio
import json
import pybullet as p
import pybullet_data
import numpy as np
import time
import signal
import sys

class ESP32WebSocketClient:
    def __init__(self, uri="ws://192.168.1.100:81"):
        self.uri = uri
        self.websocket = None
        self.running = True
        
        self.speedL = 1500
        self.speedR = 1500
        self.lock = asyncio.Lock()
        
        # IMU data - gravity-free acceleration and quaternion
        self.ax = 0.0  # linear acceleration in g (gravity-free)
        self.ay = 0.0
        self.az = 0.0
        self.qw = 1.0  # quaternion
        self.qx = 0.0
        self.qy = 0.0
        self.qz = 0.0
        self.gz = 0.0  # angular velocity in deg/s
        
        # Integration state
        self.vx = 0.0  # velocity in m/s
        self.vy = 0.0
        self.last_update_time = None
        
        # IMU calibration (only for acceleration and gyro bias)
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
        p.setGravity(0, 0, -9.81)
        
        # Load plane
        p.loadURDF("plane.urdf")
        
        # Create simple box robot
        bot_size = [0.1, 0.2, 0.1]
        collision_shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=bot_size)
        visual_shape = p.createVisualShape(
            p.GEOM_BOX, 
            halfExtents=bot_size,
            rgbaColor=[0.2, 0.5, 0.8, 1.0]
        )
        
        self.bot_id = p.createMultiBody(
            baseMass=1.0,
            baseCollisionShapeIndex=collision_shape,
            baseVisualShapeIndex=visual_shape,
            basePosition=[0, 0, 0.15]
        )
        
        # Create walls around the origin (5m x 5m arena)
        wall_height = 0.5
        wall_thickness = 0.1
        arena_size = 5.0
        
        wall_configs = [
            [arena_size/2, 0, wall_thickness, arena_size],
            [-arena_size/2, 0, wall_thickness, arena_size],
            [0, arena_size/2, arena_size, wall_thickness],
            [0, -arena_size/2, arena_size, wall_thickness]
        ]
        
        for x, y, length, width in wall_configs:
            wall_shape = p.createCollisionShape(
                p.GEOM_BOX, 
                halfExtents=[length/2, width/2, wall_height/2]
            )
            wall_visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=[length/2, width/2, wall_height/2],
                rgbaColor=[0.7, 0.7, 0.7, 1.0]
            )
            wall_id = p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=wall_shape,
                baseVisualShapeIndex=wall_visual,
                basePosition=[x, y, wall_height/2]
            )
            self.walls.append(wall_id)
        
        # Set camera (top-down view)
        p.resetDebugVisualizerCamera(
            cameraDistance=6.0,
            cameraYaw=0,
            cameraPitch=-89,
            cameraTargetPosition=[0, 0, 0]
        )
        
        p.changeDynamics(self.bot_id, -1, linearDamping=0.1, angularDamping=0.1)
        
    def quaternion_to_yaw(self, qw, qx, qy, qz):
        """Extract yaw angle from quaternion (rotation around Z-axis)"""
        # Yaw (z-axis rotation)
        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        return yaw
        
    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        print("Connected to ESP32")
    
    async def send_loop(self):
        """Send motor commands at fixed rate"""
        try:
            while self.running:
                async with self.lock:
                    message = {
                        "action": "move",
                        "speedL": self.speedL,
                        "speedR": self.speedR
                    }
                await self.websocket.send(json.dumps(message))
                await asyncio.sleep(0.02)
        except asyncio.CancelledError:
            print("Send loop cancelled")
        except Exception as e:
            print(f"Send loop error: {e}")
    
    async def receive_loop(self):
        """Receive sensor data"""
        try:
            while self.running:
                message = await asyncio.wait_for(
                    self.websocket.recv(), timeout=0.5
                )
                data = json.loads(message)
                
                async with self.lock:
                    # Get gravity-free linear acceleration (in g)
                    self.ax = data.get("ax", 0.0)
                    self.ay = data.get("ay", 0.0)
                    self.az = data.get("az", 0.0)
                    
                    # Get quaternion orientation
                    self.qw = data.get("qw", 1.0)
                    self.qx = data.get("qx", 0.0)
                    self.qy = data.get("qy", 0.0)
                    self.qz = data.get("qz", 0.0)
                    
                    # Get angular velocity
                    self.gz = data.get("gz", 0.0)
                    
                    # Collect calibration samples (only for accel and gyro bias)
                    if not self.is_calibrated and len(self.calibration_samples) < 100:
                        self.calibration_samples.append({
                            'ax': self.ax,
                            'ay': self.ay,
                            'gz': self.gz
                        })
                        if len(self.calibration_samples) == 100:
                            self.ax_bias = np.mean([s['ax'] for s in self.calibration_samples])
                            self.ay_bias = np.mean([s['ay'] for s in self.calibration_samples])
                            self.gz_bias = np.mean([s['gz'] for s in self.calibration_samples])
                            self.is_calibrated = True
                            print(f"\n=== IMU CALIBRATED ===")
                            print(f"ax_bias: {self.ax_bias:.6f} g (linear)")
                            print(f"ay_bias: {self.ay_bias:.6f} g (linear)")
                            print(f"gz_bias: {self.gz_bias:.6f} deg/s")
                            print("Using quaternion for orientation (no drift!)")
                            print("======================\n")
                
                yaw_deg = np.degrees(self.quaternion_to_yaw(self.qw, self.qx, self.qy, self.qz))
                print(f"ax:{data['ax']:.3f} ay:{data['ay']:.3f} gz:{data['gz']:.3f} yaw:{yaw_deg:.1f}°")
                    
        except asyncio.TimeoutError:
            pass
        except asyncio.CancelledError:
            print("Receive loop cancelled")
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            self.running = False
        except Exception as e:
            print(f"Receive loop error: {e}")
            self.running = False
    
    async def simulation_loop(self):
        """Update PyBullet simulation"""
        try:
            self.last_update_time = time.time()
            
            while self.running:
                if not self.is_calibrated:
                    await asyncio.sleep(0.1)
                    continue
                
                current_time = time.time()
                dt = current_time - self.last_update_time
                self.last_update_time = current_time
                
                # Clamp dt to prevent jumps
                dt = min(dt, 0.05)
                
                async with self.lock:
                    # Get linear acceleration (already gravity-free!)
                    ax = self.ax
                    ay = self.ay
                    
                    # Get quaternion
                    qw = self.qw
                    qx = self.qx
                    qy = self.qy
                    qz = self.qz
                    
                    # Get angular velocity
                    gz = self.gz
                
                if self.bot_id is None:
                    await asyncio.sleep(1./240.)
                    continue
                
                # Remove bias from linear acceleration
                ax_corrected = ax - self.ax_bias
                ay_corrected = ay - self.ay_bias
                gz_corrected = gz - self.gz_bias
                
                # Convert linear acceleration to m/s²
                ax_ms2 = ax_corrected * 9.81
                ay_ms2 = ay_corrected * 9.81
                gz_rads = np.radians(gz_corrected)
                
                # Apply deadzones - can be much tighter now!
                deadzone_accel = 0.01  # 0.01g threshold
                deadzone_gyro = 0.3    # 0.3 deg/s threshold
                
                if abs(ax_corrected) < deadzone_accel:
                    ax_ms2 = 0.0
                if abs(ay_corrected) < deadzone_accel:
                    ay_ms2 = 0.0
                if abs(gz_corrected) < deadzone_gyro:
                    gz_rads = 0.0
                
                # Extract yaw from quaternion - NO DRIFT!
                yaw = self.quaternion_to_yaw(qw, qx, qy, qz)
                
                # Transform accelerations from body frame to world frame
                # Using the accurate quaternion-based yaw
                ax_world = ax_ms2 * np.cos(yaw) - ay_ms2 * np.sin(yaw)
                ay_world = ax_ms2 * np.sin(yaw) + ay_ms2 * np.cos(yaw)
                
                # Acceleration gain for responsiveness
                accel_gain = 2.0  # Higher gain since we have clean data
                ax_world *= accel_gain
                ay_world *= accel_gain
                
                # Integrate acceleration to velocity
                self.vx += ax_world * dt
                self.vy += ay_world * dt
                
                # Smart damping - aggressive when no input
                if abs(ax_corrected) < deadzone_accel and abs(ay_corrected) < deadzone_accel:
                    # Exponential decay when coasting
                    decay_rate = 6.0  # faster decay
                    damping = np.exp(-decay_rate * dt)
                    self.vx *= damping
                    self.vy *= damping
                    
                    # Hard stop if very slow
                    if abs(self.vx) < 0.01:
                        self.vx = 0.0
                    if abs(self.vy) < 0.01:
                        self.vy = 0.0
                else:
                    # Minimal damping during acceleration
                    self.vx *= 0.998
                    self.vy *= 0.998
                
                # # Velocity limits
                # max_velocity = 10.0
                # current_speed = np.sqrt(self.vx**2 + self.vy**2)
                # if current_speed > max_velocity:
                #     scale = max_velocity / current_speed
                #     self.vx *= scale
                #     self.vy *= scale
                
                # Get current position
                pos, _ = p.getBasePositionAndOrientation(self.bot_id)
                
                # Update position
                new_x = pos[0] + self.vx * dt
                new_y = pos[1] + self.vy * dt
                new_z = 0.15
                
                # Arena bounds
                max_pos = 2.4
                if new_x > max_pos or new_x < -max_pos:
                    new_x = np.clip(new_x, -max_pos, max_pos)
                    self.vx = 0.0
                if new_y > max_pos or new_y < -max_pos:
                    new_y = np.clip(new_y, -max_pos, max_pos)
                    self.vy = 0.0
                
                # Use quaternion directly for orientation (keep robot flat in XY plane)
                # We only use yaw, so reconstruct quaternion with roll=0, pitch=0
                new_orn = p.getQuaternionFromEuler([0, 0, yaw])
                
                # Update PyBullet
                p.resetBasePositionAndOrientation(
                    self.bot_id,
                    [new_x, new_y, new_z],
                    new_orn
                )
                
                p.resetBaseVelocity(
                    self.bot_id,
                    linearVelocity=[self.vx, self.vy, 0],
                    angularVelocity=[0, 0, gz_rads]
                )
                
                p.stepSimulation()
                await asyncio.sleep(1./240.)
                
        except asyncio.CancelledError:
            print("Simulation loop cancelled")
        except Exception as e:
            print(f"Simulation loop error: {e}")
    
    async def update_speed(self, speedL=None, speedR=None):
        async with self.lock:
            if speedL is not None:
                self.speedL = speedL
            if speedR is not None:
                self.speedR = speedR
    
    async def close(self):
        print("Closing connections...")
        self.running = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                print("WebSocket closed")
            except:
                pass
        
        if self.physics_client is not None:
            try:
                p.disconnect()
                print("PyBullet disconnected")
            except:
                pass

async def main():
    client = ESP32WebSocketClient()
    
    # Setup signal handlers for clean shutdown
    def signal_handler(sig, frame):
        print("\n\nCtrl+C detected! Shutting down gracefully...")
        client.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await client.connect()
        
        send_task = asyncio.create_task(client.send_loop())
        recv_task = asyncio.create_task(client.receive_loop())
        sim_task = asyncio.create_task(client.simulation_loop())
        
        # Wait for tasks or until running is False
        while client.running:
            await asyncio.sleep(0.1)
            
        # Cancel all tasks
        print("Cancelling tasks...")
        send_task.cancel()
        recv_task.cancel()
        sim_task.cancel()
        
        # Wait for cancellation to complete
        await asyncio.gather(send_task, recv_task, sim_task, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected")
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        await client.close()
        print("Shutdown complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        sys.exit(0)