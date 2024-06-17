import torch
import gradio as gr
import os
from pyannote.audio import Pipeline
import tempfile

device = torch.device("cuda" if torch.cuda.is_available() or torch.backends.mps.is_available() else "cpu") # prioritize GPU or Metal Performance Shaders if available
vram = torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0

print(f"Using device: {device} with (V)RAM: {vram:.2f} GB")

audio_formats = ["wav", "mp3", "flac", "ogg"]


try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=os.environ["HUGGINGFACE_READ_TOKEN"]
    )
    pipeline.to(device) # move the model and its components to the device
except Exception as e:
    raise Exception(f"Error loading the model: {e}") # if you get an error, dont bother running the rest of the code

def save_audio(audio):
    if audio is None:
        raise ValueError("No audio file uploaded")
    if audio.split('.')[-1] not in audio_formats:
        raise ValueError(f"Invalid audio format: {audio.name.split('.')[-1]}") # audio.split('.')[-1] gets the extension of the file by simply splitting the directory

    temp_file = tempfile.NamedTemporaryFile(delete=False)

    with open(audio, 'rb') as aud_file:
        with open(temp_file.name, 'wb') as temp: # open the temporary file nicely
            temp.write(aud_file.read())

def diarize_audio(temp_file, num_speakers, min_speakers, max_speakers):
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
        raise ValueError(f"Error diarizing audio: {e}")

    os.remove(temp_file)

    return str(diarization)
    
def timestamp_to_seconds(timestamp):
    try:
        h, m, s = map(float, timestamp.split(':'))
        return 3600 * h + 60 * m + s
    except ValueError as e:
        print(f"Error converting timestamp to seconds: '{timestamp}'. Error: {e}")
        return None

def parse_line(line):
    parts = line.strip()[1:-1].split(' --> ')
    start_time = parts[0].strip()
    end_time = parts[1].split(']')[0].strip()
    label = line.split()[-1].strip()
    return start_time, end_time, label

def write_label(outfile, start_seconds, end_seconds, label):
    outfile.write(f"{start_seconds}\t{end_seconds}\t{label}\n")

def process_line(line, outfile):
    try:
        start_time, end_time, label = parse_line(line)
        start_seconds = timestamp_to_seconds(start_time)
        end_seconds = timestamp_to_seconds(end_time)
        write_label(outfile, start_seconds, end_seconds, label)
        return True
    except Exception as e:
        print(f"Error processing line: '{line.strip()}'. Error: {e}")
        return False

def generate_labels_from_diarization(diarization_output):
    labels_path = 'labels.txt'
    try:
        with open(labels_path, 'w') as outfile:
            lines = diarization_output.strip().split('\n')
            successful_lines = sum(process_line(line, outfile) for line in lines)
        print(f"Processed {successful_lines} lines successfully.")
        return labels_path if successful_lines > 0 else None
    except Exception as e:
        print(f"Cannot write to file '{labels_path}'. Error: {e}")
        return None




def process_audio(audio, num_speakers, min_speakers, max_speakers):
    diarization_result = diarize_audio(save_audio(audio), num_speakers, min_speakers, max_speakers)
    if diarization_result.startswith("Error"):
        return diarization_result, None
    else:
        label_file = generate_labels_from_diarization(diarization_result)
        return diarization_result, label_file

with gr.Blocks() as demo:
    gr.Markdown("""
    # 🗣️Pyannote Speaker Diarization 3.1🗣️
    This model can be used to separate speakers in an audio file. It can be used to detect the number of speakers in the audio file or you can specify the number of speakers in advance.
    
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
    
demo.launch(share=False)
