# Copyright (c) 2025, Harleen Lappano
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
from consts import *
import string
import random
import os
import subprocess
import requests
import json
from voiceinfo import VoiceInfo
import shutil
import logging
import hashlib


# *********************************************************
#
# Get Voice Info from Catalog
#
# *********************************************************
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
        logging.info(f"Pulled latest voice catalog from huggingface repo")
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
            logging.info("Saving Voices.json")
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

# Global Variable
voice_catalog = get_voices_catalog()

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
                                logging.error(f"Key is not in catalog. TODO: Handle manual uploads")
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