import random
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from pydantic import BaseSettings
import requests

root = tk.Tk()
root.title('Label Widget Demo')

pastel_green = "#82e67e"
pastel_yellow = "#f7e283"
pastel_red = "#ff7c70"


class GlobalConfig(BaseSettings):
    G64_url = "http://169.254.150.100:8000/api/any/g64"


env_config = GlobalConfig()

label_timestamp = ttk.Label(
    root,
    text='1/1/1970 00:00:00', anchor='ne',
    font=("Helvetica", 20))

label_rads = ttk.Label(
    root,
    text='0', anchor='center',
    font=("Helvetica", 30))

label_entry = ttk.Label(
    root,
    anchor='center',
    font=("Helvetica", 70))

label_timestamp.pack(fill='x')
label_rads.pack(fill='x')
label_entry.pack(fill='both',expand=True)


def set_warning():
    label_entry.configure(
        text='Qualified personnel only', anchor='center',
        background=pastel_yellow, foreground='black')
    label_rads.configure(background=pastel_yellow, foreground='black')
    label_timestamp.configure(background=pastel_yellow, foreground='black')


def set_danger():
    label_entry.configure(
        text='Danger of ionizing radiation',
        background=pastel_red, foreground='black')
    label_rads.configure(background=pastel_red, foreground='black')
    label_timestamp.configure(background=pastel_red, foreground='black')


def set_safe():
    label_entry.configure(
        text='Safe to enter', anchor='center',
        background=pastel_green, foreground='black')
    label_rads.configure(background=pastel_green, foreground='black')
    label_timestamp.configure(background=pastel_green, foreground='black')


def update():
    label_timestamp.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        rads = float(requests.get(env_config.G64_url, timeout=2).json()['dosage_rate(uSv/h)'])
        if rads > 3.2:
            set_danger()
        elif rads > 1.2:
            set_warning()
        else:
            set_safe()
        label_rads.configure(text="Radiation level: {0:.5f} uSv/h".format(rads))
    except:
        set_danger()
        label_rads.configure(text="Failed to retrieve radiation level. Verify network connection")

    root.after(2000, update)


update()
root.mainloop()
