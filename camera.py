import cv2

class Camera:
    def __init__(self, src=0):
        self.src = src
        self.cap = None
        self.is_opened = False
        self._initialize()
    
    def _initialize(self):
        """Initialize or reinitialize the camera."""
        if self.cap is not None:
            self.cap.release()
        
        self.cap = cv2.VideoCapture(self.src)
        
        if not self.cap.isOpened():
            print(f"Error: Could not open camera {self.src}.")
            print("Trying alternative camera indices...")
            
            # Try a few alternative indices
            for alt_src in [0, 1, 2]:
                if alt_src != self.src:
                    self.cap = cv2.VideoCapture(alt_src)
                    if self.cap.isOpened():
                        print(f"Successfully opened camera {alt_src}")
                        self.src = alt_src
                        self.is_opened = True
                        break
        else:
            self.is_opened = True
        
        if self.is_opened:
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
            
    def get_frame(self):
        """Capture and return a frame from the camera."""
        if not self.is_opened:
            return None
            
        ret, frame = self.cap.read()
        if ret:
            return frame
        return None
    
    def change_source(self, src):
        """Change camera source."""
        self.src = src
        self._initialize()
        return self.is_opened

    def release(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.is_opened = False
    
    @staticmethod
    def list_cameras(max_cameras=5):
        """List available camera indices."""
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available
