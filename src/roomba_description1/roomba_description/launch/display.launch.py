from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ld = LaunchDescription()

    pkg_share = FindPackageShare('roomba_description')

    ld.add_action(DeclareLaunchArgument(name='model', default_value='urdf/aranya6.urdf.xacro',
                                        description='Ruta al URDF relativa al paquete roomba_description'))
    ld.add_action(DeclareLaunchArgument(name='gui', default_value='true', choices=['true', 'false'],
                                        description='Lanzar joint_state_publisher_gui'))
    ld.add_action(DeclareLaunchArgument(name='rvizconfig',
                                        default_value=PathJoinSubstitution([pkg_share, 'rviz', 'roomba.rviz']),
                                        description='Ruta absoluta al fichero de configuración de RViz'))

    # Reutilizamos el launcher genérico de ejemplos de URDF de ROS 2
    ld.add_action(IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('urdf_launch'), 'launch', 'display.launch.py']),
        launch_arguments={
            'urdf_package': 'roomba_description',
            'urdf_package_path': LaunchConfiguration('model'),
            'rviz_config': LaunchConfiguration('rvizconfig'),
            'jsp_gui': LaunchConfiguration('gui')}.items()
    ))

    return ld
