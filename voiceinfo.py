# Copyright (c) 2025, Harleen Lappano
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

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
