cmake_minimum_required(VERSION 3.10)
project(roomba_gazebo)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf config launch worlds rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
