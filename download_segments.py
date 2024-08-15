import os
import requests
base_url = "test"
# Directory to save the downloaded segments
output_dir = "video_segments"
os.makedirs(output_dir, exist_ok=True)


# Function to download a single segment
def download_segment(number):
    url = base_url.replace("{number}", str(number))
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        file_path = os.path.join(output_dir, f"seg-{number}-v1-a1.ts")
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded segment {number}")
        return True
    else:
        print(f"Failed to download segment {number}")
        return False


# Download segments in a loop
segment_number = 1
while True:
    if not download_segment(segment_number):
        break
    segment_number += 1

print("All segments downloaded.")

# Generate file list for FFmpeg
with open("file_list.txt", "w") as f:
    for i in range(1, segment_number):
        f.write(f"file '{output_dir}/seg-{i}-v1-a1.ts'\n")

print("File list generated.")

# You can now use the following FFmpeg command to combine the segments:
# ffmpeg -f concat -safe 0 -i file_list.txt -c copy output.mp4
