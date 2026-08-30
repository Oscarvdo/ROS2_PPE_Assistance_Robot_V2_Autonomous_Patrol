from __future__ import annotations

import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image


class MockCameraNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_mock_camera")
        self.declare_parameter("camera_topic", "/camera/image_raw")
        self.declare_parameter("fps", 5.0)
        self.publisher = self.create_publisher(
            Image, str(self.get_parameter("camera_topic").value), 10
        )
        self.bridge = CvBridge()
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        fps = max(0.2, float(self.get_parameter("fps").value))
        self.create_timer(1.0 / fps, self.publish_frame)

    def publish_frame(self) -> None:
        message = self.bridge.cv2_to_imgmsg(self.frame, encoding="bgr8")
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "mock_camera"
        self.publisher.publish(message)


def main() -> None:
    rclpy.init()
    node = MockCameraNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
