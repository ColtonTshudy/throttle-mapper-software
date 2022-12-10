__author__ = "Colton Tshudy"
__version__ = "0.42"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Spaghetti code to the extreme... sorry, this is my first Python project

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import DynoRunner as dr

sg.theme('DefaultNoMoreNagging')

plot_col = [
    [ 
        sg.Push(),
        sg.Checkbox('Full Time Scale', enable_events=True, key='-PLOT_FULL-'),
    ],
    [ 
        sg.Canvas(key = '-CANVAS-'),
    ],
    [
        sg.Push(),
        sg.Slider(orientation ='horizontal', key='-TIME_SLIDER-', range=(10,100), enable_events=True),
    ],
]

serial_col = [ 
    [ 
        sg.Text('Serial Messages                                                   Serial Data')
    ],
    [ 
        sg.Multiline(size=(40,15), font='Tahoma 10', key='-STLINE-', autoscroll=False),
        sg.Multiline(size=(30,15), font='Tahoma 10', key='-RAWDATA-', autoscroll=False),
    ],
    [
        sg.Button('Start', key = '-PAUSE-'),
        sg.Button('Terminate', key='-TERMINATE-', button_color='red'),
        sg.Input(size=(25, 5000), enable_events=True, key="-COMMAND-"),
        sg.Button('Send', bind_return_key=True, key='-SEND-'),
        sg.Checkbox('Autoscroll', default=True, key='-AS-', enable_events=True),
    ],
    [
        sg.Text('Notice: pause only pauses after the current command is complete.')
    ],
]

layout = [
    [ 
        sg.Column(plot_col),
        sg.VSeperator(),
        sg.Column(serial_col),
    ]
]

titlebar = ''.join(["DynoRunner ver. ", __version__])

window = sg.Window(titlebar,
                layout,
                default_element_size=(12, 1),
                resizable=True,finalize=True)

#initial state of window
window['-TIME_SLIDER-'].update(value = 20)

#matplotlib
fig = plt.figure(figsize = (6,4))
fig.add_subplot(1,1,1).plot([],[])
figure_canvas_agg = FigureCanvasTkAgg(fig,window['-CANVAS-'].TKCanvas)
figure_canvas_agg.draw()
figure_canvas_agg.get_tk_widget().pack()
plt.title('Throttle Voltage', fontsize = 10)
plt.ylabel('Voltage (v)')
plt.xlabel('Time (s)')
plt.gca().set_ylim(ymin=0, ymax=5)
plt.grid(linestyle=':')
xs = [0]
ys = [0]

# variables
paused = True
command = False
terminate = False
auto_scroll = True
restart = False
fullgraph = False
x_min = 0
time_scale = 20

def update_figure(data):
    axes = fig.axes
    axes[0].clear()
    if len(data) == 2:
        xs.append(float(data[0])/1000)
        ys.append(float(data[1]))
    axes[0].plot(xs,ys,'-b')
    plt.title('Throttle Voltage', fontsize = 10)
    plt.ylabel('Voltage (v)')
    plt.xlabel('Time (s)')
    plt.gca().set_ylim(ymin=0, ymax=5)
    plt.grid(linestyle=':')
    if fullgraph:
        x_min = 0
    else:
        x_min = xs[-1]-time_scale
    plt.xlim(xmin = x_min)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack()

while True:
    try:
        serial_r = dr.checkSerial(paused, command, terminate, restart)

        #reset any button variables
        command = False
        terminate = False
        restart = False

        #see if checkSerial returned data
        if serial_r != False:
            if serial_r[0] != '[':
                window['-STLINE-'].print(serial_r[1], autoscroll = auto_scroll)
            else:
                window['-RAWDATA-'].print(serial_r[1], autoscroll = auto_scroll)
            if serial_r[2] != False:
                volts = serial_r[2][0]
                time = serial_r[2][3]
                update_figure([time, volts])

        #check if command file is done
        if dr.endOfFile() and not paused:
            paused = True
            window['-SEND-'].update(disabled=False)
            window['-PAUSE-'].Update("Start")
            window['-STLINE-'].print("Reached end of command file.", autoscroll = auto_scroll)

        #get gui window events
        event, values = window.read(timeout = 1) #1ms timeout

        #exit
        if event == 'Exit' or event == sg.WIN_CLOSED:
                break

        #pause
        elif event == '-PAUSE-':
            if paused:
                paused = False
                window['-PAUSE-'].Update("Pause")
                window['-SEND-'].update(disabled=True)
                if dr.endOfFile():
                    restart = True
            else:
                paused = True
                window['-SEND-'].update(disabled=False)
                window['-PAUSE-'].Update("Unpause")

        #send
        elif event == '-SEND-':
            command = values['-COMMAND-'];
            window['-COMMAND-']('')

        #terminate
        elif event == '-TERMINATE-':
            terminate = True
            paused = True
            window['-PAUSE-'].Update("Start")
            window['-STLINE-'].print("Terminated command file execution.", autoscroll = auto_scroll)

        #plot buttons
        elif event == '-PLOT_FULL-':
            window['-TIME_SLIDER-'].update(visible=not values['-PLOT_FULL-'])
            fullgraph = values['-PLOT_FULL-']
            update_figure('')

        #graph time scale
        if event == '-TIME_SLIDER-':
            time_scale = values['-TIME_SLIDER-']
            update_figure('')

        #autoscroll
        if event == '-AS-':
            auto_scroll = values['-AS-']
        
    except KeyboardInterrupt:
        dr.closeRunner()
        window.close()