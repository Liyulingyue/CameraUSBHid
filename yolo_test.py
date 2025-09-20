from ultralytics import YOLO

# Load a model
model = YOLO("./Source/Models/yolo11x-pose.pt", device="CPU")  # load an official model
# Predict with the model
results = model("https://ultralytics.com/images/bus.jpg")  # predict on an image

# Access the results
for result in results:
    xy = result.keypoints.xy  # x and y coordinates
    xyn = result.keypoints.xyn  # normalized
    kpts = result.keypoints.data  # x, y, visibility (if available)