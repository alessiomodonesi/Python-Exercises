#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class DrawCircleNode(Node):
    
    def __init__(self):
        super().__init__("draw_circle")
        # create a publisher
        # data type, topic name, queue size
        self.cmd_vel_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        # create a timer
        self.timer = self.create_timer(0.5, self.send_velocity_command)
        self.get_logger().info("Draw circle node has been started")
    
    # ros2 topic list
    # ros2 topic info /turtle1/cmd_vel
    # ros2 interface show geometry_msgs/msg/Twist
    # ros2 topic echo /turtle1/cmd_vel
    def send_velocity_command(self):
        msg = Twist()
        msg.linear.x = 2.0
        msg.angular.z = 1.0
        # publish the message
        self.cmd_vel_pub.publish(msg)

def main(args=None):
    # initialize ros2 communications
    rclpy.init(args=args)
    node = DrawCircleNode()
    rclpy.spin(node) # rimane in esecuzione
    rclpy.shutdown()
