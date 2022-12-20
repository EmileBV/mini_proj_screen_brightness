import tkinter as tk
import screen_brightness_control as sbc
import time


def set_brightness(value):
    global out_slider
    global last_bright
    global last_input_time
    global is_input_refreshed
    out_slider.set(value)
    sbc.set_brightness(value)
    last_bright = value
    last_input_time = time.time()
    is_input_refreshed = False


def fuzz_update():
    global last_bright
    global out_slider
    global sim_slider
    global gui
    global last_input_time
    global is_input_refreshed

    # input from windows' screen brightness control
    cur_bright = sbc.get_brightness(display=0)[0]
    if cur_bright != last_bright:
        set_brightness(cur_bright)

    # input from app slider
    elif out_slider.get() != last_bright:
        cur_bright = out_slider.get()
        set_brightness(cur_bright)

    # when a new user input has been detected, update c-means
    if time.time() - last_input_time > 1.0 and not is_input_refreshed:
        # todo: use cur_bright to set a new truth entry in fuzzy controller
        print("update c-means!==========================")
        is_input_refreshed = True
    # else if user is not changing the value, use fuzzy controller
    elif is_input_refreshed:
        # todo: run normal fuzzy controller here
        print("fuzzy ctrl call")

    # tkinter refresh to call this function again
    gui.after(1, fuzz_update)


if __name__ == '__main__':
    last_bright = sbc.get_brightness(display=0)
    last_input_time = time.time()
    is_input_refreshed = True
    gui = tk.Tk()
    gui.resizable(False, False)
    gui.attributes("-toolwindow", 1)
    frame = tk.Frame(gui)
    frame.anchor(tk.NW)
    frame.pack()

    out_slider = tk.Scale(frame, from_=100, to=0, orient=tk.VERTICAL)
    out_slider.set(last_bright)
    out_slider.grid(row=0, column=0)
    tk.Label(frame, text="brightness").grid(row=1, column=0)

    sim_slider = tk.Scale(frame, from_=100, to=0, orient=tk.VERTICAL)
    sim_slider.set(50)
    sim_slider.grid(row=0, column=1)
    tk.Label(frame, text="sensor").grid(row=1, column=1)

    gui.after(1, fuzz_update)
    gui.mainloop()

