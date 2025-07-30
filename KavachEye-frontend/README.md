# KavachEye

A Python-based RTSP camera streaming system that provides efficient management of multiple camera streams.

## Features

- Support for multiple RTSP camera streams
- Thread-safe frame capture
- Frame rate limiting
- Efficient queue-based frame management
- Simple camera management interface

## Requirements

- Python 3.x
- OpenCV (cv2)
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/shreyas162004/KavachEye.git
cd KavachEye
```

2. Install the required packages:
```bash
pip install opencv-python numpy
```

## Usage

```python
from camera_stream import camera_manager

# Add a camera
camera_manager.add_camera("camera1", "rtsp://your-camera-url")

# Get a frame from a specific camera
frame = camera_manager.get_frame("camera1")

# Remove a camera
camera_manager.remove_camera("camera1")

# Stop all cameras
camera_manager.stop_all()
```

## License

MIT License 