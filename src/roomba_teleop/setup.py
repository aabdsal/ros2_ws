from setuptools import find_packages, setup

package_name = 'roomba_teleop'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Enric Talens',
    maintainer_email='enricxz@gmail.com',
    description='Teleop de teclado para la Roomba: moverse y barrer con la tecla B.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'teleop_keyboard = roomba_teleop.teleop_keyboard:main',
        ],
    },
)
