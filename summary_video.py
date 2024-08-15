import whisper
import openai
import os
import torch

# Define the input and output file paths
number = "04"
input_video = f"{number}.mp4"
audio_output = f"audio_output_{number}.mp3"
transcription_file = f"transcription_{number}.txt"
summary_file = f"summary_{number}.txt"

# Step 1: Extract audio from video using ffmpeg
if not os.path.exists(audio_output):
    os.system(f"ffmpeg -i {input_video} -q:a 0 -map a {audio_output}")

# Step 2: Check if GPU is available and load the Whisper model accordingly
if not os.path.exists("transcription_file"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=device)
    result = model.transcribe(audio_output, language="zh")

    # Save the transcription to a text file
    with open(transcription_file, "w", encoding="utf-8") as file:
        file.write(result["text"])

# Step 3: Summarize the transcription using GPT-4
transcription = result["text"]
openai.api_key = "your-api-key"

response = openai.Completion.create(
    engine="davinci",
    prompt=f"用正體中文總結以下文本，用台灣常見用語:\n\n{transcription}",
    max_tokens=150,
)

summary = response.choices[0].text.strip()

# Save the summary to a text file
with open(summary_file, "w") as file:
    file.write(summary)

print("Summary generated and saved to summary.txt")
