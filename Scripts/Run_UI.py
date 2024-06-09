import torch
import gradio as gr
import os
from pyannote.audio import Pipeline

# find the device
if torch.cuda.is_available() and torch.backends.cuda.is_built():
    # A CUDA compatible GPU was found.
    print("CUDA device found, enabling.")
    device = "cuda"
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    # Apple M1/M2 machines have the MPS framework.
    print("Apple MPS device found, enabling.")
    device = "mps"
else:
    # Else we're defaulting to CPU.
    device = "cpu"
    print("No CUDA or MPS devices found, running on CPU.")

# instantiate the pipeline
try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=os.environ["HUGGINGFACE_READ_TOKEN"]
    )
    # Move the pipeline to the GPU
    pipeline.to(device)
except Exception as e:
    print(f"Error initializing pipeline: {e}")
    pipeline = None


def save_audio(audio):
    if pipeline is None:
        return "Error: Pipeline not initialized"

    # Read the uploaded audio file as bytes
    with open(audio, "rb") as f:
        audio_data = f.read()

    # Save the uploaded audio file to a temporary location
    with open("temp.wav", "wb") as f:
        f.write(audio_data)

    return "temp.wav"

def diarize_audio(temp_file, num_speakers, min_speakers, max_speakers):
    if pipeline is None:
        return "Error: Pipeline not initialized"

    try:
        params = {}
        if num_speakers > 0:
            params["num_speakers"] = num_speakers
        if min_speakers > 0:
            params["min_speakers"] = min_speakers
        if max_speakers > 0:
            params["max_speakers"] = max_speakers

        diarization = pipeline(temp_file, **params)
    except Exception as e:
        return f"Error processing audio: {e}"

    # Remove the temporary file
    os.remove(temp_file)

    # Return the diarization output
    return str(diarization)
    
def timestamp_to_seconds(timestamp):
    try:
        # Extracts hour, minute, and second from timestamp and converts to total seconds
        h, m, s = map(float, timestamp.split(':'))
        return 3600 * h + 60 * m + s
    except ValueError as e:
        print(f"Error converting timestamp to seconds: '{timestamp}'. Error: {e}")
        return None

def generate_labels_from_diarization(diarization_output):
    successful_lines = 0  # Counter for successfully processed lines
    labels_path = 'labels.txt'
    try:
        with open(labels_path, 'w') as outfile:
            lines = diarization_output.strip().split('\n')
            for line in lines:
                try:
                    parts = line.strip()[1:-1].split(' --> ')
                    start_time = parts[0].strip()
                    end_time = parts[1].split(']')[0].strip()
                    label = line.split()[-1].strip()  # Extracting the last word as label
                    start_seconds = timestamp_to_seconds(start_time)
                    end_seconds = timestamp_to_seconds(end_time)
                    outfile.write(f"{start_seconds}\t{end_seconds}\t{label}\n")
                    successful_lines += 1
                except Exception as e:
                    print(f"Error processing line: '{line.strip()}'. Error: {e}")
        print(f"Processed {successful_lines} lines successfully.")
        return labels_path if successful_lines > 0 else None
    except Exception as e:
        print(f"Cannot write to file '{labels_path}'. Error: {e}")
        return None



def process_audio(audio, num_speakers, min_speakers, max_speakers):
    diarization_result = diarize_audio(save_audio(audio), num_speakers, min_speakers, max_speakers)
    if diarization_result.startswith("Error"):
        return diarization_result, None  # Return None for label file link if there's an error
    else:
        label_file = generate_labels_from_diarization(diarization_result)
        return diarization_result, label_file

with gr.Blocks() as demo:
    gr.Markdown("""
    # 🗣️Pyannote Speaker Diarization 3.1🗣️
    This model takes an audio file as input and outputs the diarization of the speakers in the audio.
    Please upload an audio file and adjust the parameters as needed.
    
    The maximum length of the audio file that can be processed depends based on the hardware it's running on. If you are on the ZeroGPU HuggingFace Space, it's around **35-40 minutes**.
    If you find this space helpful, please ❤ it.
    Join my server for support and open source AI discussion: https://discord.gg/osai
    IF YOU LEAVE ALL THE PARAMETERS BELOW TO 0, IT WILL BE ON AUTO MODE, AUTOMATICALLY DETECTING THE SPEAKERS, ELSE USE THE ONES BELOW FOR MORE COSTUMIZATION & BETTER RESULTS
    """)
    audio_input = gr.Audio(type="filepath", label="Upload Audio File")
    num_speakers_input = gr.Number(label="Number of Speakers", info="Use it only if you know the number of speakers in advance, else leave it to 0 and use the parameters below", value=0)
    
    gr.Markdown("Use the following parameters only if you don't know the number of speakers, you can set lower and/or upper bounds on the number of speakers, if instead you know it, leave the following parameters to 0 and use the one above")
    
    min_speakers_input = gr.Number(label="Minimum Number of Speakers", value=0)
    max_speakers_input = gr.Number(label="Maximum Number of Speakers", value=0)
    process_button = gr.Button("Process")
    diarization_output = gr.Textbox(label="Diarization Output")
    label_file_link = gr.File(label="Download DAW Labels")

    process_button.click(
        fn=process_audio,
        inputs=[audio_input, num_speakers_input, min_speakers_input, max_speakers_input],
        outputs=[diarization_output, label_file_link]
)
demo.launch(share = False)