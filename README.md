# Test Task - Streamlit App with Riffusion

This project is a Streamlit application that integrates Riffusion. The application supports both GPU (CUDA) and CPU configurations and provides configurable options for Riffusion.

## Features (for brownie points)

- Runs on Docker (image available on Docker Hub) https://hub.docker.com/repository/docker/wdwell/test-task-riff/general
- GPU (CUDA) or CPU available
- Configurable options for Riffusion
- Can audjust the amount of columns for your outputs (up to 5, 3 by default)

## Note Extra Details

- The clips are divided into equal lengths.
- `ffmpeg` (and Python `ffmpeg` bindings) are used for video manipulation.
- **Important:** The deprecated warning messages come from Riffusion itself as it is not well-maintained and uses deprecated cache decorators.
- Riffusion needs to be incluses localy and linked locally since the newest version is not available on pip.

## To install

1. Clone Riffusion
2. Move the subdirectory "Riffusion" into the root of the project
3. Install requirements from requirements.txt
4. I use cuda 1.16 (that's what my pc supports), make sure your version is compatible (or update this one)
5. streamlit run test_task.py

Completed exclusively by me (Sofiia)
(but i didn't make riffusion obviously)
