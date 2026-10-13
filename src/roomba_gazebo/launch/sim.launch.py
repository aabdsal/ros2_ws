"""Simula la Roomba en Gazebo con ros2_control.

Orden de arranque:
  1. Gazebo.
  2. robot_state_publisher con el URDF generado por xacro (/robot_description).
  3. ros_gz_sim create: lee /robot_description y mete el robot en Gazebo.
     Al aparecer el robot, el plugin gz_ros2_control arranca el
     controller_manager.
  4. Cuando el robot ya está dentro, los spawners cargan y activan los
     controladores del YAML.
  5. Puente /clock de Gazebo a ROS para que todos usen el tiempo simulado.

El teleop se lanza aparte, en otra terminal, porque necesita leer el teclado:
  ros2 run roomba_teleop teleop_keyboard
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('roomba_gazebo')

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')

    declare_args = [
        DeclareLaunchArgument('world', default_value=PathJoinSubstitution([pkg_share, 'worlds', 'salon.sdf']),
                              description='Ruta absoluta al mundo de Gazebo'),
        DeclareLaunchArgument('gui', default_value='true', choices=['true', 'false'],
                              description='Abrir la ventana de Gazebo (false = solo servidor, más ligero)'),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false'],
                              description='Abrir RViz'),
    ]

    # xacro -> URDF.
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg_share, 'urdf', 'roomba.urdf.xacro'])]),
        value_type=str)

    # 1. Gazebo.
    gazebo = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
        launch_arguments={
            'gz_args': [world, ' -r -v 1', PythonExpression(["'' if '", gui, "' == 'true' else ' -s'"])],
            'on_exit_shutdown': 'true',
        }.items())

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
        arguments=['-topic', 'robot_description', '-name', 'roomba', '-z', '0.01'],
        output='screen')

    controllers_yaml = PathJoinSubstitution([
        pkg_share, 'config', 'roomba_controllers.yaml'
    ])

    # 4. Spawners: cargan y activan cada controlador del YAML por su nombre.
    #    Esperamos a que spawn_robot termine (= robot dentro de Gazebo).
    #
    # ======================= TODO 11 =======================
    # Pasa al spawner la lista con los NOMBRES de los tres controladores
    # que has declarado en config/roomba_controllers.yaml (los nombres, no
    # los tipos). Un spawner puede cargar varios de golpe.
    # Si falta el joint_state_broadcaster, ¿qué dejarás de ver en RViz?)
    controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', 'diff_drive_controller',],  # <- aquí
        output='screen')

    start_controllers = RegisterEventHandler(
        OnProcessExit(target_action=spawn_robot, on_exit=[controller_spawner]))

    # 5. Reloj de Gazebo -> ROS.
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_share, 'rviz', 'roomba_sim.rviz'])],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(rviz)
        )

    return LaunchDescription(declare_args + [
        gazebo,
        robot_state_publisher,
        spawn_robot,
        start_controllers,
        clock_bridge,
        rviz_node,
    ])
