from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np


def visualize_yolo_segmentation(
    image_path,
    label_path,
    output_path="annotation_overlay.jpg",
    class_names=None,
    alpha=0.45,
    draw_boxes=True,
    draw_points=False,
):
    """
    Visualize YOLO instance-segmentation polygon annotations.

    Parameters
    ----------
    image_path : str or Path
        Path to the source image.
    label_path : str or Path
        Path to the matching YOLO segmentation .txt file.
    output_path : str or Path
        Where to save the visualized image.
    class_names : dict, optional
        Example: {0: "Car", 1: "Wall"}.
    alpha : float
        Polygon transparency from 0 to 1.
    draw_boxes : bool
        Draw the bounding box derived from each polygon.
    draw_points : bool
        Draw every polygon vertex.
    """

    image_path = Path(image_path)
    label_path = Path(label_path)
    output_path = Path(output_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if not label_path.exists():
        raise FileNotFoundError(f"Label not found: {label_path}")

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"OpenCV could not read: {image_path}")

    height, width = image.shape[:2]
    overlay = image.copy()

    #Four points
    t1=[180, 340]
    bl=[70,472]
    tr=[438,340]
    br=[538, 472]
    
    cv2.circle(image, t1, 5, (0,0,255), -1)
    cv2.circle(image, bl, 5, (0,0,255), -1)
    cv2.circle(image, tr, 5, (0,0,255), -1)
    cv2.circle(image, br, 5, (0,0,255), -1)

    cv2.imwrite("autonomy_ws/src/yolo_perception/image_2.jpg", image)

    if class_names is None:
        class_names = {}

    # BGR colors because OpenCV uses BGR.
    palette = [
        (255, 255, 0),    # cyan
        (0, 165, 255),    # orange
        (255, 0, 255),    # magenta
        (0, 255, 0),      # green
        (255, 0, 0),      # blue
        (0, 255, 255),    # yellow
    ]

    annotations = []

    with label_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            values = line.split()

            try:
                class_id = int(float(values[0]))
                coordinates = np.asarray(
                    values[1:],
                    dtype=np.float32,
                )
            except ValueError as error:
                print(f"Skipping invalid row {line_number}: {error}")
                continue

            if len(coordinates) < 6:
                print(
                    f"Skipping row {line_number}: "
                    "a polygon needs at least three points."
                )
                continue

            if len(coordinates) % 2 != 0:
                print(
                    f"Skipping row {line_number}: "
                    f"found an odd number of coordinates "
                    f"({len(coordinates)})."
                )
                continue

            normalized_points = coordinates.reshape(-1, 2)

            # Warn about invalid normalized coordinates.
            if np.any(normalized_points < 0) or np.any(normalized_points > 1):
                print(
                    f"Warning: row {line_number} contains coordinates "
                    "outside the normalized range [0, 1]."
                )

            pixel_points = normalized_points.copy()
            pixel_points[:, 0] *= width
            pixel_points[:, 1] *= height

            pixel_points = np.rint(pixel_points).astype(np.int32)

            # Prevent x=1 or y=1 from becoming width or height.
            pixel_points[:, 0] = np.clip(
                pixel_points[:, 0], 0, width - 1
            )
            pixel_points[:, 1] = np.clip(
                pixel_points[:, 1], 0, height - 1
            )

            color = palette[class_id % len(palette)]

            annotations.append(
                {
                    "class_id": class_id,
                    "points": pixel_points,
                    "color": color,
                    "line_number": line_number,
                }
            )

            # Filled segmentation annotation.
            cv2.fillPoly(
                overlay,
                [pixel_points.reshape(-1, 1, 2)],
                color,
            )

    # Blend polygon fills with the source image.
    visualized = cv2.addWeighted(
        overlay,
        alpha,
        image,
        1.0 - alpha,
        0,
    )

    # Draw outlines, bounding boxes, class names, and optional vertices.
    for instance_number, annotation in enumerate(annotations):
        class_id = annotation["class_id"]
        points = annotation["points"]
        color = annotation["color"]

        contour = points.reshape(-1, 1, 2)

        cv2.polylines(
            visualized,
            [contour],
            isClosed=True,
            color=color,
            thickness=3,
            lineType=cv2.LINE_AA,
        )

        x_min = int(points[:, 0].min())
        y_min = int(points[:, 1].min())
        x_max = int(points[:, 0].max())
        y_max = int(points[:, 1].max())

        if draw_boxes:
            cv2.rectangle(
                visualized,
                (x_min, y_min),
                (x_max, y_max),
                color,
                thickness=2,
            )

        if draw_points:
            for x, y in points:
                cv2.circle(
                    visualized,
                    (int(x), int(y)),
                    radius=3,
                    color=(0, 0, 255),
                    thickness=-1,
                )

        class_name = class_names.get(class_id, f"class_{class_id}")
        label_text = f"{class_name} #{instance_number + 1}"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65
        thickness = 2

        (text_width, text_height), baseline = cv2.getTextSize(
            label_text,
            font,
            font_scale,
            thickness,
        )

        text_x = x_min
        text_y = max(y_min, text_height + baseline + 4)

        cv2.rectangle(
            visualized,
            (text_x, text_y - text_height - baseline - 4),
            (text_x + text_width + 6, text_y + 2),
            color,
            thickness=-1,
        )

        cv2.putText(
            visualized,
            label_text,
            (text_x + 3, text_y - baseline),
            font,
            font_scale,
            (0, 0, 0),
            thickness,
            cv2.LINE_AA,
        )

        print(
            f"Instance {instance_number + 1}: "
            f"class={class_name}, "
            f"vertices={len(points)}, "
            f"box=[{x_min}, {y_min}, {x_max}, {y_max}]"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not cv2.imwrite(str(output_path), visualized):
        raise IOError(f"Could not save result to: {output_path}")

    print(f"\nSaved visualization to: {output_path}")
    print(f"Image dimensions: {width} × {height}")
    print(f"Annotations found: {len(annotations)}")

    # Matplotlib displays the image correctly in notebooks and Colab.
    plt.figure(figsize=(16, 9))
    plt.imshow(cv2.cvtColor(visualized, cv2.COLOR_BGR2RGB))
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    return visualized


# Update these paths.
visualize_yolo_segmentation(
    image_path="autonomy_ws/src/yolo_perception/output_results_3.jpg",
    label_path="Val_labels/1163_png.rf.YpXGSNmCl7wsEdkFZCzM.txt",
    output_path="Val_output/1163_annotated.jpg",
    class_names={
        0: "Car",
        1: "Wall",
    },
    alpha=0.45,
    draw_boxes=True,
    draw_points=True,
)