cmake_minimum_required(VERSION 3.10)
project(my_cpp_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(example_interfaces REQUIRED)
find_package(my_robot_interfaces REQUIRED)

add_executable(test_node src/my_first_node.cpp)
add_executable(number_publisher src/number_publisher.cpp)
add_executable(number_counter src/number_counter.cpp)
add_executable(reset_counter_client src/reset_counter_client.cpp)

ament_target_dependencies(test_node rclcpp)
ament_target_dependencies(number_publisher rclcpp example_interfaces)
ament_target_dependencies(number_counter rclcpp example_interfaces my_robot_interfaces)
ament_target_dependencies(reset_counter_client rclcpp my_robot_interfaces)

install(TARGETS
 test_node
 number_publisher
 number_counter
 reset_counter_client
 DESTINATION lib/${PROJECT_NAME}/
)

ament_package()
