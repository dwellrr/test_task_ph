import streamlit as st
import ffmpeg
from riffusion.streamlit import util as streamlit_util
from riffusion.spectrogram_params import SpectrogramParams
from pathlib import Path
import shutil
from zipfile import ZipFile
from streamlit import session_state as s_s


TEMP_PATH = "files/temp/"
RESULT_PATH = "files/generated/"
TEMP_NAME = "temp_"

##start stuff(session)

if 'sidebar_state' not in s_s:
    s_s.sidebar_state = 'collapsed'

if 'submitted' not in s_s:
    s_s.submitted = False #so the output doesn't get regenerated on every widget interraction

if 'displaying' not in s_s:
    s_s.displaying = False #so the buttons for download don't hide on every widget interraction

##start stuff(new video)

dirpath = Path(RESULT_PATH)

def resetFolders():
    Path(TEMP_PATH).mkdir(parents=True, exist_ok=True)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(dirpath)
    Path(RESULT_PATH).mkdir(parents=True, exist_ok=True)
    
##ui
def change():
    s_s.sidebar_state = (
        "collapsed" if s_s.sidebar_state == "expanded" else "expanded"
    )

def submit_toggle():
    s_s.submitted = not s_s.submitted


##video splitting

def save_video_pipe(video_segment_io, name):
    process = (
        ffmpeg
        .input('pipe:')
        .output(name)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )
    process.communicate(input=video_segment_io.getbuffer())

def save_video(video_segment, name):
    process = (
        ffmpeg
        .input(video_segment)
        .output(name)
        .overwrite_output()
        .run()
    )

def get_video_chunk(i, start_sec, end_sec):
    process = (
        ffmpeg
        .input(f'{TEMP_PATH}toprocess.mp4', loglevel="quiet", ss = start_sec, t = end_sec)
        .output(f'{RESULT_PATH}{vid.name}_{i}.mp4')
        .overwrite_output()
        .run()
    )

@st.cache_data
def get_video_length(video_path):
    metadata = (ffmpeg
                .probe(video_path)
                )
    duration_str = metadata['streams'][0]['duration']

    duration = float(duration_str)
    return duration

def get_splits(video_path, splits_amount, clip_to_change):
    
    video_length = get_video_length(video_path)
    chunk_length = video_length/splits_amount
    current_chunk_start = 0

    paths = []

    for i in range (1, splits_amount+1):
        get_video_chunk(i, current_chunk_start, chunk_length)
        paths.append(f'{RESULT_PATH}{vid.name}_{i}.mp4')
        current_chunk_start += chunk_length
    return paths

##sound gen
#the reason this function is separate is to cache it with the editable params
@st.cache_data
def segment_from_text(prompt, guidance, negative_prompt, seed, duration_width, device):
    params = SpectrogramParams(
        min_frequency=10,
        max_frequency=20000,
        sample_rate=44100,
        stereo=True,
    )
    image = streamlit_util.run_txt2img( 
        prompt=prompt,
        num_inference_steps=30,
        guidance=guidance,
        negative_prompt= negative_prompt,
        seed=seed,
        width=duration_width,
        height=512,
        checkpoint="riffusion/riffusion-model-v1",
        device=device,
        scheduler="DPMSolverMultistepScheduler",
    )
    #st.image(image)
    segment = streamlit_util.audio_segment_from_spectrogram_image( 
        image=image,
        params=params,
        device="cuda",
    )
    return segment

##sound change (so needs fragment)

def change_sound(video_path, audio_path, name):
    inv = ffmpeg.input(video_path)
    ina = ffmpeg.input(audio_path)
    process = (
        ffmpeg
        .concat(inv, ina, v=1, a=1)
        .output(name)
        .overwrite_output()
        .run()
    )

vid = st.file_uploader("upload video here", type=['mp4'], accept_multiple_files=False, key=None, help=None, on_change=None, args=None, kwargs=None, disabled=False, label_visibility="visible")
if vid is None:
    resetFolders()
    s_s.displaying = False
    s_s.submitted = False
if vid:
    with st.sidebar:
            st.write("Hewwo!")
            guidance = st.number_input("Guidance", step=0.5, min_value=0.5, max_value=999.0, value=7.0)
            seed = st.number_input("Seed", step=1, min_value=-1000, max_value=1000, value=42)
            negative_prompt = st.text_area(placeholder="Anything you don't want goes here!", label="Negative prompt")
            device = streamlit_util.select_device(st.sidebar)
            st.write("tip: better to run cuda (on your GPU)!")

    vid_file = Path(f'{TEMP_PATH}toprocess.mp4')
    if not vid_file.is_file():
        save_video_pipe(vid, f'{TEMP_PATH}toprocess.mp4')


    st.write("Choose options to apply")
    prompt = st.text_area(placeholder="Write your prompt here", label="Prompt")
    coltxt1, coltxt2 = st.columns([1, 1])
    with coltxt1:
        clip_number = st.number_input("Amount of clips to output", step=1, value=2, min_value=2)
    with coltxt2:
        clip_to_change = st.number_input("Which clip would you like to apply the new audio to?", step=1, value=1, min_value=1, max_value=clip_number)
    
    colopt1, colopt2 = st.columns([3, 1])
    
    with colopt2:
        st.write("") #just to align the checkbox
        st.write("")
        auto_col = st.checkbox("Auto (3)", value=True)
    with colopt1:
        column_number = st.number_input("Number of columns to output files into", disabled=auto_col, step=1, min_value=1, max_value=5, value=3)
    

    col1, col2 = st.columns([1, 2])
    with col1:
        moreOptions = st.button("More options for Riffusion", on_click=change)
    with col2:
        st.button("Submit", on_click=submit_toggle)
        
    if s_s.submitted:
        s_s.displaying = False
        st.write(f"#### Seed {seed}")

        paths = get_splits(f"{TEMP_PATH}toprocess.mp4", clip_number, clip_to_change) 
        duration = get_video_length(paths[clip_to_change-1])
        duration_width = int(duration * 100)
        duration_width += 8 - (duration_width % 8)


        audio_segment = segment_from_text(
            prompt=prompt,
            guidance=guidance,
            negative_prompt=negative_prompt,
            seed=seed,
            duration_width=duration_width,
            device=device,
        )
        audio_segment.export('filegen.wav', format="wav")

        change_sound(paths[clip_to_change-1], 'filegen.wav', f"{TEMP_PATH}new.mp4")
        save_video(f"{TEMP_PATH}new.mp4", f'{RESULT_PATH}{vid.name}_{clip_to_change}.mp4')

        streamlit_util.display_and_download_audio(
            audio_segment, name="generated_audio", extension="mp3"
        )
        s_s.displaying = True

    if s_s.displaying:
        
        rendered_columns = 3 if auto_col else column_number
        columns = st.columns(rendered_columns)
        for i in range (1, clip_number+1):
            col = columns[(i-1) % rendered_columns]
            with open(f'{RESULT_PATH}{vid.name}_{i}.mp4', "rb") as file:
                col.download_button(
                    label=f"Download segment {i}",
                    data=file,
                    file_name=f'{vid.name}_{i}.mp4'
                )

        with ZipFile(f"{RESULT_PATH}zipped.zip", 'w') as zip_object:
            for i in range (1, clip_number+1):
                zip_object.write(f'{RESULT_PATH}{vid.name}_{i}.mp4')
        with open(f'{RESULT_PATH}zipped.zip', 'rb') as f:
            st.download_button(
                label=f"Download as archive",
                data=f,
                file_name=f'{vid.name}_zipped.zip' #don't add the folder as the resulting archive is there as well
            )
        s_s.submitted = False