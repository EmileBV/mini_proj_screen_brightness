import tkinter as tk
import screen_brightness_control as sbc
import time
import cv2
import numpy as np


def get_estimated_lux():
    global camera
    _, image = camera.read()
    is_valid, img_data = camera.retrieve(image=image)
    if is_valid:
        pixel_count = len(img_data) * len(img_data[0])
        avg_rgb = np.sum(np.concatenate(img_data), axis=0) / pixel_count
        lux = (avg_rgb[0] * .229) + (avg_rgb[1] * .587) + (avg_rgb[2] * .114)
        return lux
    else:
        return -1


def get_percent_lux():
    global sensor_avg
    lux_max = 140
    sample_count = 10
    lux = get_estimated_lux()
    if lux == -1:
        return -1
    else:
        # moving average
        sensor_avg = ((sensor_avg * (sample_count - 1)) + lux) / sample_count
        return (min(lux_max, max(0, sensor_avg)) / lux_max) * 100


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
    global use_real_sensor

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
        sensor_value = 0
        if use_real_sensor.get() == 1:
            sensor_value = get_percent_lux()
        else:
            sensor_value = sim_slider.get()
        print(f"fuzzy ctrl call with sensor = {sensor_value}%")

    # tkinter refresh to call this function again
    gui.after(1, fuzz_update)


if __name__ == '__main__':
    last_bright = sbc.get_brightness(display=0)
    last_input_time = time.time()
    is_input_refreshed = True
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    sensor_avg = 0

    # create main window
    gui = tk.Tk()
    gui.resizable(False, False)
    gui.attributes("-toolwindow", 1)
    frame = tk.Frame(gui)
    frame.anchor(tk.NW)
    frame.pack()

    # create brightness slider
    out_slider = tk.Scale(frame, from_=100, to=0, orient=tk.VERTICAL)
    out_slider.set(last_bright)
    out_slider.grid(row=0, column=0)
    tk.Label(frame, text="brightness").grid(row=1, column=0)

    # create input value slider
    sim_slider = tk.Scale(frame, from_=100, to=0, orient=tk.VERTICAL)
    sim_slider.set(50)
    sim_slider.grid(row=0, column=1)
    tk.Label(frame, text="sensor").grid(row=1, column=1)

    use_real_sensor = tk.Scale(frame, from_=0, to=1, orient=tk.HORIZONTAL)
    use_real_sensor.grid(row=2, column=1)
    tk.Label(frame, text="use webcam").grid(row=3, column=1)

    # run UI and update function
    gui.after(1, fuzz_update)
    gui.mainloop()
    camera.release()

