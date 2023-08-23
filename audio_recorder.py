"""
Audio Recorder and UDP Controller
---------------------------------

This module provides a GUI-based audio recording application that can start and stop recordings
based on UDP commands received. 

Features:
- Record audio in various formats and codecs.
- Select audio input devices from available options.
- UDP listener for remote start and stop commands.
- GUI log window to capture and display the status and any potential errors.
- Dynamic port assignment for UDP listener.

Dependencies:
- PySide6
- xml.etree.ElementTree
- socket, os

Usage:
Simply run this script. The GUI will provide options for device and format selection.
The UDP listener will wait for XML-formatted commands to start and stop recordings.
When a CaptureStart command is received, recording will commence using the selected device and format.
On CaptureStop, the recording will end.

Author: Martin Holmberg
Email: martin.holmberg@qualisys.se
Date: 2023-08-23
Version: 1.0
"""

import os
import socket
from xml.etree import ElementTree as ET
from PySide6.QtCore import QThread, Signal, QObject, QUrl
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QLabel, QComboBox, QWidget,QLineEdit
from PySide6.QtMultimedia import QAudioInput, QMediaCaptureSession, QMediaRecorder, QMediaFormat, QMediaDevices


def clean_xml_data(data):
    closing_tags = ['</CaptureStop>', '</CaptureStart>']
    for tag in closing_tags:
        end_index = data.find(tag)
        if end_index != -1:
            return data[:end_index + len(tag)]
    return data

class AudioRecorder(QObject):


    FILE_EXTENSION_MAP = {
        QMediaFormat.AudioCodec.MP3: (QMediaFormat.FileFormat.MP3, ".mp3"),
        QMediaFormat.AudioCodec.AAC: (QMediaFormat.FileFormat.AAC, ".aac"),
        # AC3 doesn't have a corresponding file format in the list you've shared earlier, assuming ".ac3" as extension:
        QMediaFormat.AudioCodec.AC3: (QMediaFormat.FileFormat.UnspecifiedFormat, ".ac3"),
        # Similarly, for EAC3:
        QMediaFormat.AudioCodec.EAC3: (QMediaFormat.FileFormat.UnspecifiedFormat, ".eac3"),
        QMediaFormat.AudioCodec.FLAC: (QMediaFormat.FileFormat.FLAC, ".flac"),
        # Assuming ".truehd" for DolbyTrueHD:
        QMediaFormat.AudioCodec.DolbyTrueHD: (QMediaFormat.FileFormat.UnspecifiedFormat, ".truehd"),
        # Assuming ".opus" for Opus:
        QMediaFormat.AudioCodec.Opus: (QMediaFormat.FileFormat.Ogg, ".opus"),
        # Assuming ".ogg" for Vorbis:
        QMediaFormat.AudioCodec.Vorbis: (QMediaFormat.FileFormat.Ogg, ".ogg"),
        QMediaFormat.AudioCodec.Wave: (QMediaFormat.FileFormat.Wave, ".wav"),
        QMediaFormat.AudioCodec.WMA: (QMediaFormat.FileFormat.WMA, ".wma"),
        # Assuming ".alac" for ALAC:
        QMediaFormat.AudioCodec.ALAC: (QMediaFormat.FileFormat.UnspecifiedFormat, ".alac"),
    }

    log_message = Signal(str)
    log_error = Signal(str)

    def handle_error(self, error, errorString):
        self.log_error.emit(f"Recorder error: {error}, {errorString}")

    def __init__(self, sample_rate=44100, channels=2):
        super().__init__()
        media_format = QMediaFormat()
        self.available_formats = media_format.supportedAudioCodecs(
            QMediaFormat.Encode)

        self.available_format_descriptions = [
            QMediaFormat.audioCodecDescription(codec) for codec in self.available_formats]
        self.session = QMediaCaptureSession()
        self.audioInput = QAudioInput()
        self.session.setAudioInput(self.audioInput)
        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)
        default_format = QMediaFormat()
        default_format.setAudioCodec(QMediaFormat.AudioCodec.MP3)
        default_format.setFileFormat(QMediaFormat.FileFormat.MP3)
        self.recorder.setMediaFormat(default_format)
        self.recorder.setQuality(QMediaRecorder.HighQuality)
        self.available_devices = [device.description()
                                  for device in QMediaDevices.audioInputs()]
        self.recorder.errorOccurred.connect(self.handle_error)
        
    def set_audio_device(self, device_index):
        selected_device = QMediaDevices.audioInputs()[device_index]
        self.session.audioInput().setDevice(selected_device)
        self.log_message.emit(
            f"Selected Device: {self.session.audioInput().device().description()}")

    def set_format(self, format_index):
        selected_codec = self.available_formats[format_index]
        media_format = QMediaFormat()
        media_format.setAudioCodec(selected_codec)
        file_format, file_extension = self.FILE_EXTENSION_MAP.get(
            selected_codec)
        if file_format:
            media_format.setFileFormat(file_format)
        self.recorder.setMediaFormat(media_format)

        self.log_message.emit(
            f"Selected Format: {self.available_format_descriptions[format_index]}")

    def start_recording(self, filepath, filename):
        codec = self.recorder.mediaFormat().audioCodec()
        file_format, extension = self.FILE_EXTENSION_MAP.get(
            codec, ("", ".unknown"))
        filenamepath = os.path.join(filepath, filename + extension)
        url = QUrl.fromLocalFile(os.fspath(filenamepath))
        self.recorder.setOutputLocation(url)
        self.recorder.record()
        self.log_message.emit("Recording started to " + url.toString())

    def stop_recording(self):
        self.recorder.stop()
        self.log_message.emit("Recording stopped.")


