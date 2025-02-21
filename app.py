# Copyright (c) 2025, Harleen Lappano
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
import os
import logging
from consts import VOICES_PATH, AUDIO_PATH
from routes import *

if __name__ == '__main__':
    logging.info("Starting Piper Hub Web Server")
    os.makedirs(VOICES_PATH, exist_ok=True)
    os.makedirs(AUDIO_PATH, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)