#!/bin/bash

# Detect OS and set paths accordingly
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # Unix-like system
    VENV_ACTIVATE="$(dirname "$0")/venv_ui/bin/activate"
else
    # Windows system
    VENV_ACTIVATE="$(dirname "$0")/venv_ui/Scripts/activate"
fi

REQUIREMENTS_FILE="$(dirname "$0")/Scripts/requirements_ui.txt"
RUN_SCRIPT_FILE="$(dirname "$0")/Scripts/Run_UI.py"

# Check if venv_ui folder exists in the root directory
if [ ! -d "$(dirname "$0")/venv_ui" ]; then
    echo "Creating virtual environment..."
    # Create a virtual environment named "venv_ui" in the root directory
    if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
        python3 -m venv "$(dirname "$0")/venv_ui"
    else
        python -m venv "$(dirname "$0")/venv_ui"
    fi
fi


echo "Activating the virtual environment..."
# Activate the virtual environment
source "$VENV_ACTIVATE"

echo "Installing requirements..."
# Install requirements inside the virtual environment
pip install -r "$REQUIREMENTS_FILE"

# Get the HF Read Token
echo "Get your Hugging Face Read Token at https://huggingface.co/settings/tokens and paste it below,"
echo "be sure that you accept the conditions of https://huggingface.co/pyannote/segmentation-3.0 & https://huggingface.co/pyannote/speaker-diarization-3.1."
read -rp "Enter your HuggingFace Read Token: " HUGGINGFACE_READ_TOKEN

# Export the Hugging Face Read Token as an environment variable
export HUGGINGFACE_READ_TOKEN

echo "Running Python script..."
# Run your Python file here
python "$RUN_SCRIPT_FILE"

echo "Deactivating the virtual environment..."
# Deactivate the virtual environment
deactivate

echo "Script execution complete."
echo "Press Enter to exit..."
read