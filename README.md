<img src="./static/imgs/piper_web_logo.png" alt="Alt Text" width="256" height="256">

# Piper Hub
This is a web interface portal to the [Piper TTS](https://github.com/rhasspy/piper). It allows to do the following with a web browser:
* Download and Install Voices from [Huggingface: rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
* Uninstall Voices
* Upload Custom Voices
* Generate Text-To-Speech with the selected voice.
* Download the audio generated via the web browser.

## Docker Deploying Application
1. Open command prompt inside the Piper-Hub root.
2. Build Image:
`` docker build -t piper-hub-image .``
3. Compose Image:
``docker run -d --name piper-hub -p 5000:5000 piper-hub-image``
    * Port can be adjusted to ``{your_preferred_port}:5000``
4. Open web browser to http://localhost:5000 (non-secure)

## License
MIT License

## Thanks
Thank's to the Rhasspy's Piper software.
Thank's to [HirCoir-Piper-TTS-Tools](https://github.com/HirCoir/Piper-TTS-Tools) for inspiration.
