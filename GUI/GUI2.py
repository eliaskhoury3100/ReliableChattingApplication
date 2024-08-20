import tkinter as tk
from tkinter import scrolledtext, END, filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import socket
from datetime import datetime
import base64

class ChatAppGUI:
    def __init__(self, title, peer_address, peer_port, listen_port):
        self.peer_address = peer_address
        self.peer_port = peer_port
        self.listen_port = listen_port

        self.window = tk.Tk()
        self.window.title("EECE350 Chatting App: " + title)
        self.window.configure(bg="#f2f2f2")

        chat_frame = ttk.Frame(self.window)
        chat_frame.configure(style="ChatFrame.TFrame")
        chat_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.chat_box = scrolledtext.ScrolledText(chat_frame, width=50, height=20, bg="white", borderwidth=0, highlightthickness=0)
        self.chat_box.tag_configure("user_msg", foreground="#000000", font=("Arial", 12, "bold"))
        self.chat_box.tag_configure("other_msg", foreground="#000000", font=("Arial", 12, "bold"))
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_box.config(state=tk.DISABLED)

        buttonframe = ttk.Frame(self.window)
        buttonframe.configure(style="ButtonFrame.TFrame")
        buttonframe.pack(padx=10, pady=10)

        iconmsg = Image.open("msg.png")
        iconmsg = iconmsg.resize((32, 31))
        iconmsg = ImageTk.PhotoImage(iconmsg)

        self.entrymsg = ttk.Entry(buttonframe, width=40, font=("Arial", 12, "bold"))
        self.entrymsg.pack(side=tk.LEFT, padx=5, pady=5)
        self.entrymsg.bind("<Return>", self.send_message)
        self.entrymsg.bind("<KeyRelease>", self.typing_indicator)

        self.sendbutton = ttk.Button(buttonframe, image=iconmsg, command=self.send_message)
        self.sendbutton.image = iconmsg
        self.sendbutton.configure(style="IconButton.TButton")
        self.sendbutton.pack(side=tk.LEFT, padx=5)

        iconfile = Image.open("file.png")
        iconfile = iconfile.resize((32, 31))
        iconfile = ImageTk.PhotoImage(iconfile)

        self.filebutton = ttk.Button(buttonframe, image=iconfile, command=self.send_file)
        self.filebutton.image = iconfile
        self.filebutton.configure(style="IconButton.TButton")
        self.filebutton.pack(side=tk.LEFT)

        ttk.Style().configure("EntryStyle.TEntry", padding=6, relief="solid", bordercolor="#d9edff")

        # Create a server socket for receiving messages
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', self.listen_port))
        self.server_socket.listen(1)

        self.typing = False

    def accept_connections(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(target=self.receive_messages, args=(client_socket,)).start()

    def receive_messages(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if data:
                    current_time = datetime.now().strftime('%H:%M:%S')
                    if data.startswith(b"FILE:"):
                        # Received a file
                        file_name = base64.b64decode(data[5:]).decode()
                        self.receive_file(client_socket, file_name)
                    elif data.startswith(b"TYPING:"):
                        # Typing indicator
                        self.update_typing_status(True)
                    else:
                        # Received a text message
                        message = data.decode()
                        message_with_time = f"{current_time} Peer: {message}"
                        self.chat_box.config(state=tk.NORMAL)
                        self.chat_box.insert(tk.END, message_with_time + "\n", "other_msg")
                        self.chat_box.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", str(e))
                break

    def send_message(self, event=None):
        message = self.entrymsg.get()
        if message:
            current_time = datetime.now().strftime('%H:%M:%S')
            message_with_time = f"{current_time} You: {message}"
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, message_with_time + "\n", "user_msg")
            self.chat_box.config(state=tk.DISABLED)
            self.entrymsg.delete(0, tk.END)
            # Send message to the peer
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((self.peer_address, self.peer_port))
                client_socket.sendall(message.encode())
                client_socket.close()
            except Exception as e:
                messagebox.showerror("ERROR!!! Peer Unavailable: Please request connection", str(e))

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            messagebox.showinfo("Transfer File", "File Uploaded")
            # Read and send the file
            try:
                with open(file_path, "rb") as file:
                    file_data = file.read()
                
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((self.peer_address, self.peer_port))
                
                # Send file indicator and file name
                encoded_file_name = base64.b64encode(file_path.encode())
                client_socket.sendall(f"FILE:".encode() + encoded_file_name)
                
                # Send file data
                client_socket.sendall(file_data)
                
                client_socket.close()
            except Exception as e:
                messagebox.showerror("ERROR!!! Peer Unavailable: Please request connection", str(e))

    def receive_file(self, client_socket, file_name):
        try:
            with open(file_name, "wb") as file:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    file.write(data)
            current_time = datetime.now().strftime('%H:%M:%S')
            message_with_time = f"{current_time} Peer: File Received: {file_name}\n"
            self.chat_box.config(state=tk.NORMAL)
            self.chat_box.insert(tk.END, message_with_time, "other_msg")
            self.chat_box.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_typing_status(self, typing):
        self.typing = typing
        if typing:
            self.window.title("Typing...")
        else:
            self.window.title("EECE350 Chatting App")

    def typing_indicator(self, event=None):
        if self.entrymsg.get() and not self.typing:
            # Send typing indicator if there is text in the message entry and typing indicator is not already on
            threading.Thread(target=self.send_typing_indicator).start()
        elif not self.entrymsg.get() and self.typing:
            # Update typing status if message entry is empty and typing indicator is on
            self.update_typing_status(False)

    def send_typing_indicator(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.peer_address, self.peer_port))
            client_socket.sendall(b"TYPING:")
            client_socket.close()
        except Exception as e:
            messagebox.showerror("ERROR!!! Peer Unavailable: Please request connection", str(e))

    def run(self):
        threading.Thread(target=self.accept_connections).start()
        self.window.mainloop()


peer2 = ChatAppGUI("Second Client", "localhost", 5555, 5556)
peer2.run()
