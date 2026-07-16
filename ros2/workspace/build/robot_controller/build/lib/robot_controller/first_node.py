#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

class MyNode(Node):
    
    def __init__(self):
        super().__init__("first_node")
        self.get_logger().info("Hello from ROS2")

def main(args=None):
    # initialize ros2 communications
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node) # rimane in esecuzione
    rclpy.shutdown()

if __name__ == '__main__':
    main()