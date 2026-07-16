FROM ros:jazzy

RUN apt-get update && apt-get install -y \
    ros-jazzy-desktop \
    tmux \
    git \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

WORKDIR /workspace
