# ROS 2 PPE Assistance Robot V2

## Autonomous Mapping and PPE Patrol

Research prototype for mapping a manufacturing facility, localizing in a saved map, patrolling approved waypoints, detecting missing helmets and safety vests, issuing offline voice alerts, and recording auditable events. The target platform is a Yahboom MicroROS-Pi5 mobile robot running ROS 2 Humble.

> This software is an undergraduate research prototype. It is not a certified industrial safety system and must not replace trained personnel, approved PPE procedures, engineered safeguards, or a hardware emergency stop. Autonomous motion is disabled by default and must only be enabled after mapping, calibration, stationary validation, and supervised low-speed testing.

## What works in this version

- Pure-Python mock demo requiring no ROS, camera, model, or robot.
- ROS 2 Humble packages and custom messages.
- ROS camera topic and generated mock-camera topic.
- Webcam/video input through a standalone runner.
- Replaceable mock and Ultralytics YOLO detectors.
- Geometric helmet/head and vest/torso association.
- Lightweight IoU tracking with stable person IDs.
- Five-state event machine with frame/time confirmation and cooldown.
- Explicit `UNKNOWN` handling that never creates an accusation.
- Nonblocking `espeak-ng` voice queue and a test double.
- Parameterized SQLite event storage and date-organized evidence images.
- Perception-only navigation guard retained from V1.
- Twelve hardware-independent automated tests.
- SLAM Toolbox configuration for manual plant mapping.
- Nav2 + AMCL localization against a saved map.
- Route validation and sequential `NavigateToPose` waypoint patrol.
- LiDAR watchdog that stops patrol on stale or unsafe scan data.
- Nav2 Collision Monitor between navigation velocity and the base.
- Patrol cancellation/pause when a confirmed PPE event occurs.

## Architecture

```mermaid
flowchart LR
    C[Camera or video] --> P[PPE perception]
    P --> O[/ppe/observations]
    O --> D[Decision state machine]
    D --> E[/ppe/events]
    E --> A[Voice alert]
    E --> L[SQLite logger]
    E --> N[Patrol pause]
    S[MS200 LiDAR] --> SLAM[SLAM Toolbox]
    SLAM --> M[Plant map]
    M --> NAV[AMCL and Nav2]
    W[Approved waypoints] --> NAV
    NAV --> CM[Collision Monitor]
    CM --> B[Mobile base]
    S --> CM
```

The Python algorithms are separate from ROS nodes so they can be tested on a normal computer. Hardware topic names and safety thresholds live in YAML.

## Repository

| Package | Responsibility |
|---|---|
| `ppe_interfaces` | `PPEObservation` and `PPEEvent` ROS messages |
| `ppe_perception` | Detectors, association, tracking, pipeline, camera node |
| `ppe_decision` | Confirmation/cooldown state machine and event node |
| `ppe_alert` | Asynchronous offline voice alert |
| `ppe_logger` | SQLite repository and evidence storage |
| `ppe_navigation` | SLAM, AMCL/Nav2, patrol action client, Collision Monitor and LiDAR supervisor |
| `ppe_bringup` | Development/robot launch files and YAML |

## ROS topics

| Topic | Type | Direction |
|---|---|---|
| `/camera/image_raw` | `sensor_msgs/Image` | Input |
| `/ppe/observations` | `ppe_interfaces/PPEObservation` | Perception output |
| `/ppe/events` | `ppe_interfaces/PPEEvent` | Confirmed event |
| `/ppe/system_status` | `std_msgs/String` | Health/error output |
| `/ppe/voice_alert` | `std_msgs/String` | Alert queue status |
| `/scan` | LiDAR input reserved for Nav2 | Future |
| `/odom` | Odometry input reserved for Nav2 | Future |
| `/cmd_vel_nav` | `geometry_msgs/Twist` | Nav2/teleop input to Collision Monitor |
| `/cmd_vel` | `geometry_msgs/Twist` | Filtered output from Collision Monitor to robot base |
| `/ppe/safety_stop` | `std_msgs/Bool` | LiDAR/estop patrol inhibit |
| `/ppe/patrol_status` | `std_msgs/String` | Patrol state and waypoint result |
| `/ppe/emergency_stop` | `std_msgs/Bool` | Software stop request; not a substitute for hardware E-stop |

