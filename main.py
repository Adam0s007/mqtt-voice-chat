import time
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
SUBSCRIPTION_TOPIC = "msg/spk" 
PUBLICATION_TOPIC = "msg/mic"
is_listening = False
removed_once = False
text_counter = 0

mute = False
messages_queue = Queue()

unheard_count = 0
unheard_label = None

# Lista możliwych odbiorców
recipients = ["msg/mic", "msg/mic/#", "msg/mic/Adam", "msg/mic/Piotr"]

def toggle_mute():
    global mute
    global unheard_count
    mute = not mute

    if mute:
        mute_button.config(bg='#f1c40f', text="Unmute")
    else:
        mute_button.config(bg='#8ac6d1', text="Mute")
        


def update_unheard_label():
    global unheard_count
    global unheard_label
    if unheard_count > 0:
        unheard_label.config(text=f"({unheard_count})")
    else:
        unheard_label.config(text="")


def process_message_queue():
    global messages_queue, mute,unheard_count

    while True:
        if not messages_queue.empty() and not mute:
            sender_id, message, timestamp = messages_queue.get()
            unheard_count -=1
            update_unheard_label()
            if message is not None:
                receiveMessage(message, sender_id, timestamp)
        time.sleep(0.5)

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






#otrzymywane wiadomosci i odpowiedni zapis nazwy uzytkownika.
# jesli nasluchujemy na msg/spk/# to sytuacja w ktorej: -t "msg/spk/Adam" -m"Joe|Witaj" -> Joe bedzie nazwą bo bedzie silniejsze 
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
    except UnicodeDecodeError:
        payload = message.payload.decode('latin-1')

    # Odczytaj nazwę użytkownika z tematu wiadomości
    topic_parts = message.topic.split('/')
    if len(topic_parts) >= 3:
        sender_id = "_".join(topic_parts[2:])
    else:
        sender_id = "Stranger"
    arr = payload.split('|', 1)
    if (len(arr) != 2):
        message_text = "".join(arr)
    else:
        sender_id_part, message_text = arr
        sender_id_part = sender_id_part.replace(" ", "")
        if sender_id_part:
            sender_id = sender_id_part

    global unheard_count
    timestamp = datetime.datetime.now().strftime('%H:%M')
    messages_queue.put((sender_id, message_text, timestamp))
    unheard_count += 1
    update_unheard_label()


def init_speaker():
    global engine
    engine = tts.init()
    engine.setProperty('volume', 0.7)
    engine.setProperty('rate', 190)



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
    text = text_entry.get('1.0', tk.END).strip()
    display_text = text_entry.get('1.0', tk.END).strip()
    send(PUBLICATION_TOPIC, text)

    addMessageOnCanvas(display_text,icon_person,"e",True,40,my_name)
    text_entry.delete('1.0', tk.END)


def speech_to_text():
    threading.Thread(target=_speech_to_text).start()

def _speech_to_text():
    global is_listening
    r = sr.Recognizer()
    with sr.Microphone() as source:
        if is_listening:
            audio = r.listen(source)
            is_listening = not is_listening
            mic_animation()
        else:
            return
    try:
        text = r.recognize_google(audio, language='pl_PL')
        sending_message = text
        send(PUBLICATION_TOPIC, sending_message)
        addMessageOnCanvas(text,icon_person,"e",True,40,my_name)
    except sr.UnknownValueError:
        print('nie rozumiem')
    except sr.RequestError as e:
        print('error:', e)



def mic_animation():
    global is_listening
    if not is_listening:
        mic_button.config(bg="#e5e5e5", text="Turn off")
        is_listening = True
        speech_to_text()
    else:
        mic_button.config(bg="#8ac6d1", text="Speak")
        is_listening = False




def set_placeholder(event=None):
    if text_entry.get('1.0', tk.END).strip() == '':
        text_entry.insert('1.0', 'Enter your message...')
        text_entry.config(fg='#777777')

