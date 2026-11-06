# YOLO Driven Racer

## Included

- `autonomy_ws/src`: `autonomy_core`, `yolo_detection`, `yolo_perception`, `follow_the_gap_crude`, and `slam_mapping`.
- `subsystem_ws`: VESC drivers, camera nodes, command mux, and teleoperation.
- 150-epoch YOLO26n segmentation checkpoint at the repository root.
- Rosbag4 and rosbag2, stored losslessly as gzip files in Git LFS.

## Model

```text
25_08_runs_ep150_sz640_adamW_lr0.001_lrf_0.1_wd0.0005_Fz10_GS50_noauto_hsv_translate0.1_scale0.3_Coslr_fromtheinitialweight.onnx
```
YOLO26n segmentation, classes `0: Car` and `1: Wall`, and 640-pixel inference. The drivable-region node selects this model with confidence a confidence. 

## Example masks

[View four stages from the same rosbag4 scene](docs/images/rosbag4-frame-0100/README.md): blue YOLO detection, initial binary mask, geometric wall correction, and the final drivable region. The images share frame 100; their historical run sources and the exported intermediate are documented with the images.

## Restore the rosbags

Install Git LFS first, then:

```bash
git lfs install
git clone https://github.com/SamaviaJaffery/yolo-driven-racer.git
cd yolo-driven-racer
git lfs pull
python3 scripts/restore_rosbags.py
```

Restore only one with `python3 scripts/restore_rosbags.py rosbag4`. SHA-256 verification reconstructs the original `.db3` files referenced by `metadata.yaml`.

| Bag | Camera frames | Duration | Original size |
| --- | ---: | ---: | ---: |
| rosbag4 | 797 | 53 seconds | 711 MiB |
| rosbag2 | 3,080 | 205 seconds | 2.67 GiB |

Both contain `/camera/camera/color/image_raw`. Rosbag4 also contains LiDAR and odometry; rosbag2 contains camera IMU messages. They were the top two in the previously counted named result folders.

Compression keeps each bag below the [GitHub Free/Pro LFS limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage). Ordinary Git files are limited to [100 MiB](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). Restored bags need about 3.4 GiB in addition to compressed downloads.

## Dependencies and build

A ROS 2 development environment, rosdep, and colcon are required. Source your installed ROS distribution before these commands. Python inference dependencies were smoke-tested with Python 3.10.

```bash
python3 -m pip install -r requirements-yolo.txt
cd subsystem_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
cd ../autonomy_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
cd ..
```

Initialize rosdep first if your ROS environment has not already done so. ROS dependencies include `rclpy`, `cv_bridge`, `sensor_msgs`, `nav_msgs`, `ackermann_msgs`, `vision_msgs`, and the declared subsystem drivers. Hardware setup is described in `subsystem_ws/README.md`.

After fixing the runtime blockers below, run from the repository root with both overlays sourced:

```bash
ros2 run yolo_detection yolo_detection_node --ros-args -p use_rosbags:=true -p rosbag_dir_name:=rosbags/rosbag4
```

The node starts bag playback internally. Change the bag parameter to `rosbags/rosbag2` for the second recording. The annotation/tracking entry point is `ros2 run yolo_perception yolo_node`; explicitly pass `-p model_name:=<included checkpoint filename>` because its saved default selects a different model.

The subsystem entry point is `ros2 launch subsystem_stack bringup_launch.py`. The custom camera node publishes `/camera/color/image_raw`; remap it to the YOLO input `/camera/camera/color/image_raw` when using that camera.


