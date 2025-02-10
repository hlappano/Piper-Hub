from flask import Flask, request, render_template, send_file, redirect, url_for, flash, jsonify, after_this_request
import requests
import json
import io
import os
import logging
import threading
import shutil
import base64
import random
import subprocess
import re
import string
import base64
from functools import wraps
import time
from io import BytesIO
import hashlib
from pathlib import Path


# *********************************************************
#
# Global Variables
#
# *********************************************************
APP_PATH= '/app'
DATA_PATH=os.path.join(APP_PATH, "data")
VOICES_PATH=os.path.join(DATA_PATH, "voices")
PIPER_BIN=os.path.join(APP_PATH, "piper", "piper")
AUDIO_PATH=os.path.join(DATA_PATH, "audio")
PIPER_VOICES_URL="https://huggingface.co/rhasspy/piper-voices/raw/v1.0.0"
VOICES_JSON_URL=os.path.join(PIPER_VOICES_URL, "voices.json")
VOICES_JSON_FILE_PATH=os.path.join(DATA_PATH, "voices.json")
DOWNLOAD_VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"#en/en_US/amy/low/en_US-amy-low.onnx?download=true"

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mutex for thread lock
install_lock = threading.Lock()

# Generate Catalog
voice_catalog = {}

# *********************************************************
#
# Class Structure for Voice Info
#
# *********************************************************
class VoiceInfo:
    def __init__(self, key, name, lang, lang_code, lang_name_english, lang_country_english, region, quality, num_speakers, speaker_id_map = None):
        self.key = key
        self.name = name
        self.lang = lang
        self.lang_code = lang_code
        self.lang_name_english = lang_name_english
        self.lang_country_english = lang_country_english
        self.region = region
        self.quality = quality
        self.num_speakers = num_speakers
        self.speaker_id_map = speaker_id_map

# *********************************************************
#
# Get Voice Info from Catalog
#
# *********************************************************
def get_voice_name(voice_key, catalog):
    return catalog[voice_key]["name"]

def get_voice_lang(voice_key, catalog):
    return catalog[voice_key]["language"]["family"]

def get_voice_lang_code(voice_key, catalog):
    return catalog[voice_key]["language"]["code"]

def get_voice_lang_name_english(voice_key, catalog):
    return catalog[voice_key]["language"]["name_english"]

def get_voice_lang_country_english(voice_key, catalog):
    return catalog[voice_key]["language"]["country_english"]

def get_voice_region(voice_key, catalog):
    return catalog[voice_key]["language"]["region"]

def get_voice_quality(voice_key, catalog):
    return catalog[voice_key]["quality"]

def get_voice_num_speakers(voice_key, catalog):
    return catalog[voice_key]["num_speakers"]

def get_voice_speaker_id_map(voice_key, catalog):
    return catalog[voice_key]["speaker_id_map"]

def get_voice_files(voice_key, catalog):
    return catalog[voice_key]["files"]

# *********************************************************
#
# Server Functions
#
# *********************************************************
def multiple_replace(text, replacements):
    # Iterar sobre cada par de remplazo
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def filter_text(text):
    # Lista de remplazos a realizar
    replacements = [('(', ','), (')', ','), ('?', ','), ('¿', ','), (':', ','), ('\n', ' ')]
    
    # Realizar remplazos
    filtered_text = multiple_replace(text, replacements)
    
    # Escapar todos los caracteres especiales dentro de las comillas
    filtered_text = re.sub(r'(["\'])', lambda m: "\\" + m.group(0), filtered_text)
    
    return filtered_text

# Piper TTS
def piper(text, model, speaker_id, speaker_rate, audio_volatility, phoneme_volatility):
    # Get a unique file name for temporary file storage
    random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8)) + '.wav'
    output_file = os.path.join(AUDIO_PATH, random_name)

    # Check if Piper bin exists
    if os.path.isfile(PIPER_BIN):
        # Get Model Path
        if model in voice_catalog:
            # Get model path
            model_files = get_voice_files(model, voice_catalog)
            model_path = None
            for file in model_files:
                if file.endswith(".onnx"):
                    model_path = os.path.join(VOICES_PATH, file)
                    break
            if model_path is not None:
                # With Speaker ID
                if speaker_id != -1:
                    command = f'echo "{text}" | "{PIPER_BIN}" -m {model_path} -s {speaker_id} --length_scale {speaker_rate} --noise_scale {audio_volatility} --noise_w {phoneme_volatility} -f {output_file}'
                # Without Speaker ID
                else:
                    command = f'echo "{text}" | "{PIPER_BIN}" -m {model_path} --length_scale {speaker_rate} --noise_scale {audio_volatility} --noise_w {phoneme_volatility} -f {output_file}'

                # Try to run the piper command
                try:
                    subprocess.run(command, shell=True, check=True)
                    return output_file
                except subprocess.CalledProcessError as e:
                    logging.error(f"Error on piper command: {e}")
        else:
            logger.error(f"Error Model '{model} is not in catalog")
    else:
        logger.error(f"Error Can't find Piper")

    return None


