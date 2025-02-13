<img src="./static/imgs/piper_web_logo.png" alt="Alt Text" width="256" height="256">

# Piper Hub
This is a web interface portal to the [Piper TTS](https://github.com/rhasspy/piper). It allows to do the following with a web browser:
* Download and Install Voices from [Huggingface: rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)
* Uninstall Voices
* Upload Custom Voices
* Generate Text-To-Speech with the selected voice.
* Download the audio generated via the web browser.

## Docker Deploying Application
Prerequisite:
Follow instructions from Docker to install docker on your platform.

Steps:
1. Open terminal and change directory to inside the Piper-Hub root. This will be the context to build the image.
2. Build Image:
`` docker build -t piper-hub:dev .``
**Note: 'dev' is just a made up tag, to tag this build.**
3. Compose Image:
``docker run -d --name piper-hub-container -p 5000:5000 piper-hub-image``
    * Port can be adjusted to ``{your_preferred_port}:5000``
    * If you want to volume mount for develop, then add before ``piper-hub-image``
    ``-v ${pwd}:/app``
4. Open web browser to http://localhost:5000 (non-secure)

### Docker Images
[Docker Hub Repo HLappano/Piper](https://hub.docker.com/r/hlappano/piper-hub)
Formats:
* arm64
* amd64

## License
MIT License

## Thanks
Thank's to the Rhasspy's Piper software.
Thank's to [HirCoir-Piper-TTS-Tools](https://github.com/HirCoir/Piper-TTS-Tools) for inspiration.