Confirm the actual Yahboom topics with `ros2 topic list`; the defaults are not assumed to match every vendor image.

## PPE model

Standard COCO weights do not normally contain helmet and safety-vest classes. Supply custom Ultralytics weights whose class names resolve to:

- `person`
- `helmet`
- `safety_vest` (the alias `vest` is normalized)

Without weights, use mock mode. A future version should replace geometric PPE association with pose-assisted or instance-level association.

## Install on Ubuntu 22.04 / ROS 2 Humble

```bash
sudo apt update
sudo apt install ros-humble-desktop ros-humble-cv-bridge python3-colcon-common-extensions \
  python3-rosdep python3-opencv python3-numpy espeak-ng

mkdir -p ~/ppe_ws/src
cp -r ppe_interfaces ppe_perception ppe_decision ppe_alert ppe_logger \
  ppe_navigation ppe_bringup ~/ppe_ws/src/
cd ~/ppe_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

For custom YOLO inference:

```bash
python3 -m pip install ultralytics
```

On Raspberry Pi, benchmark the model before deployment. Prefer a nano-size model and consider NCNN or a Hailo accelerator if latency is excessive.

## Run without ROS

```bash
python3 scripts/run_mock_demo.py
```

Expected behavior: two persistent mock violations are confirmed, two voice messages are captured by the mock adapter, and two rows are stored in `data/mock_events.db`.

Webcam with mock detections:

```bash
python3 scripts/run_video_demo.py --source 0 --mode mock --display
```

Video with custom YOLO weights:

```bash
python3 scripts/run_video_demo.py --source data/demo.mp4 --mode yolo \
  --weights models/ppe_yolo.pt --display
```

Add `--voice` only after installing and testing `espeak-ng`.

## Run ROS mock mode

```bash
source ~/ppe_ws/install/setup.bash
ros2 launch ppe_bringup development.launch.py
```

Inspect activity:

```bash
ros2 topic echo /ppe/observations
ros2 topic echo /ppe/events
sqlite3 data/ppe_events.db 'select event_id, violation_type, timestamp_utc from ppe_events;'
```

## V2 prerequisite: verify the Yahboom base

Before mapping, the vendor base stack must provide:

```text
/scan                sensor_msgs/LaserScan
/odom                nav_msgs/Odometry
/cmd_vel              geometry_msgs/Twist (base input)
odom → base_link      TF
base_link → laser_frame TF
```

Run these checks while the wheels are raised or motion is physically constrained:

```bash
ros2 topic list
ros2 topic hz /scan
ros2 topic hz /odom
ros2 run tf2_ros tf2_echo odom base_link
ros2 run tf2_ros tf2_echo base_link laser_frame
```

The included calibration URDF uses approximate dimensions only. Prefer the Yahboom URDF; otherwise measure the assembled robot and update base size, footprint and LiDAR transform.

## Create the plant map

Mapping is manual and supervised. Start the Yahboom base/driver first, then:

```bash
ros2 launch ppe_navigation mapping.launch.py
```

Drive slowly with teleoperation through every approved corridor and room. Teleoperation must target the Collision Monitor input:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_nav
```

In RViz, verify that scans align with walls, revisit the starting area to close loops, and stop if the map doubles, bends, or drifts. Save the occupancy map:

```bash
mkdir -p ~/ppe_maps
ros2 run nav2_map_server map_saver_cli -f ~/ppe_maps/manufacturing_plant
```

This creates `manufacturing_plant.yaml` and `manufacturing_plant.pgm`. Facility maps can be sensitive; store and share them only with authorization.

## Define the patrol

Copy `ppe_navigation/config/waypoints.example.yaml` and replace the example coordinates using poses selected in the completed map. Every waypoint contains a name, `x`, `y`, `yaw`, and dwell time. Do not place goals inside doorways, near stairs, in forklift lanes, or where the robot blocks an exit.

Validate localization and Nav2 with motion disabled:

```bash
ros2 launch ppe_bringup autonomous_patrol.launch.py \
  map:=$HOME/ppe_maps/manufacturing_plant.yaml \
  route_file:=$HOME/ppe_maps/plant_patrol.yaml
```

Set the initial pose in RViz and send individual Nav2 goals first. Only after supervised validation, explicitly enable patrol:

```bash
ros2 launch ppe_bringup autonomous_patrol.launch.py \
  map:=$HOME/ppe_maps/manufacturing_plant.yaml \
  route_file:=$HOME/ppe_maps/plant_patrol.yaml \
  enable_motion:=true
```

When a confirmed PPE event arrives, the patrol node cancels its active Nav2 goal, pauses for the configured alert interval, and later retries the same waypoint. A LiDAR timeout, invalid scan, close obstacle, or `/ppe/emergency_stop=true` also cancels the active goal.

## Run PPE detection without autonomous patrol

1. Confirm camera, LiDAR, odometry, and velocity topics.
2. Edit `ppe_bringup/config/robot.yaml`.
3. Copy custom PPE weights to the configured path.
4. Keep `dry_run: true`.
5. Test stationary detection and audio before any navigation work.
6. Start:

```bash
ros2 launch ppe_bringup robot.launch.py
```

The older `ppe_navigation_guard` remains available for perception-only operation.

## Parameters

| Parameter | Development default | Meaning |
|---|---:|---|
| `camera_topic` | `/camera/image_raw` | ROS image input |
| `detector_mode` | `mock` | `mock` or `yolo` |
| `weights_path` | empty | Custom PPE model |
| `confidence_threshold` | `0.50` | Detector threshold |
| `violation_confirmation_frames` | `3` | Minimum repeated observations |
| `violation_confirmation_seconds` | `0.40` | Minimum persistence time |
| `alert_cooldown_seconds` | `15.0` | Repeat suppression |
| `enable_voice` | `false` | Enable `espeak-ng` |
| `database_path` | `data/ppe_events.db` | SQLite database |
| `dry_run` | `true` | Perception-only guard default |
| `enable_motion` | `false` | Explicit gate before patrol sends Nav2 goals |
| `stop_distance` | `0.40 m` | Independent LiDAR patrol-stop threshold; calibrate |
| `cmd_vel_topic` | `/cmd_vel` | Reserved motion topic |

Association ratios and tracker thresholds are typed Python configuration values in the MVP and are the next candidates for ROS parameters.

## Tests

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m pytest -q
```

Tests cover PPE association, compliance states, identity persistence/expiry, temporal confirmation, cooldown, compliance restoration, `UNKNOWN`, mock audio, SQLite insertion, route validation, and LiDAR safety decisions.

## Event-state transitions

- `CLEAR` → `VIOLATION_PENDING`: first known violation.
- `VIOLATION_PENDING` → `ALERTED`: both frame and time thresholds pass.
- `ALERTED` → `COOLDOWN`: subsequent violation observations are suppressed.
- Any violation state → `CLEAR`: compliance is restored.
- Any state → `OBSERVING`: PPE status is unknown; no alert is permitted.

Durations use `time.monotonic()`, while stored audit timestamps use UTC.

## Known limitations

- No trained PPE weights are bundled.
- The default association heuristic can assign PPE incorrectly when people overlap.
- The IoU tracker is suitable for an MVP, not dense crowds.
- Evidence capture is available in the standalone video runner; the ROS logger currently stores event metadata only.
- Static-image input can be passed through the video runner only when OpenCV treats the source as a capture; a dedicated image CLI is future work.
- The map, waypoint coordinates, exact footprint and sensor transforms are site/robot-specific and are not bundled as facts.
- Nav2 parameters are conservative starting values, not validated Yahboom calibration.
- A software emergency-stop topic cannot replace a directly wired hardware emergency stop.
- The robot patrols fixed approved waypoints; it does not chase or approach a detected person.
- ROS 2 build must be performed in an Ubuntu 22.04 ROS 2 Humble environment.

## Next research milestones

1. Curate and evaluate a PPE dataset with precision, recall, mAP, confusion matrices, and subgroup/environment analysis.
2. Replace box-center association with pose-aware association.
3. Add calibrated confidence and an explicit human acknowledgement channel.
4. Validate SLAM/Nav2 in simulation, then stationary and supervised low-speed hardware tests.
5. Add keepout/speed-zone masks for forklift lanes, stairs, exits, and restricted rooms.
6. Design and formally test approach-distance constraints before any person-following behavior.
7. Study whether alert wording/timing adapts to human response without creating unsafe or coercive behavior.