# Returns the voices catalog
def get_voices_catalog():
    has_voices_json = False
    # Check if voices.json exists on local
    if os.path.exists(VOICES_JSON_FILE_PATH):
        has_voices_json = True

    # Get Latest Voices from huggingface repo
    # Download the JSON File
    response = requests.get(VOICES_JSON_URL)
    # Pull latest voices json
    voices_json = None
    if response.status_code == 200:
        print(f"Pulled latest voice catalog from huggingface repo")
        # Parse JSON content
        voices_json = response.json()

    # Migrate Voices
    if voices_json is not None:
        if has_voices_json == True:
            logging.info("Migrating Voices.json")
            # Load on file voices
            with open(VOICES_JSON_FILE_PATH, "r") as file:
                voices_on_file_json = json.load(file)

            for voice_key in voices_json:
                # Voice Key not in on file
                if voice_key not in voices_on_file_json:
                    voices_on_file_json[voice_key] = voices_json[voice_key]
            
            # Save new voices json
            with open(VOICES_JSON_FILE_PATH, "w") as file:
                json.dump(voices_on_file_json, file, indent = 4)
            return voices_on_file_json
        else:
            # Save the json file
            with open(VOICES_JSON_FILE_PATH, "w") as file:
                json.dump(voices_json, file, indent = 4)
            # Return the voice info data
            return voices_json
    elif has_voices_json == True:
        print(f"Warning: Huggingface voice catalog not accessible. Reading from local voices.json")
        # Open existing file
        with open(VOICES_JSON_FILE_PATH, "r") as file:
            data = json.load(file)
    else:
        print(f"Error: Unable to retrieve voices")
        return None

# Get Installed Voices
def get_installed_voices():
    voice_infos = {}

    # Traverse the languages (e.g en)
    for lang in os.listdir(VOICES_PATH):
        # lang path 
        lang_path = os.path.join(VOICES_PATH, lang)
        # Traverse the code (e.g. en_US)
        for code in os.listdir(lang_path):
            # country path
            code_path = os.path.join(lang_path, code)
            # Traverse voice name
            for voice_name in os.listdir(code_path):
                # voice name path
                voice_name_path = os.path.join(code_path, voice_name)
                # Traverse on quality
                for quality in os.listdir(voice_name_path):
                    # quality path
                    quality_path = os.path.join(voice_name_path, quality)
                    # Look at files
                    for file in os.listdir(quality_path):
                        if file.endswith(".onnx"):
                            key = os.path.splitext(file)[0]
                            if voice_catalog is not None and key not in voice_catalog:
                                print(f"Error: Key is not in catalog. TODO: Handle manual uploads")
                            else:                               
                                # Add VoiceInfo
                                voice_infos[key] = VoiceInfo(
                                        key,
                                        get_voice_name(key, voice_catalog),
                                        get_voice_lang(key, voice_catalog),
                                        get_voice_lang_code(key, voice_catalog),
                                        get_voice_lang_name_english(key, voice_catalog),
                                        get_voice_lang_country_english(key, voice_catalog),
                                        get_voice_region(key, voice_catalog),
                                        get_voice_quality(key, voice_catalog),
                                        get_voice_num_speakers(key, voice_catalog),
                                        get_voice_speaker_id_map(key, voice_catalog)
                                    )
    return voice_infos

# Get Available Voices
def get_available_voices(installed_voices):
    voice_infos = {}
    # Loop through each voice in catalog
    for key in voice_catalog:
        if key not in installed_voices:
            # Add VoiceInfo
            voice_infos[key] = VoiceInfo(
                    key,
                    get_voice_name(key, voice_catalog),
                    get_voice_lang(key, voice_catalog),
                    get_voice_lang_code(key, voice_catalog),
                    get_voice_lang_name_english(key, voice_catalog),
                    get_voice_lang_country_english(key, voice_catalog),
                    get_voice_region(key, voice_catalog),
                    get_voice_quality(key, voice_catalog),
                    get_voice_num_speakers(key, voice_catalog)
                )
    return voice_infos

