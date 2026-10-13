"""Teleop de teclado para la Roomba.

Publica:
  /diff_drive_controller/cmd_vel      geometry_msgs/TwistStamped  (moverse)
  /side_brush_controller/commands     std_msgs/Float64MultiArray  (barrer)

Parámetros (ros2 run ... --ros-args -p nombre:=valor):
  linear_speed   velocidad lineal en m/s       (0.3)
  angular_speed  velocidad angular en rad/s    (1.5)
  brush_speed    velocidad del cepillo, rad/s  (12.0)
"""

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

HELP = """
Control de la Roomba
---------------------------
        q    w    e
        a    s    d
             x

  w/x : adelante / atrás
  a/d : girar a la izquierda / derecha
  q/e : avanzar girando
  s o espacio : parar

  b : encender / apagar el cepillo (barrer)

  CTRL-C para salir
"""

MOVE_KEYS = {
    'w': (1, 0),
    'x': (-1, 0),
    'a': (0, 1),
    'd': (0, -1),
    'q': (1, 1),
    'e': (1, -1),
    's': (0, 0),
    ' ': (0, 0),
}


class TeleopKeyboard(Node):

    def __init__(self):
        super().__init__('roomba_teleop_keyboard')
        self.linear_speed = self.declare_parameter('linear_speed', 0.3).value
        self.angular_speed = self.declare_parameter('angular_speed', 1.5).value
        self.brush_speed = self.declare_parameter('brush_speed', 12.0).value

        # ======================= TODO 12 =======================
        # Publisher para mover el robot.
        #   - El diff_drive_controller escucha en /<nombre_controlador>/cmd_vel
        #   - En Jazzy el tipo es TwistStamped (ya está importado arriba).
        # Compruébalo con la simulación en marcha:
        #   ros2 topic list -t | grep cmd_vel
        self.cmd_vel_pub = self.create_publisher(TwistStamped, 'diff_drive_controller/cmd_vel', 10)

        # ======================= TODO 13 =======================
        # Publisher para el cepillo.
        #   - Un JointGroupVelocityController escucha en /<nombre_controlador>/commands
        #   - El tipo es un vector de float64: Float64MultiArray.
        self.brush_pub = self.create_publisher(Float64MultiArray, 'side_brush_controller/commands', 10)

        self.linear = 0.0
        self.angular = 0.0
        self.brushing = False

    def handle_key(self, key):
        if key in MOVE_KEYS:
            lin, ang = MOVE_KEYS[key]
            self.linear = lin * self.linear_speed
            self.angular = ang * self.angular_speed
        # ======================= TODO 14 =======================
        # Tecla B: encender / apagar el cepillo.
        #   - Si la tecla es 'b' o 'B', invierte self.brushing (True <-> False)
        #   - y llama a self.publish_brush() para mandar la nueva velocidad.
        # Aquí no hace falta publicar continuamente: el controlador del
        # cepillo mantiene la última velocidad que le mandamos.
        if key == 'b' or key == 'B':
            self.brushing = not self.brushing
            self.publish_brush()


    def publish_cmd_vel(self):
        msg = TwistStamped()
        # Dejamos header.stamp a 0 A PROPÓSITO: el controlador vive en el
        # tiempo de Gazebo (/clock) y este nodo en el del PC. Si sellamos con
        # la hora del PC, el controlador cree que el mensaje es "del futuro"
        # y el cmd_vel_timeout nunca salta. Con stamp = 0 el controlador lo
        # sella él mismo al recibirlo (avisa una vez en el log de Gazebo).
        msg.header.frame_id = 'base_footprint'
        msg.twist.linear.x = self.linear
        msg.twist.angular.z = self.angular
        self.cmd_vel_pub.publish(msg)

    def publish_brush(self):
        msg = Float64MultiArray()
        # ======================= TODO 15 =======================
        # msg.data es una LISTA con una velocidad (rad/s) por cada joint del
        # controlador, en el orden del YAML. Aquí solo hay uno.
        #   - Barriendo (self.brushing True): self.brush_speed
        #   - Apagado:                        0.0

        msg.data = [self.brush_speed if self.brushing else 0.0]

        self.brush_pub.publish(msg)

    def status(self):
        brush = 'BARRIENDO' if self.brushing else 'apagado'
        return (f'\rlineal {self.linear:+.2f} m/s | angular {self.angular:+.2f} rad/s '
                f'| cepillo: {brush:<10}')


def read_key(timeout):
    """Devuelve la tecla pulsada o '' si no se pulsa nada en `timeout` s."""
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    return sys.stdin.read(1) if ready else ''


def main():
    rclpy.init()
    node = TeleopKeyboard()
    old_settings = termios.tcgetattr(sys.stdin)
    print(HELP)
    try:
        # cbreak: las teclas llegan una a una, sin esperar al Enter.
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            key = read_key(0.1)
            if key == '\x03':  # CTRL-C
                break
            node.handle_key(key)
            # Publicamos siempre (unas 10 veces por segundo): si el
            # controlador deja de recibir cmd_vel durante cmd_vel_timeout,
            # para el robot por seguridad.
            node.publish_cmd_vel()
            print(node.status(), end='', flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        # Al salir: robot parado, cepillo apagado y terminal como estaba.
        node.linear = node.angular = 0.0
        node.brushing = False
        node.publish_cmd_vel()
        node.publish_brush()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
