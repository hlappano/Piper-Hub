# Copyright (c) 2025, Harleen Lappano
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os
import logging
import threading

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
DOWNLOAD_VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

# Mutex for thread lock
install_lock = threading.Lock()
# Make Logging Conig
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
