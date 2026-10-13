# Clase 2 — La Roomba se mueve: Gazebo + ros2_control

En la clase 1 escribimos el URDF de la Roomba y lo vimos en RViz. Hoy la vamos a
**simular en Gazebo** y a **controlarla con el teclado**:

- Con `w a s d x q e` se mueve (tracción diferencial).
- Con la tecla **`b`** enciende o apaga el cepillo lateral: **barre**.

Todo el movimiento pasa por **ros2_control**, el mismo sistema que usaría la
Roomba real. Solo cambiaría el "driver" de hardware.

Los paquetes están casi terminados. Faltan **15 huecos** marcados así:

```
======================= TODO 5 =======================
```

y con `___` donde va la respuesta. Cada TODO explica qué hay que poner y trae
pistas. **Entiende por qué va cada cosa**: en el examen no habrá pistas 😉.

---

## 1. Preparar el workspace

```bash
mkdir -p ~/ros2_ws/src
cp -r roomba_gazebo roomba_teleop ~/ros2_ws/src/

cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash

# Instala todo lo que piden los package.xml (Gazebo, ros2_control, controladores...)
sudo rosdep init          # solo la primera vez en el PC (si da error, ya estaba hecho)
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# --symlink-install: los cambios en URDF, YAML, launch y Python se ven sin recompilar
colcon build --symlink-install
source install/setup.bash
```

> Compila aunque haya huecos. Los errores aparecen al **lanzar**.

---

## 2. Qué hay en cada paquete

```
roomba_gazebo/
├── urdf/
│   ├── roomba.urdf.xacro           # El robot + inercias                 (ya puestas)
│   ├── roomba.ros2_control.xacro   # Qué joints controla ros2_control    (TODO 1-3)
│   └── roomba.gazebo.xacro         # Plugin de Gazebo y fricción         (TODO 4-5)
├── config/
│   └── roomba_controllers.yaml     # Qué controladores hay y sus parámetros (TODO 6-10)
├── launch/
│   └── sim.launch.py               # Arranca Gazebo, el robot y los controladores (TODO 11)
├── worlds/salon.sdf                # Un salón con sofá y mesa
└── rviz/roomba_sim.rviz

roomba_teleop/
└── roomba_teleop/teleop_keyboard.py  # Teclado -> cmd_vel y cepillo      (TODO 12-15)
```

### ¿Cómo encaja todo?

```
 teleop_keyboard ──TwistStamped──►  /diff_drive_controller/cmd_vel ─┐
        │                                                          │
        └──Float64MultiArray──►  /side_brush_controller/commands ──┤
                                                                   ▼
                          ┌──────────────── Gazebo ─────────────────────────┐
                          │  plugin gz_ros2_control                         │
                          │   └─ controller_manager (lee el YAML)           │
                          │       ├─ diff_drive_controller  → ruedas        │
                          │       ├─ side_brush_controller  → cepillo       │
                          │       └─ joint_state_broadcaster → /joint_states│
                          │   └─ GazeboSimSystem (hardware = motores sim.)  │
                          └─────────────────────────────────────────────────┘
                                                                   │
        robot_state_publisher ◄── /joint_states ───────────────────┘
               └──► /tf  ──► RViz
```

---

## 3. Orden recomendado y cómo comprobar cada parte

Ve por bloques y **comprueba cada uno antes de pasar al siguiente**.

### Bloque A — Hardware y Gazebo (TODO 1 a 5)

```bash
ros2 launch roomba_gazebo sim.launch.py
```

Aún fallarán los controladores (bloque B), pero la Roomba ya debería aparecer en
el salón. En otra terminal:

```bash
ros2 control list_hardware_interfaces
```

Deben salir `left_wheel_joint/velocity`, `right_wheel_joint/velocity` y
`side_brush_joint/velocity` como *command interfaces*.

### Bloque B — Controladores (TODO 6 a 11)

Relanza la simulación y comprueba:

```bash
ros2 control list_controllers
```

Los tres (`joint_state_broadcaster`, `diff_drive_controller`,
`side_brush_controller`) deben estar **active**. Pruébalos **sin teleop**:

```bash
# Avanzar a 0.2 m/s (hay que publicar sin parar: -r 10 = 10 veces por segundo)
ros2 topic pub -r 10 /diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  "{twist: {linear: {x: 0.2}}}"

# Encender el cepillo a 10 rad/s (basta una vez)
ros2 topic pub --once /side_brush_controller/commands std_msgs/msg/Float64MultiArray \
  "{data: [10.0]}"
```

### Bloque C — Teleop (TODO 12 a 15) · `teleop_keyboard.py`

Con la simulación en marcha, en **otra terminal**:

```bash
source ~/ros2_ws/install/setup.bash
ros2 run roomba_teleop teleop_keyboard
```

| Tecla | Acción |
|-------|--------|
| `w` / `x` | adelante / atrás |
| `a` / `d` | girar a izquierda / derecha |
| `q` / `e` | avanzar girando |
| `s` o espacio | parar |
| **`b`** | **encender / apagar el cepillo** |
| `Ctrl-C` | salir (para el robot y apaga el cepillo) |

La terminal del teleop tiene que estar seleccionada para que lleguen las teclas.

---

## 4. Opciones del launch

```bash
ros2 launch roomba_gazebo sim.launch.py gui:=false   # sin ventana de Gazebo (PC lento)
ros2 launch roomba_gazebo sim.launch.py rviz:=false  # sin RViz
```

---

## 5. Preguntas para pensar

1. Si pones `wheel_radius` el doble de grande, ¿el robot va más rápido o más
   lento de lo que pides? ¿Y qué le pasa a la odometría en RViz?
2. ¿Por qué el teleop publica el `cmd_vel` 10 veces por segundo, pero el
   comando del cepillo solo cuando pulsas `b`?
3. Si quitas el `joint_state_broadcaster` del launch, ¿qué deja de funcionar en RViz?
4. Si tuviéramos la Roomba real, ¿qué fichero(s) cambiarías?
5. La odometría (`/diff_drive_controller/odom`) se calcula con lo que giran las
   ruedas. Si una rueda patina, ¿la odometría se entera? Compara en RViz dónde
   cree el robot que está con dónde está de verdad en Gazebo.

---

## 6. Errores típicos

| Síntoma | Mira... |
|---------|---------|
| El robot aparece pero ningún controlador arranca | Plugin de Gazebo (TODO 4) o hardware (TODO 1) |
| `Loader for controller '...' (type '...') not found` | Tipo mal escrito en el YAML (TODO 6/7) |
| Solo arranca `joint_state_broadcaster` | El spawner se para en el primer controlador que falla: mira el `[ERROR]` anterior |
| Un controlador sale `inactive` o no sale | Nombre distinto en YAML y launch (TODO 11) |
| `NameError: name '___' is not defined` | Queda un hueco en el teleop |
| El teleop publica pero el robot no se mueve | `ros2 topic info -v` del topic: ¿coinciden nombre y tipo? (TODO 12) |
| Pulso `b` y no pasa nada | TODO 14 y 15. Mira `ros2 topic echo /side_brush_controller/commands` |
