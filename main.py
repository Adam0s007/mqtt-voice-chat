import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import speech_recognition as sr
import pyttsx3 as tts
from PIL import Image, ImageTk
from queue import Queue
import datetime
import threading
import socket


my_name = ""
client = ""
BROKER = "localhost"
SUBSCRIPTION_TOPIC = "msg/spk" #w kodzie dodamy /usr gdzie usr to bedzie moje id
PUBLICATION_TOPIC = "msg/mic"

removed_once = False
text_counter = 0

mute = False
messages_queue = Queue()

unheard_count = 0
unheard_label = None



def toggle_mute():
    global mute
    global unheard_count
    mute = not mute

    if mute:
        mute_button.config(bg='#f1c40f', text="Unmute")
    else:
        mute_button.config(bg='#8ac6d1', text="Mute")
        play_queued_messages()
        unheard_count = 0
        update_unheard_label()


def update_unheard_label():
    global unheard_count
    global unheard_label
    if unheard_count > 0:
        unheard_label.config(text=f"{unheard_count} unheard messages")
    else:
        unheard_label.config(text="")


def play_queued_messages():
    threading.Thread(target=_play_queued_messages).start()

def _play_queued_messages():
    global messages_queue
    
    while not messages_queue.empty():
        sender_id,message,timestamp = messages_queue.get()
        if message is not None:
            receiveMessage(message,sender_id,timestamp)
    messages_queue = Queue()

def receiveMessage(message,sender_id,time=None):
    addMessageOnCanvas(message,icon,sender_id=sender_id,time=time)
    speakNow(message,sender_id,time)

def send(topic, payload):
    global client
    client.publish(topic, payload, retain=True)




def wrap_text(text, max_width=70):
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        if len(' '.join(current_line + [word])) <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines



def addMessageOnCanvas(sendText, icon, param1="w", is_user_message=False, value=-40, sender_id=None,time=None):
    global removed_once
    global text_counter
    global my_name
    client_name = sender_id if sender_id else my_name
    if not removed_once:
        graph_canvas.delete("all")  # usunięcie wcześniejszych elementów z kanwy
        removed_once = True
    canvas_width = graph_canvas.winfo_width()
    text_x = 50 if not is_user_message else (canvas_width - 50)
    text_y = 100 + text_counter * 35 
    wrapped_lines = wrap_text("("+time+") [" + client_name + "]: " + sendText) if time else wrap_text("[" + client_name + "]: " + sendText)
    graph_canvas.create_image(text_x + value, text_y, image=icon, anchor=param1)  # dodaj ikonę przed tekstem
    for line in wrapped_lines:
        text_y = 100 + text_counter * 35 
        graph_canvas.create_text(text_x, text_y, text=line, fill='black', font=('Roboto', 12), tags="current_text", anchor=param1)
        text_counter += 1



def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
    except UnicodeDecodeError:
        payload = message.payload.decode('latin-1')
    arr = payload.split('|', 1)
    if (len(arr) != 2):
        sender_id = "Stranger"
        message_text = "".join(arr)
    else:
        sender_id,message_text = arr
        sender_id = sender_id.replace(" ", "")
    if mute:
        global unheard_count
        timestamp = datetime.datetime.now().strftime('%H:%M')
        messages_queue.put((sender_id,message_text,timestamp))
        unheard_count += 1
        update_unheard_label()
    else:
        play_queued_messages() if not messages_queue.empty() else receiveMessage(message_text,sender_id)



def init_speaker():
    global engine
    engine = tts.init()
    engine.setProperty('volume', 0.7)
    engine.setProperty('rate', 190)


    

def speakNow(text, sender_id, time=None):
    if time:
        engine.say("Wiadomość od " + sender_id + ": " + text + " wysłano " + time)
    else:
        engine.say("Wiadomość od " + sender_id + ": " + text)
    engine.runAndWait()


def init_broker():
    global client
    global my_name
    client = mqtt.Client("username")
    my_name = client._client_id.decode('utf-8')
    client.on_message = on_message
    client.connect(BROKER)
    client.loop_start()
    client.subscribe([(SUBSCRIPTION_TOPIC, 0)])

def send_text_message():
    global my_name
    text = my_name + "|" + text_entry.get('1.0', tk.END).strip()
    display_text = text_entry.get('1.0', tk.END).strip()
    send(PUBLICATION_TOPIC, text)

    addMessageOnCanvas(display_text,icon_person,"e",True,40,my_name)
    text_entry.delete('1.0', tk.END)


def speech_to_text():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio, language='pl_PL')
        sending_message = my_name + "|" + r.recognize_google(audio, language='pl_PL')
        send(PUBLICATION_TOPIC, sending_message)
        addMessageOnCanvas(text,icon_person,"e",True,40,my_name)
    except sr.UnknownValueError:
        print('nie rozumiem')
    except sr.RequestError as e:
        print('error:', e)


def _mic_animation():
    mic_button.config(relief=tk.SUNKEN)
    root.update()
    mic_button.after(100, lambda: mic_button.config(relief=tk.RAISED))
    root.update()

def mic_animation():
    threading.Thread(target=_mic_animation).start()
    




