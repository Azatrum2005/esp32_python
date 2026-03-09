import serial
import serial.tools.list_ports
import time
import sys

class ESP32Tester:
    def __init__(self, port=None, baudrate=115200):
        self.ser = None
        self.port = port
        self.baudrate = baudrate
        
    def find_esp32_port(self):
        """Auto-detect ESP32 port"""
        ports = serial.tools.list_ports.comports()
        
        print("\nAvailable serial ports:")
        for i, port in enumerate(ports):
            print(f"  [{i}] {port.device} - {port.description}")
        
        if not ports:
            print("ERROR: No serial ports found!")
            return None
            
        # Try to find ESP32 automatically
        for port in ports:
            if 'USB' in port.description or 'UART' in port.description or 'CP210' in port.description:
                print(f"\nAuto-detected: {port.device}")
                return port.device
        
        # If not found, ask user
        choice = input(f"\nSelect port [0-{len(ports)-1}]: ")
        try:
            return ports[int(choice)].device
        except (ValueError, IndexError):
            return ports[0].device
    
    def connect(self):
        """Connect to ESP32"""
        if self.port is None:
            self.port = self.find_esp32_port()
            
        if self.port is None:
            print("ERROR: Could not determine serial port")
            return False
        
        try:
            print(f"\nConnecting to {self.port} at {self.baudrate} baud...")
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for ESP32 to reset
            
            # Clear any pending data
            self.ser.reset_input_buffer()
            
            print("SUCCESS: Connected to ESP32")
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect - {e}")
            return False
    
    def read_output(self, timeout=1.0):
        """Read and display output from ESP32"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"  {line}")
                        
                        # Parse result if it's a RESULT line
                        if line.startswith("RESULT|"):
                            self.parse_result(line)
                except Exception as e:
                    print(f"  Read error: {e}")
            time.sleep(0.01)
    
    def parse_result(self, result_line):
        """Parse and display inference results"""
        try:
            parts = result_line.split('|')
            data = {}
            for part in parts[1:]:  # Skip "RESULT"
                key, value = part.split(':')
                data[key] = value
            
            print("\n" + "="*60)
            print("INFERENCE RESULT:")
            print(f"  Input Value:     {data['input']}")
            print(f"  Quantized:       {data['quantized']}")
            print(f"  Class 0 Score:   {data['class0']}")
            print(f"  Class 1 Score:   {data['class1']}")
            print(f"  Predicted Class: {data['predicted']}")
            
            # Interpret result
            if data['predicted'] == '0':
                print(f"  → LED 1 should light up")
            else:
                print(f"  → LED 2 should light up")
            print("="*60 + "\n")
        except Exception as e:
            print(f"  Warning: Could not parse result - {e}")
    
    def send_value(self, value):
        """Send a value to ESP32 for inference"""
        try:
            command = f"{value}\n"
            self.ser.write(command.encode('utf-8'))
            print(f"\n>>> Sent: {value}")
            
            # Read response
            self.read_output(timeout=2.0)
            return True
        except Exception as e:
            print(f"ERROR: Failed to send - {e}")
            return False
    
    def interactive_mode(self):
        """Interactive testing mode"""
        print("\n" + "="*60)
        print("INTERACTIVE MODE")
        print("="*60)
        print("Commands:")
        print("  Enter any float value (e.g., 1.0, 2.0)")
        print("  '1' - Quick test with value 1.0 (should predict Class 0 / LED 1)")
        print("  '2' - Quick test with value 2.0 (should predict Class 1 / LED 2)")
        print("  'test' - Run comprehensive test")
        print("  'quit' - Exit")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("Enter value: ").strip().lower()
                
                if user_input == 'quit' or user_input == 'exit':
                    print("Exiting...")
                    break
                
                elif user_input == '1':
                    self.send_value(1.0)
                
                elif user_input == '2':
                    self.send_value(2.0)
                
                elif user_input == 'test':
                    self.run_test_suite()
                
                elif user_input:
                    try:
                        value = float(user_input)
                        self.send_value(value)
                    except ValueError:
                        print("ERROR: Invalid number")
                        
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
    
    def run_test_suite(self):
        """Run a comprehensive test suite"""
        print("\n" + "="*60)
        print("RUNNING TEST SUITE")
        print("="*60)
        
        test_values = [
            (0.5, 0, "Well below Class 0"),
            (0.8, 0, "Near Class 0 lower bound"),
            (1.0, 0, "Class 0 center"),
            (1.2, 0, "Near Class 0 upper bound"),
            (1.5, None, "Boundary region"),
            (1.8, 1, "Near Class 1 lower bound"),
            (2.0, 1, "Class 1 center"),
            (2.2, 1, "Near Class 1 upper bound"),
            (2.5, 1, "Well above Class 1"),
        ]
        
        results = []
        for value, expected_class, description in test_values:
            print(f"\n--- Test: {description} ---")
            self.send_value(value)
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print("TEST SUITE COMPLETE")
        print("="*60 + "\n")
    
    def close(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Connection closed")

def main():
    print("="*60)
    print("ESP32 TensorFlow Lite Serial Tester")
    print("="*60)
    
    # Create tester instance
    tester = ESP32Tester()
    
    # Connect to ESP32
    if not tester.connect():
        print("Failed to connect. Exiting.")
        return
    
    # Wait for ESP32 to initialize
    print("\nWaiting for ESP32 initialization...")
    time.sleep(2)
    
    # Read initial output
    print("\nESP32 Output:")
    tester.read_output(timeout=3.0)
    
    try:
        # Start interactive mode
        tester.interactive_mode()
    finally:
        tester.close()

if __name__ == "__main__":
    main()