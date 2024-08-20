import tkinter as tk
from time import strftime

class DigitalClockApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Digital Clock")

        # Create a label for displaying the time
        self.clock_label = tk.Label(self.root, font=('calibri', 40, 'bold'), background='purple', foreground='white')
        self.clock_label.pack(anchor='center')

        # Update the clock every second
        self.update_clock()

    def update_clock(self):
        current_time = strftime('%H:%M:%S %p')  # Get the current time
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)  # Update every second

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DigitalClockApp()
    app.run()