def set_placeholder(event=None):
    if text_entry.get('1.0', tk.END).strip() == '':
        text_entry.insert('1.0', 'Wpisz wiadomość...')
        text_entry.config(fg='#777777')

def remove_placeholder(event=None):
    if text_entry.get('1.0', tk.END).strip() == 'Wpisz wiadomość...':
        text_entry.delete('1.0', tk.END)
        text_entry.config(fg='#000000')



def is_broker_running(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def create_name_label(parent_frame):
    label = tk.Label(parent_frame, text="Your Name:", font=('Roboto', 12), bg='#222222', fg='#ffffff')
    return label


def create_name_input(parent_frame):
    entry = ttk.Entry(parent_frame, font=('Roboto', 14), background='white', foreground='#000000', width=15)
    entry.insert(0, my_name)
    return entry


def create_custom_event(widget):
    variable = tk.StringVar()
    variable.trace("w", lambda *args: widget.event_generate("<<NameChanged>>"))
    widget.config(textvariable=variable)
    return variable

def on_name_change(event):
    global my_name
    my_name = myName_entry.get().strip() or "username"


if __name__ == "__main__":

    if not is_broker_running(BROKER,1883):
        print("Mosquitto is OFF")
        exit(1)


    root = tk.Tk()
    root.title("MQTT Communication App")

    root.geometry('700x500')
    root.configure(bg='#222222')
    root.resizable(width=False, height=False)

    icon_image = Image.open('icon.png')  # lub 'emoji.png'
    icon_image = icon_image.resize((30, 30))  # dostosuj rozmiar
    icon = ImageTk.PhotoImage(icon_image)
    root.iconphoto(True, icon)

    icon_anotherPerson = Image.open('person.jpg')  # lub 'emoji.png'
    icon_anotherPerson = icon_anotherPerson.resize((30, 30))  # dostosuj rozmiar
    icon_person = ImageTk.PhotoImage(icon_anotherPerson)


    # definicja stylów ttk
    style = ttk.Style()
    style.theme_use('default')
    style.configure('TLabel', font=('Roboto', 14), background='#222222', foreground='#fff')
    style.configure('TButton', font=('Roboto', 14), background='#3498db', foreground='#fff', width=10, pady=8, borderwidth=0, activebackground='#2980b9')

    style.configure('TEntry', font=('Roboto', 14), background='rgba(255, 255, 255)', foreground='#000000', width=30, borderwidth=0)



    # widgety
    canvas_frame = tk.Frame(root, bg='#ffffff')
    canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    graph_canvas = tk.Canvas(canvas_frame, bg='#ffffff', highlightthickness=0)
    graph_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=graph_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


    graph_canvas.create_text(250, 150, text="Tutaj pojawią się wiadomości", fill='#333333', font=('Roboto', 14), anchor='center')

    text_entry_frame = ttk.Frame(root, style='TLabel')
    text_entry_frame.pack(fill=tk.X, padx=50, pady=10)

    text_entry = tk.Text(text_entry_frame, font=('Roboto', 14), background='white', foreground='#000000', width=20, height=2.5, borderwidth=0, wrap=tk.WORD)
    text_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

    text_entry.bind('<FocusIn>', remove_placeholder)
    text_entry.bind('<FocusOut>', set_placeholder)

    text_entry.insert('1.0', 'Wpisz wiadomość...')
    text_entry.config(fg='#777777')

    send_text_button = ttk.Button(text_entry_frame, text="Send", command=send_text_message, style='TButton', cursor='hand2')
    send_text_button.pack(side=tk.LEFT, padx=5, pady=5)



    buttons_frame = tk.Frame(root, bg='#222222')
    buttons_frame.pack(padx=20, pady=10)

    mic_button = tk.Button(buttons_frame, text="Speak", command=speech_to_text, bg='#8ac6d1', fg='#333333', font=('Roboto', 12), width=10, height=6, relief=tk.RAISED, bd=0, activebackground='#e5e5e5', activeforeground='#333333', cursor='hand2')
    mic_button.pack(side=tk.LEFT, padx=5)

    mute_button = tk.Button(buttons_frame, text="Mute", command=toggle_mute, bg='#8ac6d1', fg='#333333', font=('Roboto', 12), width=10, height=6, relief=tk.RAISED, bd=0, activebackground='#e5e5e5', activeforeground='#333333', cursor='hand2')
    mute_button.pack(side=tk.LEFT, padx=5)
    mic_button.bind('<Button-1>', lambda event: mic_animation())


    unheard_label = tk.Label(buttons_frame, text="", font=('Roboto', 12), bg='#222222', fg='#ffffff')
    unheard_label.pack(side=tk.LEFT, padx=5)

    name_label = create_name_label(buttons_frame)
    name_label.pack(side=tk.LEFT, padx=5)

    myName_entry = create_name_input(buttons_frame)
    myName_entry.pack(side=tk.LEFT, padx=5)
    name_var = create_custom_event(myName_entry)
    myName_entry.bind("<<NameChanged>>", on_name_change)


    init_broker()
    init_speaker()

    root.mainloop()
    client.loop_stop()