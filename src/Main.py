__author__ = "Colton Tshudy"
__version__ = "0.20"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Main file

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial_comms

sg.theme('DefaultNoMoreNagging')
sc = serial_comms.Communicator(baudrate=115200, generate_csv=False)

def IText(*args, **kwargs):
    return sg.Col([[sg.Text(*args, **kwargs)]], pad=(0,0))

plot_col = [
    [ 
        sg.Canvas(key = '-CANVAS-'),
    ],
    [ 
        sg.Button('Moving Window Time Scale', key='-PLOT_WINDOW-'),
        sg.Button('Full Time Scale', key='-PLOT_FULL-')
    ]
]

serial_connectivity_col = [
    [ 
        sg.Text('Connected!', key="-CON-", visible = False),
        sg.Text('Disconnected.', key='-DIS-', visible = False),
    ],
]

serial_col = [ 
    [ 
        sg.Text('Port Select'),
        sg.Combo(sc.listPorts(), default_value=sc.currentPort(), key='-PORT_SEL-', enable_events=True),
        sg.Col(serial_connectivity_col, pad=(0,0))
    ],
    [ 
        sg.Text('Serial Messages                                                     Serial Data')
    ],
    [ 
        sg.Multiline(size=(40,15), font='Tahoma 10', key='-STLINE-', autoscroll=False),
        sg.Multiline(size=(30,15), font='Tahoma 10', key='-RAWDATA-', autoscroll=False)
    ],
    [
        sg.Button('Start', key = '-PAUSE-'),
        sg.Button('Terminate', key='-TERMINATE-', button_color='red'),
        sg.Input(size=(25, 5000), enable_events=True, key="-COMMAND-"),
        sg.Button('Send', bind_return_key=True, key='-SEND-'),
        sg.Checkbox('Autoscroll', default=True, key='-AS-')
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
        x_min = xs[-1]-20
    plt.xlim(xmin = x_min)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack()

startup_msg = f'Serial connected? {not sc.isBusy()}'
window['-STLINE-'].print(startup_msg, autoscroll = auto_scroll)

while True:
    sc.checkSerial()

    #see if a serial message is available
    if sc.hasMessage():
        recieved = sc.readMessage()
        if sc.messageType() != '[':
            window['-STLINE-'].print(recieved, autoscroll = auto_scroll)
        else:
            window['-RAWDATA-'].print(recieved, autoscroll = auto_scroll)
            data = recieved[1:].split(",")
            volts = data[0]
            time = data[3]
            update_figure([time, volts])

    #check if command file is done
    if sc.reachedFileEnd() and not sc.isPaused():
        sc.pause()
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
        if sc.isPaused():
            sc.resume()
            window['-PAUSE-'].Update("Pause")
            window['-SEND-'].update(disabled=True)
            if sc.reachedFileEnd():
                sc.resetFile()
        else:
            sc.pause()
            window['-SEND-'].update(disabled=False)
            window['-PAUSE-'].Update("Unpause")

    #send
    elif event == '-SEND-':
        sc.sendCommand(values['-COMMAND-']);
        window['-COMMAND-']('')

    #terminate
    elif event == '-TERMINATE-':
        sc.terminate()
        window['-PAUSE-'].Update("Start")
        window['-STLINE-'].print("Terminated command file execution.", autoscroll = auto_scroll)

    #plot buttons
    elif event == '-PLOT_WINDOW-':
        fullgraph = False
        update_figure('')
    elif event == '-PLOT_FULL-':
        fullgraph = True
        update_figure('')

    #autoscroll
    if values['-AS-'] != auto_scroll:
        auto_scroll = values['-AS-']

    #port select
    if event == '-PORT_SEL-':
        new_port = values['-PORT_SEL-']
        sc.autoFindPort(new_port)
        window['-STLINE-'].print(f'Serial Port: {sc.currentPort()}', autoscroll = auto_scroll)
        if sc.isBusy():
            window['-CON-'].update(visible=False)
            window['-DIS-'].update(visible=True)
        else:
            window['-CON-'].update(visible=True)
            window['-DIS-'].update(visible=False)
        xs = [0]
        ys = [0]
        update_figure('')
