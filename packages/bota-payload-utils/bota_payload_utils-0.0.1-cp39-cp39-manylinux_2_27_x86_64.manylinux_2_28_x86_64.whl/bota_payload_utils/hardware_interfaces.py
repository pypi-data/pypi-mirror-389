"""
Hardware interface utilities for Bota Payload Utils
"""
from . import bota_payload_utils_ext


class BotaFtSensorHWI(bota_payload_utils_ext.BotaControlBlock):
    """
    Python wrapper for BotaDriver to make it compatible with BotaControlBlock interface
    """
    def __init__(self, driver, imu_offset=None):
        """
        Initialize with an existing driver instance
        
        Args:
            driver: Configured bota_driver.BotaDriver instance
            imu_offset: IMU offset from wrench_frame to imu_frame [x, y, z] in meters
                       Default is [0.0, 0.0, -0.0257] (z = -25.7mm)
        """
        super().__init__()
        self.driver = driver
        self.buffer = bota_payload_utils_ext.BotaControlSensorSignalFrame()
        
        # Set default IMU offset if not provided
        if imu_offset is None:
            imu_offset = [0.0, 0.0, -0.0257]  # z = -25.7mm default
        self.imu_offset = list(imu_offset)
        
    def _cross_product(self, a, b):
        """Compute cross product of two 3D vectors"""
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        ]
    
    def _vector_add(self, a, b):
        """Add two 3D vectors"""
        return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]
    
    def _vector_negate(self, a):
        """Negate a 3D vector"""
        return [-a[0], -a[1], -a[2]]
        
    def update(self, update_input_block=False):
        """Update the sensor data and populate the buffer"""
        try:
            # Read frame from driver
            bota_frame = self.driver.read_frame()
            
            # Populate the buffer
            self.buffer.input_block_name = "hardware"
            self.buffer.block_name = "bota_ft_sensor_hwi"
            
            # Status check - handle integer status values
            status_error = (
                bool(bota_frame.status.throttled) or 
                bool(bota_frame.status.overrange) or 
                bool(bota_frame.status.invalid) or 
                bool(bota_frame.status.raw)
            )
            self.buffer.status = status_error
            
            # Extract IMU data
            imu_acceleration = list(bota_frame.acceleration[:3])
            imu_angular_rate = list(bota_frame.angular_rate[:3])
            
            # Transform from imu_frame to wrench_frame
            # Angular rate is independent of translation offset
            ang_vel_tf = imu_angular_rate[:]
            
            # Transform acceleration: a_wrench = a_imu + omega x (omega x r)
            # where r is the offset vector from wrench_frame to imu_frame
            r = self._vector_negate(self.imu_offset)  # Vector from wrench to imu
            omega_cross_r = self._cross_product(imu_angular_rate, r)
            centripetal_acc = self._cross_product(imu_angular_rate, omega_cross_r)
            lin_acc_tf = self._vector_add(imu_acceleration, centripetal_acc)

            # Populate force, torque, and transformed IMU data
            self.buffer.force = [float(f) for f in bota_frame.force[:3]]
            self.buffer.torque = [float(t) for t in bota_frame.torque[:3]]
            self.buffer.lin_acc = [float(a) for a in lin_acc_tf]
            self.buffer.ang_vel = [float(w) for w in ang_vel_tf]

            # print(f"Transformed lin_acc: {self.buffer.lin_acc}, ang_vel: {self.buffer.ang_vel}")

            self.buffer.temperature = float(bota_frame.temperature)
            self.buffer.timestamp = float(bota_frame.timestamp)
            
            return True
            
        except Exception as e:
            print(f"Error updating sensor data: {e}")
            return False
    
    def getCachedOutput(self):
        """Get the cached output frame"""
        return self.buffer
    
    def get_cached_output(self):
        """Python-friendly alias for getCachedOutput"""
        return self.getCachedOutput()
    
    # Expose driver methods
    def configure(self):
        return self.driver.configure()
        
    def activate(self):
        return self.driver.activate()
        
    def deactivate(self):
        return self.driver.deactivate()
        
    def shutdown(self):
        return self.driver.shutdown()
        
    def tare(self):
        return self.driver.tare()
        
def create_ft_sensor_hwi(driver, imu_offset=None):
    """
    Factory function to create a BotaFtSensorHWI from an existing driver
    
    Args:
        driver: Configured bota_driver.BotaDriver instance
        imu_offset: IMU offset from wrench_frame to imu_frame [x, y, z] in meters
        
    Returns:
        BotaFtSensorHWI instance
    """
    return BotaFtSensorHWI(driver, imu_offset)


def create_ft_sensor_hwi_from_config(config_path, imu_offset=None):
    """
    Factory function to create a BotaFtSensorHWI from a config file
    
    Args:
        config_path: Path to driver configuration file
        imu_offset: IMU offset from wrench_frame to imu_frame [x, y, z] in meters
        
    Returns:
        BotaFtSensorHWI instance
    """
    try:
        import bota_driver
        driver = bota_driver.BotaDriver(config_path)
        return BotaFtSensorHWI(driver, imu_offset)
    except ImportError:
        raise ImportError("bota_driver package is required to create HWI from config")