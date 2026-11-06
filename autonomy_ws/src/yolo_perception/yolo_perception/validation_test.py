from ultralytics import YOLO

model = YOLO("22_08_runs_ep40_sz640_adamW_lr0.0001_wd0.0005_Fz0_GS50_noauto_hsv_translate0.1_scale0.3_patience15_maskratio2.onnx")

model.predict(
    source="Val_images/1163_png.rf.YpXGSNmCl7wsEdkFZCzM.png",
    imgsz=640,
    conf=0.001,
    retina_masks=True,
    end2end=False,
    save=True,
    project="runs/compare",
    name="end2endFalse_640",

)

model.predict(
    source="Val_images/1163_png.rf.YpXGSNmCl7wsEdkFZCzM.png",
    imgsz=640,
    conf=0.001,
    retina_masks=True,
    save=True,
    project="runs/compare",
    name="end2endTrue_640",
)