# Real-Time Audio Analyzer

A high-performance Python application for real-time analysis and visualization of audio pitch (frequency) and amplitude using the ASIO interface for minimal latency.

This project is designed for tasks requiring immediate feedback from an audio stream, such as musical instrument tuning, voice pitch monitoring, or technical diagnostics.

## Features

- **Real-time Analysis**: Measures fundamental frequency and RMS amplitude on the fly.
- **Low Latency**: Utilizes the **ASIO** audio interface via the `sounddevice` library to minimize input lag.
- **High Performance**: Employs NumPy and SciPy for efficient numerical computation and FFT analysis.
- **Live Visualization**: Uses `pyqtgraph` for smooth, real-time plotting of frequency and amplitude data.
- **Cross-Platform**: Built with libraries that support Windows, macOS, and Linux.

## How It Works

The application is built on a multi-threaded architecture to prevent UI blocking and ensure smooth audio data processing:

1.  **Audio Thread**: A dedicated callback, managed by `sounddevice`, captures audio buffers from the specified ASIO device and places them into a thread-safe queue.
2.  **Main Thread (GUI)**: The main application loop retrieves audio buffers from the queue, performs analysis, and updates the GUI.
    - **Amplitude**: Calculated as the Root Mean Square (RMS) of the audio buffer.
    - **Frequency**: Determined by performing a Fast Fourier Transform (FFT) on the data and finding the frequency bin with the highest magnitude.

## Requirements

- Python >= 3.6
- An audio interface with an ASIO driver

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/qasmark/real-time-audio-analyzer.git
    cd real-time-audio-analyzer
    ```

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```
    *(You will need to create a `requirements.txt` file containing `numpy`, `sounddevice`, `scipy`, `pyqtgraph`, and `PyQt5`)*

## Usage

1.  **Configure your audio device.**
    Before running, identify the exact name of your ASIO device. You can list all available devices by running:
    ```bash
    python -m sounddevice
    ```

2.  **Update the configuration.**
    Open `main.py` and set the `DEVICE_NAME` variable to the name of your device.

3.  **Run the application:**
    ```bash
    python main.py
    ```

## Demo

![Demo_GUI](demo.png)
 
