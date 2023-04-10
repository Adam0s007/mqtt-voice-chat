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

### Mute and Unmute functionality

When the application is muted, it will queue all incoming messages along with their timestamps. Once the mute button is toggled off, the application will play and display all the queued messages in the main window along with the sender's ID and the timestamp of when the message was received. This feature ensures that users can catch up on the messages they might have missed while the application was muted.

### Microphone functionality
When the "Speak" button is clicked, the application starts listening for voice input. As the user speaks, the microphone remains active and listening. Once the user stops speaking and there is a pause in speech, the voice message is sent automatically. The microphone will continue to listen for subsequent voice messages without the need to click the "Speak" button again.

To stop listening and deactivate the microphone, click "Turn off". This will toggle the microphone off, and the button will return to its original state.

### Continuous Message Playback

Thanks to the implementation of multithreading, the application is now capable of receiving and processing new messages even while it is playing back previously queued messages. This enhancement ensures that users can continue to communicate seamlessly without having to wait for the application to finish playing back messages. To achieve this, the application uses a separate thread to handle the message queue, allowing new incoming messages to be added to the queue without interrupting the ongoing playback.


### List of recipents
The application allows users to add new recipients for messages. This feature enables users to customize the list of recipients they want to send messages to, allowing for more targeted communication.


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


``` mosquitto_sub -h localhost -t "msg/mic" ```

2. To send messages to the application, publish them to the topic "msg/spk". You can do this using mosquitto_pub:


``` mosquitto_pub -h localhost -t "msg/spk" -m "your_nick|your_message_here" ```

3. When sending a message, users can now include their sender ID in the MQTT topic, which will be displayed in the application as their nickname. For example, to send a message with the sender ID "Joe_Smith", use the following command:

``` mosquitto_pub -h localhost -t "msg/spk/Joe/Smith" -m "your_message_here" ```

This feature only works when subscription topic is set to "msg/spk/#".

    

The application will launch, and you can start sending and receiving messages using the GUI.
