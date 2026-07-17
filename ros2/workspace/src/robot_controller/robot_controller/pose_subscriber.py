#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose

class PoseSubscriberNode(Node):
    
    def __init__(self):
        super().__init__("pose_subscriber")
        # create a listener
        # data type, topic name, callback, queue size
        self.pose_subscriber_ = self.create_subscription(Pose, "/turtle1/pose", self.pose_callback, 10)
        
    # ros2 topic list
    # ros2 topic info /turtle1/pose
    # ros2 interface show turtlesim/msg/Pose
    # ros2 topic echo /turtle1/pose
    def pose_callback(self, msg: Pose):
        self.get_logger().info("(" + str(msg.x) + ", " + str(msg.y) + ")")

def main(args=None):
    # initialize ros2 communications
    rclpy.init(args=args)
    node = PoseSubscriberNode()
    rclpy.spin(node) # rimane in esecuzione
    rclpy.shutdown()
