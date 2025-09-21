import os
import urllib.request

# Base URL for the model files
url_base = "https://storage.openvinotoolkit.org/repositories/open_model_zoo/2022.1/models_bin/3/human-pose-estimation-0001/FP32/"

# List of files to download
files = ["human-pose-estimation-0001.bin", "human-pose-estimation-0001.xml"]

# Destination directory
dest_dir = "Source/Models/human-pose-estimation-0001/FP32/"

# Create the destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Download each file
for file in files:
    url = url_base + file
    dest_path = os.path.join(dest_dir, file)
    print(f"Downloading {file}...")
    urllib.request.urlretrieve(url, dest_path)
    print(f"Downloaded {file} to {dest_path}")

print("All model files downloaded successfully.")