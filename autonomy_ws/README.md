# Autonomy workspace

Contains `autonomy_core`, `yolo_detection`, `yolo_perception`, `follow_the_gap_crude`, and `slam_mapping`. The original `follow_the_gap` package is excluded.

See the [repository README](../README.md) for the model, bag restoration, builds, and existing runtime blockers.

The experimental camera path is:

```text
camera -> yolo_detection -> /yolo/drivable_mask
       -> follow_the_gap_crude -> /drive -> subsystem mux -> VESC
```

This source snapshot is not yet a validated end-to-end driving stack.
