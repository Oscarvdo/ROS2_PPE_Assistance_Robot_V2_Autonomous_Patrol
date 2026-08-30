# Plant maps

Do not commit a real facility map without authorization; it may expose sensitive layout information.

Create a map while manually driving the robot:

```bash
ros2 launch ppe_navigation mapping.launch.py
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=cmd_vel_nav
```

After closing loops and reviewing the map in RViz:

```bash
mkdir -p ~/ppe_maps
ros2 run nav2_map_server map_saver_cli -f ~/ppe_maps/manufacturing_plant
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph \
  "{filename: '$HOME/ppe_maps/manufacturing_plant'}"
```

The first command creates `.yaml` and `.pgm`; serialization preserves the pose graph for later refinement.
