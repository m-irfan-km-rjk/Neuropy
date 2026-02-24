import cv2
import numpy as np
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

class CameraCapture(Image):
    """
    Camera capture widget using OpenCV
    Integrates with Kivy for display and provides frames for emotion detection
    """
    
    def __init__(self, camera_index=0, fps=30, **kwargs):
        """
        Initialize camera capture
        
        Args:
            camera_index: Camera device index (0 for default camera)
            fps: Frames per second for capture
        """
        super().__init__(**kwargs)
        
        self.camera_index = camera_index
        self.fps = fps
        self.capture = None
        self.is_running = False
        self.current_frame = None
        
        # Allow stretch to fill widget
        self.allow_stretch = True
        self.keep_ratio = True
        
    def start(self):
        """Start camera capture"""
        if self.is_running:
            return
        
        try:
            # Open camera
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                print(f"❌ Failed to open camera {self.camera_index}")
                return
            
            # Set camera properties for better performance
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_running = True
            
            # Schedule frame updates
            Clock.schedule_interval(self.update_frame, 1.0 / self.fps)
            
            print(f"✅ Camera started successfully")
            
        except Exception as e:
            print(f"❌ Error starting camera: {e}")
            self.is_running = False
    
    def update_frame(self, dt):
        """
        Update frame from camera
        Called by Kivy Clock at specified FPS
        """
        if not self.is_running or self.capture is None:
            return
        
        try:
            # Read frame
            ret, frame = self.capture.read()
            
            if not ret:
                print("❌ Failed to read frame from camera")
                return
            
            # Store current frame for emotion detection
            self.current_frame = frame.copy()
            
            # Convert BGR to RGB for Kivy display
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Flip horizontally for mirror effect
            rgb_frame = cv2.flip(rgb_frame, 1)
            
            # Convert to Kivy texture
            h, w = rgb_frame.shape[:2]
            texture = Texture.create(size=(w, h), colorfmt='rgb')
            texture.blit_buffer(rgb_frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            
            # Flip texture vertically (Kivy coordinate system)
            texture.flip_vertical()
            
            # Update widget texture
            self.texture = texture
            
        except Exception as e:
            print(f"❌ Error updating frame: {e}")
    
    def get_frame(self):
        """
        Get current frame for processing
        
        Returns:
            frame: Current BGR frame (numpy array) or None
        """
        return self.current_frame
    
    def stop(self):
        """Stop camera capture"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Unschedule frame updates
        Clock.unschedule(self.update_frame)
        
        # Release camera
        if self.capture:
            self.capture.release()
            self.capture = None
        
        print("✅ Camera stopped")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.stop()