# Download File
def download_file(url, save_path):
    # Send the HTTP request to download the file
    try:
        logging.info(f"Downloading from: {url}")
        response = requests.get(url, stream=True)

        # On success
        if response.status_code == 200:
            # Create the directories if they don't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # Saving file data
            with open(save_path, "wb") as file:
                # Write the content to the file
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                logging.info(f"Download complete: {save_path}")
        else:
            logging.error(f"Error failed to download file, Status code {response.status_code}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

# Delete path (file or folder)
def delete_files(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        logging.info(f"Deleted {path} successfully")
    else:
        logging.error(f"{path} not found.")

# Clean up the Directory System
def clean_up_empty_directory(base_directory, current_directory):
    if not os.listdir(current_directory):
        logging.info(f"Directory {current_directory} is empty, removing it.")
        os.rmdir(current_directory)
        # if parent check
        parent_directory = os.path.dirname(current_directory)
        if parent_directory != base_directory:
            clean_up_empty_directory(base_directory, parent_directory)

def get_file_hash(path, bytes_per_chunk: int = 8192) -> str:
    """Hash a file in chunks using md5."""
    path_hash = hashlib.md5()
    with open(path, "rb") as path_file:
        chunk = path_file.read(bytes_per_chunk)
        while chunk:
            path_hash.update(chunk)
            chunk = path_file.read(bytes_per_chunk)

    return path_hash.hexdigest()

# *********************************************************
#
# Web Interface
#
# *********************************************************
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/imgs', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Main landing page
@app.route("/")
def index():   
    # Get installed Voices
    installed_voices = get_installed_voices()

    # Get Available Voices to download
    if voice_catalog is not None:
                available_voices = get_available_voices(installed_voices)
    else:
        available_voices = None
    return render_template("index.html", installed_voices=installed_voices, available_voices=available_voices)

# Install Voice - Post Message
@app.route("/install_voice", methods=["POST"])
def install_voice():
    logging.info(f"Post Action for install voice")

    # Try installing voice
    try:
        voice_key = request.json.get("voice_to_install")
        if voice_key:
            #server_install_voice(voice_key)
            logging.info(f"Server installing {voice_key}")
            if install_lock.locked():
                return jsonify({"message": "Voice installation already in progress, please wait."}), 400 

            # Lock the install
            with install_lock:
                for file in voice_catalog[voice_key]["files"]:
                    url = f"{DOWNLOAD_VOICE_URL}/{file}"
                    url_query = f"{url}?download=true"
                    save_file = os.path.join(VOICES_PATH, file)
                    download_file(url_query, save_file)

            # After installation, reload voice list
            installed_voices = get_installed_voices()
            available_voices = get_available_voices(installed_voices)

            # return updated voices as JSON
            return jsonify({
                "installed_voices": [voice.__dict__ for voice in installed_voices.values()],
                "available_voices": [voice.__dict__ for voice in available_voices.values()],
                "message": f"{voice_key} voice installed successfully!"
            }), 201
        else:
            return jsonify({"message": f"Error voice_key: {voice_key} not valid!"}), 404
    except Exception as e:
        return jsonify({"message": f"Error during voice install: {e}"}), 500

# Upload a Voice - Post <essage
@app.route("/upload_voice", methods=["POST"])
def upload_voice():
    logging.info(f"Post Action for uploading voice")

    # Try uploading voice
    try:
        if request.is_json:
            logging.info("Parsing JSON")
            raise RuntimeError("JSON not supported only Forms for /upload_voice.")

        # Check if onnx and json file are valid
        if 'onnx_file' not in request.files or 'json_file' not in request.files:
            raise RuntimeError("Missing required files")

        # Get the files for the voice model
        onnx_file = request.files['onnx_file']
        json_file = request.files['json_file']
        # Override name
        if "override_voice_name" in request.form:
            override_voice_name = request.form['override_voice_name']
        else:
            override_voice_name = None
        
        # Read json file
        json_data = json.load(json_file)

        # Check valid
        lang_key = 'language'
        fam_key = 'family'
        code_key = 'code'
        name_key = 'dataset'
        audio_key = 'audio'
        quality_key = 'quality'

        # Check validation of Json file
        #TODO: Maybe enforce PIPER VERSION CHECK
        if lang_key in json_data and \
            fam_key in json_data[lang_key] and \
            code_key in json_data[lang_key] and \
            name_key in json_data and \
            audio_key in json_data and \
            quality_key in json_data[audio_key]:

            logging.info("Json is valid")
        else:
            return jsonify({"message": f"JSON File in voice is invalid."}), 400
        
        # Add Family to Path
        lang_fam = json_data[lang_key][fam_key]
        # Code
        lang_code = json_data[lang_key][code_key]
        # dataset name
        dataset_name = json_data[name_key]
        # Quality
        quality = json_data[audio_key][quality_key]
        # Get and verify voice key
        if override_voice_name is not None:
            dataset_name = override_voice_name
        # Set voice Key
        voice_key = lang_code + "-" + dataset_name + "-" + quality

        # Create save directory
        save_directory = os.path.join(VOICES_PATH, lang_fam, lang_code, dataset_name, quality)

        # Setup filename paths
        onnx_filename = voice_key + ".onnx"
        json_filename = onnx_filename + ".json"
        onnx_path = os.path.join(save_directory, onnx_filename)
        json_path = os.path.join(save_directory, json_filename)
        model_card_path = None

        # voice_key must not be in voice_catalog before uploading.
        if voice_key not in voice_catalog:
            # Lock install, uploading files
            with install_lock:
                logging.info(f"Saving files to {os.path.dirname(onnx_path)}")
                # Make directories
                os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
                # Write the onnx file
                onnx_file.save(onnx_path)
                # Write JSON data as a proper text file
                with open(json_path, "w") as f:
                    json.dump(json_data, f, indent=2)  # Format with indentation
                # For model card, get and write file
                if 'model_card' in request.files:
                    model_card_file = request.files.get('model_card')
                    model_filename = "MODEL_CARD"
                    model_card_path = os.path.join(save_directory, model_filename)
                    model_card_file.save(model_card_path)

            logging.info("Updating voice catalog")
            voices_path = Path(VOICES_PATH)
            # Create file_paths
            file_paths = [Path(onnx_path), Path(json_path)]
            # Include model_card_path only if it's set
            if model_card_path is not None:
                file_paths.append(Path(model_card_path))

            # Add voice to catalog
            voice_catalog[voice_key] = {
                "key": voice_key,
                "name": dataset_name,
                "language": {
                    "code": lang_code,
                    "family": lang_fam,
                    "region": json_data[lang_key]['region'],
                    "name_native": json_data[lang_key]['name_native'],
                    "name_english": json_data[lang_key]['name_english'],
                    "country_english": json_data[lang_key]['country_english'],
                },
                "quality": quality,
                "num_speakers": json_data["num_speakers"],
                "speaker_id_map": json_data.get("speaker_id_map", {}),
                "files": {
                    str(file_path.relative_to(voices_path)): {
                        "size_bytes": file_path.stat().st_size,
                        "md5_digest": get_file_hash(file_path),
                    }
                    for file_path in file_paths
                },
                "aliases": [],
                # Marks that it was added on by this web
                "piper-tts-web-addon": True
            }

            logging.info("Created Voice in Catalog")

            # Save new voices json
            with open(VOICES_JSON_FILE_PATH, "w") as file:
                json.dump(voice_catalog, file, indent = 4)
        else:
            return jsonify({
                "message": f"Error: Voice key '{voice_key}', already exists in catalog for downloading, no need to upload. \
                \nVerify that the Dataset: '{dataset_name}' in the .onnx.json is correct it could be a duplicate. If not, use name override."
                }), 400

        # After installation, reload voice list
        installed_voices = get_installed_voices()
        available_voices = get_available_voices(installed_voices)
        
        # return updated voices as JSON
        return jsonify({
            "installed_voices": [voice.__dict__ for voice in installed_voices.values()],
            "available_voices": [voice.__dict__ for voice in available_voices.values()],
            "message": f"{dataset_name} voice uploaded successfully!"
        }), 200

    except Exception as e:
        logging.error(f"Exception: {e} in voice upload")
        return jsonify({
            "message": f"Error during voice upload: {e}"
            }), 500

# Uninstalling voice
@app.route("/uninstall_voice", methods=["POST"])
def uninstall_voice():
    logging.info(f"Post Action for uninstall voice")

    try:
        voice_key = request.json.get("voice_to_uninstall")
        if voice_key:
            #server_install_voice(voice_key)
            logging.info(f"Server uninstalling {voice_key}")
            if install_lock.locked():
                return jsonify({"message": "Voice uninstallation already in progress, please wait."}), 400 

            with install_lock:
                for file_path in voice_catalog[voice_key]["files"]:
                    file = os.path.join(VOICES_PATH, file_path)             
                    directory = os.path.dirname(file)
                    delete_files(directory)
                    parent_directory = os.path.dirname(directory)
                    clean_up_empty_directory(VOICES_PATH, parent_directory)
                    break

            # remove from catalog if piper-tts-web-addon
            if voice_key in voice_catalog:
                if 'piper-tts-web-addon' in voice_catalog[voice_key]:
                    del voice_catalog[voice_key]
                     # Save new voices json
                    with open(VOICES_JSON_FILE_PATH, "w") as file:
                        json.dump(voice_catalog, file, indent = 4)

            # After installation, reload voice list
            installed_voices = get_installed_voices()
            available_voices = get_available_voices(installed_voices)

            # return updated voices as JSON
            return jsonify({
                "installed_voices": [voice.__dict__ for voice in installed_voices.values()],
                "available_voices": [voice.__dict__ for voice in available_voices.values()],
                "message": f"{voice_key} voice uninstalled successfully!"
            })
        else:
            return jsonify({"message": f"Error voice_key: {voice_key} not valid!"}), 404
    except Exception as e:
        return jsonify({"message": f"Error during voice uninstall: {str(e)}"}), 500

# Get Voice Data - Get Message
@app.route('/get_voice_data')
def get_voice_data():
    # After installation, reload voice list
    installed_voices = get_installed_voices()
    available_voices = get_available_voices(installed_voices)

    return jsonify({
        "installed_voices": [voice.__dict__ for voice in installed_voices.values()],
        "available_voices": [voice.__dict__ for voice in available_voices.values()],
    })

# Piper TTS - Post Message
@app.route('/piper_tts', methods=["POST"])
def piper_tts():
    logging.info(f"Post Action for tts")
    try:
        if request.is_json:
            logging.info("Parsing JSON data")
            text = request.json.get("text")
            model = request.json.get("model")
            speaker_id = request.json.get("speaker_id", -1) # Default to -1 if not provided
            speaker_rate = request.json.get("speaker_rate")
            audio_volatility = request.json.get("audio_volatility")
            phoneme_volatility = request.json.get("phoneme_volatility")
        else:
            logging.info("Parsing Form data")
            text = request.form['text']
            model = request.form['voice']
            speaker_id = request.form.get('speaker', -1) # Default to -1 if not provided
            speaker_rate = request.form['speaker_rate']
            audio_volatility = request.form['audio_volatility']
            phoneme_volatility = request.form['phoneme_volatility']
    except KeyError as e:
        logging.error(f"Missing required form key: {e}")
        return jsonify({"error": f"Missing required key: {e}"}), 400
    except Exception as e:
        logging.error(f"Error parsing request: {e}")
        return jsonify({"error": "Invalid request format"}), 400

    # Call piper
    output_file = piper(text, model, speaker_id, speaker_rate, audio_volatility, phoneme_volatility)
    logging.info(f"Piper Completed with {output_file}")

    @after_this_request
    def remove_file(response):
        try:
            os.remove(output_file)
            logging.info("Audio file deleted: %s", output_file)
        except Exception as error:
            logging.error("Error deleting file: %s", error)
        return response

    if output_file is not None:
        with open(output_file, 'rb') as audio_file:
            audio_content = audio_file.read()
        # encode audio
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        # create a response with it.
        response = jsonify({'audio_base64': audio_base64})
    else:
        logging.error("Piper output_file is None.")
        response = jsonify({"message": "Error occurred in Piper execution!"}), 500

    return response

if __name__ == '__main__':
    logging.info("Starting Piper Hub Web Server")
    os.makedirs(VOICES_PATH, exist_ok=True)
    os.makedirs(AUDIO_PATH, exist_ok=True)
    voice_catalog = get_voices_catalog()
    app.run(host='0.0.0.0', port=5000, debug=False)