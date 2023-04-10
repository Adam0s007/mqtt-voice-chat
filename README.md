MQTT Communication App
======================

A simple GUI-based MQTT communication application using Python and Tkinter that enables users to send and receive text and voice messages in real-time. The application displays messages allows users to mute incoming voice messages and view the number of unheard messages.

![App Screenshot](app_screenshot.png)

Features
--------

*   Real-time text and voice messaging
*   Mute/unmute functionality for incoming voice messages
*   Display of the number of unheard messages
*   Tkinter-based user-friendly interface

Requirements
------------

*   Python 3.x
*   Tkinter
*   paho-mqtt
*   speech\_recognition
*   pyttsx3
*   Pillow
*   Mosquitto MQTT broker

Installation
------------

1.  Install the required Python libraries:

   ``` pip install paho-mqtt speechrecognition pyttsx3 Pillow pyaudio ```
        

For platform-specific installation instructions, refer to the [PyAudio documentation](https://people.csail.mit.edu/hubert/pyaudio/).

3.  Install and configure the [Mosquitto MQTT broker](https://mosquitto.org/).

Usage
-----

Run the script `main.py`:

    ```python main.py```

## MQTT Topics

To properly use the MQTT Communication App, make sure to subscribe to the correct topic and send messages to the appropriate topic:

1. Run `mosquitto_sub` to subscribe to the topic "msg/mic":

```bash
mosquitto_sub -h localhost -t "msg/mic"

2. To send messages to the application, publish them to the topic "msg/spk". You can do this using mosquitto_pub:

```bash
mosquitto_pub -h localhost -t "msg/spk" -m "your_message_here"


    

The application will launch, and you can start sending and receiving messages using the GUI.
