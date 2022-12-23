import tkinter as tk
import screen_brightness_control as sbc
import time
import cv2
import numpy as np
from skfuzzy import control as ctrl
import skfuzzy

import random

def control_init():
    if control_init.first_run:
        max = 120
        br_input  = ctrl.Antecedent(np.arange(0,max,1), 'input')
        br_forced = ctrl.Antecedent(np.arange(-10,10,1), 'forced')
        br_output = ctrl.Consequent(np.arange(0,max,1), 'output')

        br_input.automf(7)  # [dismal, poor, mediocre, average, decent, good, excellent]
        if len(center_list) < 3 :
            br_forced['poor'] = skfuzzy.trimf(br_forced.universe, [-10, -10, 0])
            br_forced['average'] = skfuzzy.trimf(br_forced.universe, [-5, 0, 5])
            br_forced['good'] = skfuzzy.trimf(br_forced.universe, [0, 10, 10])
        else:
            br_forced['poor'] = skfuzzy.trimf(br_forced.universe, [-10, sorted(center_list)[0], sorted(center_list)[0]+5])
            br_forced['average'] = skfuzzy.trimf(br_forced.universe, [sorted(center_list)[1]-5, sorted(center_list)[1], sorted(center_list)[1]+5])
            br_forced['good'] = skfuzzy.trimf(br_forced.universe, [sorted(center_list)[2]-5, sorted(center_list)[2], 10])
        #br_forced.automf(3) # [poor, average, good] or switch to c-means?
        br_output.automf(7) # [dismal, poor, mediocre, average, decent, good, excellent]

        br_forced.view()
        br_input.view()
        br_output.view()

        # todo: rules
        rule1   = ctrl.Rule(br_input['dismal'] & br_forced['poor'], br_output['dismal'])
        rule2   = ctrl.Rule(br_input['poor'] & br_forced['poor'], br_output['dismal'])
        rule3   = ctrl.Rule(br_input['mediocre'] & br_forced['poor'], br_output['poor'])
        rule4   = ctrl.Rule(br_input['average'] & br_forced['poor'], br_output['mediocre'])
        rule5   = ctrl.Rule(br_input['decent'] & br_forced['poor'], br_output['average'])
        rule6   = ctrl.Rule(br_input['good'] & br_forced['poor'], br_output['decent'])
        rule7   = ctrl.Rule(br_input['excellent'] & br_forced['poor'], br_output['good'])

        rule11   = ctrl.Rule(br_input['dismal'] & br_forced['average'], br_output['dismal'])
        rule12   = ctrl.Rule(br_input['poor'] & br_forced['average'], br_output['poor'])
        rule13   = ctrl.Rule(br_input['mediocre'] & br_forced['average'], br_output['mediocre'])
        rule14   = ctrl.Rule(br_input['average'] & br_forced['average'], br_output['average'])
        rule15   = ctrl.Rule(br_input['decent'] & br_forced['average'], br_output['decent'])
        rule16   = ctrl.Rule(br_input['good'] & br_forced['average'], br_output['good'])
        rule17   = ctrl.Rule(br_input['excellent'] & br_forced['average'], br_output['excellent'])

        rule21   = ctrl.Rule(br_input['dismal'] & br_forced['good'], br_output['poor'])
        rule22   = ctrl.Rule(br_input['poor'] & br_forced['good'], br_output['mediocre'])
        rule23   = ctrl.Rule(br_input['mediocre'] & br_forced['good'], br_output['average'])
        rule24   = ctrl.Rule(br_input['average'] & br_forced['good'], br_output['decent'])
        rule25   = ctrl.Rule(br_input['decent'] & br_forced['good'], br_output['good'])
        rule26   = ctrl.Rule(br_input['good'] & br_forced['good'], br_output['excellent'])
        rule27   = ctrl.Rule(br_input['excellent'] & br_forced['good'], br_output['excellent'])

        
        br_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7,
                                      rule11, rule12, rule13, rule14, rule15, rule16, rule17,
                                      rule21, rule22, rule23, rule24, rule25, rule26, rule27])
        control_init.br_var = ctrl.ControlSystemSimulation(br_ctrl)
        control_init.first_run = False

    return control_init.br_var

def cmeans():
    global center_list
    a1D = np.array(cmeans_list)
    
    a2D=np.vstack((a1D,np.zeros(len(cmeans_list))))
    #print(a2D)
    cntr, u_orig, _, _, _, _, _ = skfuzzy.cluster.cmeans(a2D, 3, 2, error=0.005, maxiter=1000)
    for pt in cntr:
        center_list.append(pt[0])
    return center_list


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
    lux_max = 200
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
    global last_slider_value
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
    global cmeans_list
    global fuzz
    global override_val

    fuzz = control_init()
    # input from windows' screen brightness control
    cur_bright = sbc.get_brightness(display=0)[0]
    if cur_bright != last_bright:
        set_brightness(cur_bright)
        
    # input from app slider
    elif out_slider.get() != last_bright:
        out_slider_time = time.time()
        cur_bright = out_slider.get()
        set_brightness(cur_bright)

    
    # when a new user input has been detected, update c-means
    if time.time() - last_input_time > 1.0 and not is_input_refreshed:
        # todo: use cur_bright to set a new truth entry in fuzzy controller
        #print("values = {} and {}".format(cur_bright, last_bright))
        '''
        if override_val :
            prendre la paire de data
        else :
            override_val = 0
        '''
        override_val = random.randrange(-10,10,1)
        cmeans_list.append(override_val)
        print("update c-means!==========================")
        #print(cmeans_list)
        centers = cmeans()
        is_input_refreshed = True
    # else if user is not changing the value, use fuzzy controller
    elif is_input_refreshed:
        '''
        todo: run normal fuzzy controller here
        '''
        sensor_value = 0
        if use_real_sensor.get() == 1:
            sensor_value = get_percent_lux()
        else:
            sensor_value = sim_slider.get()

        fuzz.input['input'] = sensor_value
        fuzz.input['forced'] = override_val
        print(sensor_value, override_val)
        fuzz.compute()
        print(fuzz.output['output'])
        print("-----")
        #print(f"fuzzy ctrl call with sensor = {sensor_value}%")

    # tkinter refresh to call this function again
    gui.after(1, fuzz_update)


if __name__ == '__main__':
    last_bright = sbc.get_brightness(display=0)
    last_input_time = time.time()
    cmeans_list = []
    center_list = []
    override_val = 0
    is_input_refreshed = True
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    sensor_avg = 0

    control_init.first_run = True

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