class UDPAudioController(QThread):
    captureStart = Signal(str, str)  # filepath, filename, format
    captureStop = Signal()   # filepath, filename, format
    errorOccurred = Signal(str)  # Error message signal
    _port = None
    @property
    def port(self):
        return self._port
    @port.setter
    def port(self, value):
        #if self.running:
         #   raise ValueError("Can't change port while the service is running")
        print("Changing port")
        # Close the existing socket if it's open

        self._port = value

        
    def __init__(self, port=8989):
        super().__init__()
        self._port = 12345  # some default port
        self.socket_closed = True
        self.received_packet_ids = set()
        self.running = True
        self.port = port
        self.socket_closed = False

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(("", self.port))
        except socket.error as e:
            # Emitting the error message
            self.errorOccurred.emit(f"Socket Error: {str(e)}")
            self.sock = None
            return
        print("Running")
        print("Port: ", self.port)
        print("Socket: ", self.sock)
        self.running = True
        while self.running:
            try:
                print("Waiting for data")
                data, addr = self.sock.recvfrom(1024)
                print("Data received")
            except socket.error:
                print("Socket error")
                break
            data_str = data.decode('utf-8')
            cleaned_data_str = clean_xml_data(data_str)
            try:
                root = ET.fromstring(cleaned_data_str)
            except ET.ParseError as e:
                self.errorOccurred.emit(f"XML parsing error: {str(e)}")
                continue
            packet_id = int(root.find("./PacketID").get("VALUE"))

            if packet_id in self.received_packet_ids:
                continue

            self.received_packet_ids.add(packet_id)
            print("Packet ID: ", packet_id)
            command = root.tag
            if command == 'CaptureStart':
                filename = root.find("./Name").get("VALUE")
                filepath = root.find("./DatabasePath").get("VALUE")
                self.captureStart.emit(filepath, filename)
            elif command == 'CaptureStop':
                filename = root.find("./Name").get("VALUE")
                filepath = root.find("./DatabasePath").get("VALUE")
                self.captureStop.emit()

    def stop(self):  # Add this method to stop the thread
        self.running = False
        print("Stopping")
        print(self.sock)
        if self.sock:
            print("Closing socket")
            self.sock.close()
            self.socket_closed = True
        self.wait()  # Wait for the thread to finish


class RecorderGUI(QMainWindow):
    def __init__(self, recorder, udp_controller):
        super().__init__()
        self.recorder = recorder
        self.udp_controller = udp_controller
        self.recorder.log_message.connect(self.log_message)
        self.initUI()

    def initUI(self):
        centralWidget = QWidget()
        layout = QVBoxLayout()

        self.statusLabel = QLabel("Stopped")
        self.statusLabel.setStyleSheet("color: red")
        layout.addWidget(self.statusLabel)

        self.logWindow = QTextEdit()
        self.logWindow.setReadOnly(True)
        layout.addWidget(self.logWindow)

        self.deviceComboBox = QComboBox()
        available_devices = QMediaDevices.audioInputs()
        for device in available_devices:
            self.deviceComboBox.addItem(device.description())
        layout.addWidget(self.deviceComboBox)
        self.deviceComboBox.currentIndexChanged.connect(
            self.recorder.set_audio_device)

        self.formatComboBox = QComboBox()
        self.formatComboBox.addItems(
            self.recorder.available_format_descriptions)
        self.formatComboBox.currentIndexChanged.connect(
            self.recorder.set_format)
        index_of_mp3 = self.formatComboBox.findText("MP3")
        if index_of_mp3 != -1:  # If MP3 is found in the ComboBox
            self.formatComboBox.setCurrentIndex(index_of_mp3)
        layout.addWidget(self.formatComboBox)
        self.formatComboBox.currentIndexChanged.connect(
            self.update_file_format)
        self.portLabel = QLabel("Port:")
        layout.addWidget(self.portLabel)
        self.portInput = QLineEdit()
        self.portInput.setText("8989")  # Default port
        layout.addWidget(self.portInput)
        self.portInput.editingFinished.connect(self.update_port)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
    
    def update_file_format(self, index):
        selected_format = self.formatComboBox.itemText(index)
        self.udp_controller.file_format = selected_format

    def update_audio_device(self, index):
        selected_device = QMediaDevices.audioInputs()[index]
        audio_input = QAudioInput(selected_device)
        self.recorder.session.setAudioInput(audio_input)
        self.recorder.log_message.emit(
            f"Selected Device: {selected_device.description()}")

    def log_message(self, message):
        self.logWindow.append(message)

    def log_error(self, message):
        self.logWindow.append(f'<span style="color: red;">{message}</span>')
    def update_port(self):
        try:
            # Try converting the input to an integer
            port = int(self.portInput.text())
            # If successful, update the port in the UDP controller
            self.udp_controller.port = port
            self.udp_controller.stop()
            self.udp_controller.start()
        except ValueError:
            # If not a valid number, perhaps show a warning in the log
            self.log_error("Invalid port number.")

def main():
    app = QApplication([])
    recorder = AudioRecorder()
    udp_controller = UDPAudioController()
    udp_controller.captureStart.connect(recorder.start_recording)
    udp_controller.captureStop.connect(recorder.stop_recording)

    window = RecorderGUI(recorder, udp_controller)
    udp_controller.errorOccurred.connect(window.log_error)
    recorder.log_error.connect(window.log_error)
    udp_controller.start()
    window.show()

    exit_code = app.exec()
    udp_controller.stop()
    return exit_code


if __name__ == '__main__':
    main()
