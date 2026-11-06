import rclpy
from rclpy.node import Node
from ultralytics import YOLO
from PIL import Image as PILImage
from autonomy_core.base_drive_node import BaseDriveNode
from cv_bridge import CvBridge, CvBridgeError
import subprocess
from sensor_msgs.msg import Image 
from ultralytics.utils.plotting import Annotator
import os
import csv
from datetime import datetime


class YOLONode(Node):

    def __init__(self):

        super().__init__('yolo_node')
        self.declare_parameter('use_rosbags', True) #update this if there's no real-time input and the data is coming from rosbags (testing)
        self.declare_parameter('rosbag_dir_name', "rosbags/rosbag4") #update this with the directory name
        self.declare_parameter('count', 0)
        #self.declare_parameter('model_name', "25_08_runs_ep150_sz640_adamW_lr0.001_lrf_0.1_wd0.0005_Fz10_GS50_noauto_hsv_translate0.1_scale0.3_Coslr_fromtheinitialweight.onnx")
        self.declare_parameter('model_name', "6_09_runs_ep150_sz640_adamW_batch32_lr0.001_lrf_0.1_wd0.0005_Fz10_noauto_hsv_translate0.1_scale0.3_Coslr_fromtheinitialweight_augmenteddata.onnx")
        self.model_name= self.get_parameter('model_name').value
        self.model=YOLO(self.model_name, task='segment')
        self.bridge= CvBridge()
        self.image_sub= self.create_subscription(Image, "/camera/camera/color/image_raw", self.rosbag_to_cv, 10)
        self.detection_pub= self.create_publisher(Image, "/yolo/annotated", 10)

        self.car_count=0
        self.total_detections=0
        self.wall_count=0
        self.frames_with_wall=0
    
        
        self.count=self.get_parameter('count').value 
    
        self.data_stream_selection()
      
      

    def data_stream_selection(self):
        use_rosbags= self.get_parameter('use_rosbags').value

        if use_rosbags==True:
             self.rosbag_dir_name= self.get_parameter('rosbag_dir_name').value
             self.get_logger().info("Playing back rosbag")
             subprocess.Popen(['ros2', 'bag', 'play', self.rosbag_dir_name, '--rate', '0.1'])
           
    
             

        else:
            self.image_data= BaseDriveNode(self.params)

    def rosbag_to_cv(self, msg:Image):
        try:
            self.get_logger().info("Image callback triggered")
            self.get_logger().info(f"Image size: {msg.width} x {msg.height}")
            self.get_logger().info(f"Encoding: {msg.encoding}")
            self.get_logger().info(f"Data length: {len(msg.data)}")
            cv_image=self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.yolo_inference(cv_image)
            #cv2.imshow('camera_image',cv_image)
         
        except CvBridgeError as e:
            self.get_logger().info(e)

    
    def yolo_inference(self, cv_image):

         
        #results = self.model.predict(cv_image, conf=0.01, seed=42)
        results = self.model.track(cv_image, conf=0.01, seed=42, persist=True)
        #results = self.model.predict(cv_image, seed=42)
        
        today = datetime.now().strftime("%Y-%m-%d")
        self.save_directory= f"autonomy_ws/src/yolo_perception/{today}/output_results_{self.rosbag_dir_name}_{self.model_name}_track"
        os.makedirs(self.save_directory, exist_ok=True)

        #saving them in image format
        self.count+=1
        for r in results:
           im_array=r.plot(  masks=True,
                             boxes=True,
                             labels=False,
                             conf=True,)
           
           #self.get_logger().info(f"YOLO plot output shape: {im_array}")
           im=PILImage.fromarray(im_array[...,::-1])  
           #img_msg= cv2.imread(im)
           
           image_path= os.path.join(self.save_directory, f"output_results_{self.count}.jpg")
           im.save(image_path)
           

           #im_array_np = np.ascontiguousarray(im_array).astype(np.uint8)
           #rgb_image = cv2.cvtColor(im_array_np, cv2.COLOR_BGR2RGB)
           #img_msg=self.bridge.cv2_to_imgmsg(rgb_image, encoding="rgb8")   
           #self.detection_pub.publish(img_msg)    
           
           msg = Image()
           msg.header.stamp = self.get_clock().now().to_msg()
           msg.header.frame_id = "camera_color_optical_frame"

           msg.height = im_array.shape[0]
           msg.width = im_array.shape[1]

        # Use rgb8 first because your original camera topic was rgb8
           msg.encoding = "bgr8"

           msg.is_bigendian = 0
           msg.step = msg.width * 3
           msg.data = im_array.tobytes()

           self.detection_pub.publish(msg)
           self.get_logger().info("Published YOLO annotated image")
        
        self.extracting_details(results)

    def extracting_details(self, results):
        
        filepath= os.path.join(self.save_directory, 'summary.csv')
        
        class_names= {
           0: 'car',
           1: 'wall'
        }

        wall_found=False
        with open(filepath, 'a', newline="",encoding='utf-8') as file:
            writer=csv.writer(file)
            for r in results:
                print(r.boxes)
                
                if r.boxes is None or len(r.boxes)==0:
                    writer.writerow(["no detection", "", ""])
                    self.total_detections +=1
                    continue

                class_id = r.boxes.cls.int()
                confidence=r.boxes.conf

                for class_id, confidence in zip(class_id, confidence):
                    class_id=int(class_id.item())
                    confidence=float(confidence.item())
                    class_name= class_names.get(
                        class_id, f"Unkown Class {class_id}"
                    )

                    self.total_detections +=1
                    if class_id==0:
                        self.car_count+=1

                    if class_id==1:
                        self.wall_count+=1
                        wall_found=True

                    writer.writerow([f"image_number:{self.count}",class_id, class_name, confidence])
                
                if wall_found:
                    self.frames_with_wall+=1      
    def save_counts(self):
        filepath= os.path.join(self.save_directory, 'summary.csv')
        with open(filepath, 'a', newline="",encoding='utf-8') as file:
            writer=csv.writer(file)

            writer.writerow([f"counts",
                            f"car_counts: {self.car_count}",
                            f"wall_count: {self.wall_count}",
                            f"total_detections:  {self.total_detections}"])

            total_walls_detected= self.frames_with_wall/self.count #count is the total number of frames
            writer.writerow([f"percentage_of_walls_detected: {total_walls_detected}"])
        self.get_logger().info("Final_Detections_Saved")

def main(args=None):
    """Spin the Follow-the-Gap node until interrupted."""
    rclpy.init(args=args)
    node =YOLONode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.save_counts()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