def remove_placeholder(event=None):
    if text_entry.get('1.0', tk.END).strip() == 'Enter your message...':
        text_entry.delete('1.0', tk.END)
        text_entry.config(fg='#000000')



def is_broker_running(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0



    



def create_custom_event(widget):
    variable = tk.StringVar()
    variable.trace("w", lambda *args: widget.event_generate("<<NameChanged>>"))
    widget.config(textvariable=variable)
    return variable

def on_name_change(event):
    global my_name
    my_name = myName_entry.get().strip() or "username"


def toggle_topic_subscription(event=None):
    global client
    global SUBSCRIPTION_TOPIC
    global change_topic_button

    if SUBSCRIPTION_TOPIC == "msg/spk":
        SUBSCRIPTION_TOPIC = "msg/spk/#"
        change_topic_button.config(text="Change to 'msg/spk'")
    else:
        SUBSCRIPTION_TOPIC = "msg/spk"
        change_topic_button.config(text="Change to 'msg/spk/#'")
    
    client.unsubscribe("msg/spk")
    client.unsubscribe("msg/spk/#")
    client.subscribe([(SUBSCRIPTION_TOPIC,0)])


def create_change_topic_button(parent_frame):
    
    button = ttk.Button(parent_frame, text="Change to 'msg/spk/#'", command=toggle_topic_subscription, style='ChangeTopic.TButton', cursor='hand2')
    return button

def change_publication_topic(new_topic):
    global PUBLICATION_TOPIC
    PUBLICATION_TOPIC = new_topic
    #print(f"Zmieniono temat publikacji na: {PUBLICATION_TOPIC}")

# Funkcja dodająca nowego odbiorcę
def add_recipient():
    new_recipient = new_recipient_entry.get().strip()
    if new_recipient and new_recipient not in recipients:
        recipients.append(new_recipient)
        option_menu["values"] = recipients
        new_recipient_entry.delete(0, tk.END)


if __name__ == "__main__":

    if not is_broker_running(BROKER,1883):
        print("Mosquitto is OFF")
        exit(1)


    root = tk.Tk()
    root.title("MQTT Communication App")

    root.geometry('700x600')
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
    style.configure('TButton', font=('Roboto', 14), background='#3498db', foreground='#000', width=10, pady=8, borderwidth=0, activebackground='#2980b9')

    style.configure('TEntry', font=('Roboto', 14), background='rgba(255, 255, 255)', foreground='#000000', width=30, borderwidth=0)
    style.configure('ChangeTopic.TButton', font=('Roboto', 10), background='#3498db', foreground='#000', width=20, pady=8, borderwidth=0, activebackground='#2980b9')

    

    # widgety
    canvas_frame = tk.Frame(root, bg='#ffffff')
    canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    graph_canvas = tk.Canvas(canvas_frame, bg='#ffffff', highlightthickness=0)
    graph_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=graph_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


    graph_canvas.create_text(250, 150, text="Messages will appear here", fill='#333333', font=('Roboto', 14), anchor='center')

    text_entry_frame = ttk.Frame(root, style='TLabel')
    text_entry_frame.pack(fill=tk.X, padx=50, pady=10)

    text_entry = tk.Text(text_entry_frame, font=('Roboto', 14), background='white', foreground='#000000', width=20, height=2.5, borderwidth=0, wrap=tk.WORD)
    text_entry.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill=tk.X)

    text_entry.bind('<FocusIn>', remove_placeholder)
    text_entry.bind('<FocusOut>', set_placeholder)

    text_entry.insert('1.0', 'Enter your message...')
    text_entry.config(fg='#777777')

    send_text_button = ttk.Button(text_entry_frame, text="Send", command=send_text_message, style='TButton', cursor='hand2')
    send_text_button.pack(side=tk.LEFT, padx=5, pady=5)



    buttons_frame = tk.Frame(root, bg='#222222')
    buttons_frame.pack(padx=20, pady=10)
    
    #mikrofon
    mic_button = tk.Button(buttons_frame, text="Speak", command=mic_animation, bg='#8ac6d1', fg='#333333', font=('Roboto', 12), width=10, height=6, relief=tk.RAISED, bd=0, activebackground='#e5e5e5', activeforeground='#333333', cursor='hand2')
    mic_button.pack(side=tk.LEFT, padx=5)

    mute_button = tk.Button(buttons_frame, text="Mute", command=toggle_mute, bg='#8ac6d1', fg='#333333', font=('Roboto', 12), width=10, height=6, relief=tk.RAISED, bd=0, activebackground='#e5e5e5', activeforeground='#333333', cursor='hand2')
    mute_button.pack(side=tk.LEFT, padx=5)

    unheard_label = tk.Label(buttons_frame, text="", font=('Roboto', 14, "bold"), bg='#222222', activeforeground='#333333', fg='#c03207')
    unheard_label.pack(side=tk.LEFT, padx=5)

    name_frame = tk.Frame(buttons_frame, bg='#222222')
    name_frame.pack(side=tk.RIGHT, padx=5)

    name_label = tk.Label(name_frame, text="Your Name:", font=('Roboto', 12), bg='#222222', fg='#ffffff')
    myName_entry = ttk.Entry(name_frame, font=('Roboto', 14), background='white', foreground='#000000', width=15)
    name_label.pack(side=tk.TOP, padx=5)
    myName_entry.pack(side=tk.TOP, padx=5)
    myName_entry.insert(0, my_name)
    name_var = create_custom_event(myName_entry)
    myName_entry.bind("<<NameChanged>>", on_name_change)



    change_topic_frame = tk.Frame(buttons_frame, bg='#222222')
    change_topic_frame.pack(side=tk.LEFT, padx=5)
    change_topic_button = create_change_topic_button(buttons_frame)
    change_topic_button.pack(in_=change_topic_frame, padx=5, pady=(0, 5))
    # Utwórz zmienną, która przechowuje aktualnie wybrany temat
    current_topic = tk.StringVar(root)
    current_topic.set(recipients[0])  # Ustaw domyślny temat na pierwszy z listy
    
    style.configure('OptionMenu.TMenubutton', font=('Roboto', 12), background='#3498db', foreground='#000', width=20, pady=8, borderwidth=0, activebackground='#2980b9')
    #style.map('OptionMenu.TMenubutton', background=[('disabled', '#222222'), ('pressed', '#2980b9'), ('active', '#2980b9')], foreground=[('disabled', '#777777')])
    style.configure('TCombobox', font=('Roboto', 12), background='#3498db', foreground='#000', fieldbackground='#ffffff', selectbackground='#2980b9', selectforeground='#ffffff')
    style.map('TCombobox', fieldbackground=[('readonly', '#ffffff')], selectbackground=[('readonly', '#2980b9')], selectforeground=[('readonly', '#ffffff')])
    
    option_menu = ttk.Combobox(change_topic_frame, textvariable=current_topic, values=recipients, state='readonly', style='TCombobox')
    option_menu.bind('<<ComboboxSelected>>', change_publication_topic)
    option_menu.current(0)  # Ustaw domyślny temat na pierwszy z listy
    option_menu.pack(pady=(0, 5))
    # Dodaj nowy Label
    new_recipient_label = ttk.Label(change_topic_frame, text="Add recipient:", style='TLabel')
    new_recipient_label.pack(pady=(5, 0))

    # Dodaj nowy Entry
    new_recipient_entry = ttk.Entry(change_topic_frame, font=('Roboto', 12), width=20, style='TEntry')
    new_recipient_entry.pack(pady=(0, 5))

    # Dodaj przycisk "Dodaj"
    add_button = ttk.Button(change_topic_frame, text="Dodaj", command=add_recipient, style='TButton', cursor='hand2')
    add_button.pack(pady=(0, 5))

    
    

    init_broker()
    init_speaker()


    message_queue_thread = threading.Thread(target=process_message_queue, daemon=True)
    message_queue_thread.start()

    root.mainloop()
    client.loop_stop()