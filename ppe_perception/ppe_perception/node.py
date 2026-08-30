from __future__ import annotations

import json

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from cv_bridge import CvBridge
from ppe_interfaces.msg import PPEObservation

from .detectors import MockDetector, UltralyticsDetector
from .pipeline import PerceptionPipeline


class PPEPerceptionNode(Node):
    def __init__(self) -> None:
        super().__init__("ppe_perception")
        self.declare_parameter("camera_topic", "/camera/image_raw")
        self.declare_parameter("weights_path", "")
        self.declare_parameter("detector_mode", "mock")
        self.declare_parameter("confidence_threshold", 0.5)
        self.declare_parameter("source", "ros_camera")
        camera_topic = self.get_parameter("camera_topic").value
        mode = self.get_parameter("detector_mode").value
        if mode == "mock":
            detector = MockDetector()
        else:
            detector = UltralyticsDetector(
                self.get_parameter("weights_path").value,
                float(self.get_parameter("confidence_threshold").value),
            )
        self.pipeline = PerceptionPipeline(detector)
        self.bridge = CvBridge()
        self.publisher = self.create_publisher(PPEObservation, "/ppe/observations", 10)
        self.status = self.create_publisher(String, "/ppe/system_status", 10)
        self.create_subscription(Image, camera_topic, self.on_image, 10)
        self.get_logger().info(f"PPE perception listening on {camera_topic}; mode={mode}")

    def on_image(self, message: Image) -> None:
        try:
            image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
            observations = self.pipeline.process(
                image, str(self.get_parameter("source").value)
            )
            for item in observations:
                output = PPEObservation()
                output.header = message.header
                output.track_id = item.track_id
                output.person_confidence = item.person_confidence
                output.person_xmin = int(item.person_box.xmin)
                output.person_ymin = int(item.person_box.ymin)
                output.person_xmax = int(item.person_box.xmax)
                output.person_ymax = int(item.person_box.ymax)
                output.helmet_detected = bool(item.helmet_detected)
                output.helmet_status_known = item.helmet_detected is not None
                output.helmet_confidence = item.helmet_confidence
                output.vest_detected = bool(item.vest_detected)
                output.vest_status_known = item.vest_detected is not None
                output.vest_confidence = item.vest_confidence
                output.compliance_state = item.compliance_state.value
                output.source = item.source
                self.publisher.publish(output)
        except Exception as exc:
            self.get_logger().error(f"Image processing failed: {exc}")
            status = String()
            status.data = json.dumps({"component": "perception", "status": "error", "detail": str(exc)})
            self.status.publish(status)


def main() -> None:
    rclpy.init()
    node = PPEPerceptionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
