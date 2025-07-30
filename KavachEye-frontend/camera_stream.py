#only used if we need to use cctv provide rtsp_url of your cam for more info contact us
import cv2
import threading
import time
from queue import Queue
import numpy as np

class RTSPCamera:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = None
        self.frame_queue = Queue(maxsize=2)
        self.is_running = False
        self.thread = None

    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.cap = cv2.VideoCapture(self.rtsp_url)
        
        if not self.cap.isOpened():
            raise Exception("Failed to connect to camera")
        
        self.thread = threading.Thread(target=self._capture_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.thread:
            self.thread.join()

    def _capture_loop(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to read frame")
                time.sleep(1)
                continue

            # Clear queue if full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except:
                    pass

            self.frame_queue.put(frame)
            time.sleep(0.03)  # Limit to ~30 FPS

    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except:
            return None

class CameraManager:
    def __init__(self):
        self.cameras = {}

    def add_camera(self, camera_id, rtsp_url):
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
        
        camera = RTSPCamera(rtsp_url)
        camera.start()
        self.cameras[camera_id] = camera

    def remove_camera(self, camera_id):
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]

    def get_frame(self, camera_id):
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_frame()
        return None

    def stop_all(self):
        for camera in self.cameras.values():
            camera.stop()
        self.cameras.clear()

# Global camera manager instance
camera_manager = CameraManager() 