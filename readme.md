# Motion Capture Audio Recording Application

This is an audio recording application designed specifically to work in conjunction with motion capture software. It listens for UDP packets to start and stop audio recordings, providing an effortless way to record reference audio in sync with motion capture data. While it's tailored for Qualisys mocap systems, it is compatible with any motion capture software that sends UDP start/stop commands.

Use-cases might be to record comments on the recording during the session to repace notes.

## Features

- **Seamless Integration with Motion Capture**: Automatically starts and stops audio recordings based on UDP commands, ensuring synchronicity with motion capture sessions.
- **Customizable Audio Formats**: Provides multiple audio format options to best suit your needs.
- **Device Selection**: Choose the audio input device right from the GUI.
- **Logging**: Keep track of recording actions and any errors through the integrated log window.
- **Tailored for Qualisys**: Special considerations for Qualisys users to ensure correct file naming.

## Requirements

- Python 3.x
- PySide6

## Installation

1. Ensure you have Python 3.x installed. Download from [here](https://www.python.org/downloads/).
2. Clone this repository or download the source code.
   ```
   git clone [your-repository-url]
   ```
3. Navigate to the project directory and install the required libraries:
   ```
   pip install PySide6
   ```
4. Run the application:
   ```
   python audio_recorder.py
   ```

## Usage

1. **Launch Application**: Start the application and you will be presented with a simple GUI.
2. **Audio Device and Format**: Select the desired audio device and format from the dropdown menus.
3. **Filename for Qualisys Users**: If you're using Qualisys, ensure you set a filename in the recording window to derive the correct name for the audio file.
4. **UDP Commands**: The application listens on port `8989` by default. Send the appropriate UDP commands from your motion capture software to start and stop the audio recordings.

## Contributing

Contributions are welcome! If you have improvements or bug fixes, fork the repository and submit pull requests. For significant changes, open an issue first to discuss your ideas.

## License

[MIT](https://choosealicense.com/licenses/mit/)

