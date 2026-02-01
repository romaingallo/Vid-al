import subprocess
import os

def has_audio(input_path):
    """Check if the video file has an audio stream using ffprobe"""
    cmd = [
        'ffprobe', '-i', input_path,
        '-show_streams', '-select_streams', 'a',
        '-loglevel', 'error'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return 'codec_type=audio' in result.stdout
    except subprocess.CalledProcessError:
        return False

def convert_to_hls(input_path, output_dir):
    """Convert video to HLS format using FFmpeg"""
    os.makedirs(output_dir, exist_ok=True)

    hls_playlist = os.path.join(output_dir, 'playlist.m3u8')

    # HLS conversion command
    hls_cmd = [
        'ffmpeg', '-i', input_path,
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-start_number', '0',
        '-hls_time', '10',
        '-hls_list_size', '0',
        '-f', 'hls',
        hls_playlist
    ]

    try:
        subprocess.run(hls_cmd, check=True)
        print(f"HLS conversion completed for {input_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"HLS conversion failed: {e}")
        return False

def convert_to_dash(input_path, output_dir):
    """Convert video to DASH format using FFmpeg"""
    os.makedirs(output_dir, exist_ok=True)

    dash_playlist = os.path.join(output_dir, 'manifest.mpd')

    # Check if video has audio
    has_audio_stream = has_audio(input_path)

    # Base command
    dash_cmd = ['ffmpeg', '-i', input_path]

    # Mapping
    dash_cmd.extend(['-map', '0:v'])
    if has_audio_stream:
        dash_cmd.extend(['-map', '0:a'])

    # Video options
    dash_cmd.extend([
        '-c:v', 'libx264', '-x264-params', 'keyint=60:min-keyint=60:no-scenecut=1',
        '-b:v:0', '1500k',
        '-bf', '1', '-keyint_min', '60',
        '-g', '60', '-sc_threshold', '0'
    ])

    # Audio options if present
    if has_audio_stream:
        dash_cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

    # DASH options
    dash_cmd.extend([
        '-f', 'dash',
        '-use_template', '1', '-use_timeline', '1',
        '-init_seg_name', 'init-$RepresentationID$.m4s',
        '-media_seg_name', 'chunk-$RepresentationID$-$Number%05d$.m4s'
    ])

    # Adaptation sets
    if has_audio_stream:
        dash_cmd.extend(['-adaptation_sets', 'id=0,streams=v id=1,streams=a'])
    else:
        dash_cmd.extend(['-adaptation_sets', 'id=0,streams=v'])

    dash_cmd.append(dash_playlist)

    try:
        subprocess.run(dash_cmd, check=True, cwd=output_dir)
        print(f"DASH conversion completed for {input_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"DASH conversion failed: {e}")
        return False
    
def process_video(file_path, video_id, videos_folder):

    video_dir = os.path.join(videos_folder, video_id)
    os.makedirs(video_dir, exist_ok=True)

    # Convert to HLS
    hls_result = convert_to_hls(file_path, video_dir)

    # Convert to DASH
    dash_result = convert_to_dash(file_path, video_dir)

    return hls_result and dash_result