# Four stages from the same scene

**Rosbag4, frame 100, 640 × 480.** All four views show the same front-facing track scene and use the August 25, 150-epoch checkpoint included in this repository.

| 1. Blue YOLO detection | 2. Initial binary mask |
| --- | --- |
| ![Blue YOLO segmentation overlay](01-blue-detection.jpg) | ![Initial binary obstacle mask](02-initial-mask.jpg) |

| 3. Geometric wall correction | 4. Drivable region |
| --- | --- |
| ![Wall mask after gap filling and extension](03-geometric-correction.png) | ![Final drivable-region mask](04-drivable-region.jpg) |

White marks detected obstacles. In the final view, gray marks the region flood-filled from the bottom-center seed; black is the remaining area.
See [provenance.json](provenance.json) for exact original paths, checksums, and the camera-message timestamp.

Within each, dated experiments use `YYYY-MM-DD/output_results_rosbags/`. 
