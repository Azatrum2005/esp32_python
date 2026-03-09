import asyncio
import websockets
import json
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import time
import threading
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- CONFIGURATION ---
PHONE_IP = "192.168.70.149"
IMU_PORT = 8765
CAMERA_URL = f"http://{PHONE_IP}:8080/video"  # IP Webcam URL
# ---------------------

class VisualInertialSLAM:
    def __init__(self):
        # State estimation
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.orientation = np.array([0.0, 0.0, 0.0, 1.0])  # quaternion (x,y,z,w)
        
        # IMU bias
        self.accel_bias = np.array([0.0, 0.0, 0.0])
        
        # Calibration
        self.calibration_samples = []
        self.is_calibrated = False
        
        # Timestamp tracking
        self.last_imu_time = None
        self.last_camera_time = None
        
        # Visual features (ORB)
        self.orb = cv2.ORB_create(nfeatures=800)
        self.bf_matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        self.prev_frame = None
        self.prev_keypoints = None
        self.prev_descriptors = None
        
        # Camera intrinsics (will be estimated)
        self.K = None
        
        # Map (3D points)
        self.map_points = []
        self.map_colors = []
        
        # Trajectory
        self.trajectory = []
        self.trajectory_timestamps = []
        
        # Visualization
        self.fig = None
        self.ax = None
        self.setup_visualization()
        
        # Thread lock
        self.lock = threading.Lock()
        
    def setup_visualization(self):
        """Setup 3D visualization"""
        plt.ion()
        self.fig = plt.figure(figsize=(14, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title('Visual-Inertial SLAM')
        
    def quaternion_to_rotation_matrix(self, q):
        """Convert quaternion [x,y,z,w] to rotation matrix"""
        r = Rotation.from_quat([q[0], q[1], q[2], q[3]])
        return r.as_matrix()
    
    def estimate_camera_matrix(self, frame_shape):
        """Estimate camera intrinsic matrix"""
        h, w = frame_shape[:2]
        # Typical phone camera: ~70° FOV
        focal_length = w * 1.2  # Approximation
        cx, cy = w / 2.0, h / 2.0
        self.K = np.array([
            [focal_length, 0, cx],
            [0, focal_length, cy],
            [0, 0, 1]
        ], dtype=np.float32)
    
    def process_imu(self, linear_accel, rotation_quat, timestamp):
        """Process IMU measurement"""
        with self.lock:
            if self.last_imu_time is None:
                self.last_imu_time = timestamp
                return
            
            dt = timestamp - self.last_imu_time
            self.last_imu_time = timestamp
            
            if dt > 0.5 or dt <= 0:
                return
            
            # Calibration
            if not self.is_calibrated:
                self.calibration_samples.append({
                    'accel': np.array(linear_accel),
                })
                
                if len(self.calibration_samples) >= 50:
                    accels = np.array([s['accel'] for s in self.calibration_samples])
                    self.accel_bias = np.mean(accels, axis=0)
                    self.is_calibrated = True
                    print(f"\n=== IMU CALIBRATED ===")
                    print(f"Accel Bias: {self.accel_bias}")
                    print("======================\n")
                return
            
            # Remove bias
            accel = np.array(linear_accel) - self.accel_bias
            
            # Dead zone
            accel[np.abs(accel) < 0.08] = 0
            
            # Update orientation from sensor
            self.orientation = np.array(rotation_quat)
            
            # Transform acceleration to world frame
            R = self.quaternion_to_rotation_matrix(self.orientation)
            accel_world = R @ accel
            
            # Integrate velocity (with stronger damping)
            self.velocity += accel_world * dt
            self.velocity *= 0.96  # Stronger damping
            
            # Integrate position
            self.position += self.velocity * dt
            
            # Store trajectory
            self.trajectory.append(self.position.copy())
            self.trajectory_timestamps.append(timestamp)
            
            # Print occasional debug
            if len(self.trajectory) % 100 == 0:
                print(f"IMU - Pos: [{self.position[0]:.2f}, {self.position[1]:.2f}, {self.position[2]:.2f}] | "
                      f"Vel: [{self.velocity[0]:.2f}, {self.velocity[1]:.2f}, {self.velocity[2]:.2f}]")
    
    def triangulate_point(self, pt1, pt2, R1, t1, R2, t2):
        """Triangulate 3D point from two camera views"""
        # Projection matrices
        P1 = self.K @ np.hstack([R1, t1.reshape(-1, 1)])
        P2 = self.K @ np.hstack([R2, t2.reshape(-1, 1)])
        
        # Triangulate
        point_4d = cv2.triangulatePoints(P1, P2, pt1.reshape(2, 1), pt2.reshape(2, 1))
        point_3d = point_4d[:3] / point_4d[3]
        
        return point_3d.flatten()
    
    def process_camera(self, frame, timestamp):
        """Process camera frame for visual odometry"""
        with self.lock:
            if not self.is_calibrated:
                return
            
            # Estimate camera matrix once
            if self.K is None:
                self.estimate_camera_matrix(frame.shape)
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect ORB features
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            if self.prev_descriptors is not None and descriptors is not None:
                # Match features
                matches = self.bf_matcher.match(self.prev_descriptors, descriptors)
                matches = sorted(matches, key=lambda x: x.distance)
                
                # Keep good matches
                good_matches = matches[:min(80, len(matches))]
                
                if len(good_matches) > 20:
                    # Extract matched point coordinates
                    pts1 = np.float32([self.prev_keypoints[m.queryIdx].pt for m in good_matches])
                    pts2 = np.float32([keypoints[m.trainIdx].pt for m in good_matches])
                    
                    # Compute Essential Matrix
                    E, mask = cv2.findEssentialMat(pts1, pts2, self.K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
                    
                    if E is not None:
                        # Recover relative pose
                        _, R, t, pose_mask = cv2.recoverPose(E, pts1, pts2, self.K, mask=mask)
                        
                        # Scale estimation using IMU velocity
                        if self.last_camera_time is not None:
                            dt = timestamp - self.last_camera_time
                            
                            # Estimate scale from IMU
                            imu_displacement = np.linalg.norm(self.velocity * dt)
                            
                            if imu_displacement > 0.02:  # Minimum motion threshold
                                # Scale the translation vector
                                t_scaled = t.flatten() * imu_displacement
                                
                                # Transform to world frame
                                R_world = self.quaternion_to_rotation_matrix(self.orientation)
                                delta_pos_visual = R_world @ t_scaled
                                
                                # Fuse visual and IMU estimates (trust IMU more for now)
                                visual_position = self.position + delta_pos_visual
                                self.position = 0.8 * self.position + 0.2 * visual_position
                                
                                # Triangulate and add map points
                                R1 = np.eye(3)
                                t1 = np.zeros(3)
                                R2 = R
                                t2 = t_scaled
                                
                                # Add map points (limit to avoid slowdown)
                                num_points_to_add = min(15, np.sum(pose_mask))
                                point_count = 0
                                
                                for i, m in enumerate(good_matches):
                                    if pose_mask[i] and point_count < num_points_to_add:
                                        try:
                                            point_3d = self.triangulate_point(pts1[i], pts2[i], R1, t1, R2, t2)
                                            
                                            # Check if point is reasonable (not too far)
                                            if np.linalg.norm(point_3d) < 10.0:
                                                # Transform to world coordinates
                                                point_world = R_world @ point_3d + self.position
                                                
                                                # Get color
                                                y, x = int(pts2[i][1]), int(pts2[i][0])
                                                if 0 <= y < frame.shape[0] and 0 <= x < frame.shape[1]:
                                                    color = frame[y, x]
                                                    self.map_points.append(point_world)
                                                    self.map_colors.append(color[::-1] / 255.0)  # BGR to RGB
                                                    point_count += 1
                                        except:
                                            pass
                        
                        # Visualize matches
                        matched_frame = cv2.drawMatches(
                            self.prev_frame, self.prev_keypoints,
                            frame, keypoints,
                            good_matches[:30], None,
                            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
                        )
                        cv2.imshow('Feature Matches', matched_frame)
                        
                        print(f"Visual - Matches: {len(good_matches)}, Map Points: {len(self.map_points)}")
            
            # Update previous frame data
            self.prev_frame = frame.copy()
            self.prev_keypoints = keypoints
            self.prev_descriptors = descriptors
            self.last_camera_time = timestamp
            
            # Show current frame with features
            frame_display = frame.copy()
            if keypoints:
                cv2.drawKeypoints(frame, keypoints, frame_display, color=(0, 255, 0))
            
            # Add info overlay
            cv2.putText(frame_display, f"Features: {len(keypoints)}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame_display, f"Map Points: {len(self.map_points)}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame_display, f"Pos: [{self.position[0]:.1f}, {self.position[1]:.1f}, {self.position[2]:.1f}]", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.imshow('SLAM - Current View', frame_display)
            cv2.waitKey(1)
    
    def update_visualization(self):
        """Update 3D plot"""
        with self.lock:
            self.ax.clear()
            
            # Plot trajectory
            if len(self.trajectory) > 1:
                traj = np.array(self.trajectory)
                self.ax.plot(traj[:, 0], traj[:, 1], traj[:, 2], 
                           'b-', linewidth=2, label='Trajectory', alpha=0.8)
                self.ax.scatter(traj[-1, 0], traj[-1, 1], traj[-1, 2], 
                              c='red', s=150, marker='o', label='Current Position')
                
                # Plot orientation
                if len(self.orientation) == 4:
                    R = self.quaternion_to_rotation_matrix(self.orientation)
                    arrow_length = 0.5
                    # X-axis (red)
                    self.ax.quiver(traj[-1, 0], traj[-1, 1], traj[-1, 2],
                                 R[0, 0], R[1, 0], R[2, 0],
                                 color='red', length=arrow_length, arrow_length_ratio=0.3)
                    # Y-axis (green)
                    self.ax.quiver(traj[-1, 0], traj[-1, 1], traj[-1, 2],
                                 R[0, 1], R[1, 1], R[2, 1],
                                 color='green', length=arrow_length, arrow_length_ratio=0.3)
                    # Z-axis (blue)
                    self.ax.quiver(traj[-1, 0], traj[-1, 1], traj[-1, 2],
                                 R[0, 2], R[1, 2], R[2, 2],
                                 color='blue', length=arrow_length, arrow_length_ratio=0.3)
            
            # Plot map points (subsample if too many)
            if len(self.map_points) > 0:
                map_array = np.array(self.map_points)
                colors = np.array(self.map_colors)
                
                # Subsample if too many points
                if len(map_array) > 2000:
                    indices = np.random.choice(len(map_array), 2000, replace=False)
                    map_array = map_array[indices]
                    colors = colors[indices]
                
                self.ax.scatter(map_array[:, 0], map_array[:, 1], map_array[:, 2], 
                              c=colors, s=3, alpha=0.5, label=f'Map ({len(self.map_points)} pts)')
            
            # Set view limits
            if len(self.trajectory) > 0:
                traj = np.array(self.trajectory)
                margin = 1.5
                
                x_min, x_max = traj[:, 0].min() - margin, traj[:, 0].max() + margin
                y_min, y_max = traj[:, 1].min() - margin, traj[:, 1].max() + margin
                z_min, z_max = traj[:, 2].min() - margin, traj[:, 2].max() + margin
                
                # Include map points in bounds
                if len(self.map_points) > 0:
                    map_array = np.array(self.map_points)
                    x_min = min(x_min, map_array[:, 0].min() - margin)
                    x_max = max(x_max, map_array[:, 0].max() + margin)
                    y_min = min(y_min, map_array[:, 1].min() - margin)
                    y_max = max(y_max, map_array[:, 1].max() + margin)
                    z_min = min(z_min, map_array[:, 2].min() - margin)
                    z_max = max(z_max, map_array[:, 2].max() + margin)
                
                self.ax.set_xlim([x_min, x_max])
                self.ax.set_ylim([y_min, y_max])
                self.ax.set_zlim([z_min, z_max])
            
            self.ax.set_xlabel('X (m)')
            self.ax.set_ylabel('Y (m)')
            self.ax.set_zlabel('Z (m)')
            self.ax.set_title(f'Visual-Inertial SLAM | Trajectory: {len(self.trajectory)} pts | Map: {len(self.map_points)} pts')
            self.ax.legend(loc='upper right')
            self.ax.grid(True, alpha=0.3)
            
            plt.draw()
            plt.pause(0.001)
    
    def save_map(self, filename='slam_map.ply'):
        """Save map as PLY file for viewing in MeshLab"""
        if len(self.map_points) == 0:
            print("No map points to save!")
            return
        
        with open(filename, 'w') as f:
            # PLY header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(self.map_points)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("property uchar red\n")
            f.write("property uchar green\n")
            f.write("property uchar blue\n")
            f.write("end_header\n")
            
            # Write points
            for point, color in zip(self.map_points, self.map_colors):
                r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
                f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} {r} {g} {b}\n")
        
        print(f"Map saved to {filename}")


class SLAMClient:
    def __init__(self, imu_uri, camera_url):
        self.imu_uri = imu_uri
        self.camera_url = camera_url
        self.websocket = None
        self.running = True
        self.slam = VisualInertialSLAM()
        
        # Camera capture thread
        self.camera_thread = None
        
    def camera_thread_func(self):
        """Capture frames from IP Webcam"""
        print(f"Connecting to camera: {self.camera_url}")
        cap = cv2.VideoCapture(self.camera_url)
        
        if not cap.isOpened():
            print("ERROR: Could not connect to IP Webcam!")
            print("Make sure IP Webcam app is running and started server")
            return
        
        print("Camera connected successfully!")
        frame_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if ret:
                timestamp = time.time()
                
                # Resize for performance
                frame = cv2.resize(frame, (640, 480))
                
                # Process every frame (IP Webcam is already ~10-15 FPS)
                self.slam.process_camera(frame, timestamp)
                frame_count += 1
            else:
                print("Failed to read frame from camera")
                time.sleep(0.1)
        
        cap.release()
        print(f"Camera stopped. Processed {frame_count} frames.")
    
    async def connect_imu(self):
        print(f"Connecting to IMU at {self.imu_uri}...")
        self.websocket = await websockets.connect(self.imu_uri)
        print("IMU connected!")
    
    async def imu_receive_loop(self):
        """Receive and process IMU data"""
        try:
            while self.running:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                data = json.loads(message)
                
                if data.get('type') == 'imu':
                    linear_accel = data['linear_accel']
                    rotation_quat = data['rotation_quat']
                    timestamp = data['timestamp']
                    
                    self.slam.process_imu(linear_accel, rotation_quat, timestamp)
                
        except asyncio.TimeoutError:
            print("IMU connection timeout")
        except websockets.exceptions.ConnectionClosed:
            print("IMU disconnected")
            self.running = False
    
    async def visualization_loop(self):
        """Update 3D visualization"""
        while self.running:
            self.slam.update_visualization()
            await asyncio.sleep(0.15)  # ~6-7 Hz
    
    def start_camera(self):
        """Start camera capture in separate thread"""
        self.camera_thread = threading.Thread(target=self.camera_thread_func, daemon=True)
        self.camera_thread.start()
    
    async def close(self):
        self.running = False
        if self.websocket:
            await self.websocket.close()
        cv2.destroyAllWindows()
        plt.close('all')
        
        # Save map
        print("\nSaving map...")
        self.slam.save_map('vi_slam_map.ply')
        print("Map saved! You can view it in MeshLab or CloudCompare")


async def main():
    client = SLAMClient(
        f"ws://{PHONE_IP}:{IMU_PORT}",
        CAMERA_URL
    )
    
    print("=" * 60)
    print("VISUAL-INERTIAL SLAM")
    print("=" * 60)
    print(f"IMU Source: {PHONE_IP}:{IMU_PORT}")
    print(f"Camera Source: {CAMERA_URL}")
    print("=" * 60)
    print("\nMake sure:")
    print("1. Termux server is running (IMU)")
    print("2. IP Webcam app is running and server started")
    print("\nStarting in 3 seconds...")
    await asyncio.sleep(3)
    
    try:
        # Start camera first
        client.start_camera()
        await asyncio.sleep(2)  # Give camera time to initialize
        
        # Connect to IMU
        await client.connect_imu()
        
        # Start processing loops
        imu_task = asyncio.create_task(client.imu_receive_loop())
        viz_task = asyncio.create_task(client.visualization_loop())
        
        await asyncio.gather(imu_task, viz_task)
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        await client.close()
    except Exception as e:
        print(f"Error: {e}")
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())