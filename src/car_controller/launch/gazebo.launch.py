from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, ExecuteProcess, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnShutdown

import os
import sys

def generate_launch_description():
    pkg_share = FindPackageShare('car_controller')

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')

    declare_args = [
        DeclareLaunchArgument('world', default_value=PathJoinSubstitution([pkg_share, 'world', 'salon.sdf']),
                              description='Ruta absoluta al mundo de Gazebo'),
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false'],
                              description='Abrir la ventana de Gazebo (false = solo servidor, más ligero)'),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false'],
                              description='Abrir RViz'),
    ]

    # xacro -> URDF.
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg_share, 'urdf', 'car.urdf.xacro'])]),
        value_type=str)
    
    package_share = get_package_share_directory('car_controller')
    resource_path = os.path.dirname(package_share)

    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            resource_path,
            ':',
            os.environ.get('GZ_SIM_RESOURCE_PATH', '')
        ]
    )

    gz_mode = ''
    if(sys.platform == "darwin"):
        gz_mode = ' -s'
    
    # 1. Gazebo.
    gazebo = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={
            'gz_args': [world, ' -r -v 1', gz_mode],
            'on_exit_shutdown': 'true',
        }.items())

    # Gui para iniciar, fuck mac
    gazebo_gui = ExecuteProcess(
        cmd=['gz', 'sim', '-g'],
        output='screen'
    ) if sys.platform == 'darwin' else None

    cerrar_gazebo = RegisterEventHandler(
         OnShutdown(
              on_shutdown=[
                   ExecuteProcess(
                        cmd=['pkill', '-f', 'gz sim.*-s'],
                        output='screen',
                   )
              ])
    )
    # 2. Publica /robot_description y los TF a partir de /joint_states.
    robot_state_publisher = Node(
        package='robot_state_publisher', # Paquete que contiene el nodo
        executable='robot_state_publisher', # Nodo a ejecutar
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}], # Parámetros que le pasamos al nodo
        output='screen' # Salida por pantalla
        )

    # 3. Crea el robot en Gazebo a partir del topic /robot_description.
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'car', '-z', '0.01'],
        output='screen')

    controllers_yaml = PathJoinSubstitution([
        pkg_share, 'config', 'car_controller.yaml'
    ])

    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', 'diff_drive_controller',],  # <- aquí
        output='screen'
        )

    start_controllers = RegisterEventHandler(
        OnProcessExit(target_action=spawn_robot, on_exit=[controller_spawner]))

    # 5. Reloj de Gazebo -> ROS.
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
        )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_share, 'rviz', 'car_controller.rviz'])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(rviz)
        )

    ld = LaunchDescription(declare_args)

    ld.add_action(gazebo_resource_path)
    ld.add_action(gazebo)

    if gazebo_gui is not None:
            ld.add_action(gazebo_gui)
    
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn_robot)
    ld.add_action(start_controllers)
    ld.add_action(clock_bridge)
    ld.add_action(rviz_node)

    ld.add_action(cerrar_gazebo)
    
    return ld