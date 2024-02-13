__author__ = "Colton Tshudy"
__version__ = "0.3"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

#Main file

#======================================
# CONFIGURATION
__baudrate__ = 115200
__save_to_csv__ = True
#======================================

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial_comms

sg.theme('DefaultNoMoreNagging')
sc = serial_comms.Communicator(baudrate=__baudrate__, generate_csv=__save_to_csv__)
print(sc.currentPort())

def IText(*args, **kwargs):
    return sg.Col([[sg.Text(*args, **kwargs)]], pad=(0,0))

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

serial_connectivity_col = [
    [ 
        sg.Text('Connected!', key="-CON-", visible = False),
        sg.Text('Disconnected.', key='-DIS-', visible = False),
    ],
]

serial_col = [ 
    [ 
        sg.Text('Command File'),
        sg.In(size=(45, 10), enable_events=True, key="-FILE_SEL-"),
        sg.FileBrowse(file_types=(("TXT Files", "*.txt"), ("ALL Files", "*.*"))),
        sg.Button('Open', key='-OPEN-'),
    ],
    [ 
        sg.HSeparator(pad=(20,20))
    ],
    [ 
        sg.Text('Port Select'),
        sg.Combo(sc.listPorts(), key='-PORT_SEL-', enable_events=True),
        sg.Col(serial_connectivity_col, pad=(0,0)),
        sg.Button('Auto', key='-AUTO-'),
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

#window initial states
window['-TIME_SLIDER-'].update(value = 20)
window.write_event_value('-AUTO-', value=True)

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
        sc.reset()
        window['-SEND-'].update(disabled=False)
        window['-PAUSE-'].Update("Start")
        window['-STLINE-'].print("Reached end of command file.", autoscroll = auto_scroll)

    #get gui window events
    event, values = window.read(timeout = 1) #1ms timeout

    #exit
    if event == 'Exit' or event == sg.WIN_CLOSED:
        sc.close()
        break

    #pause
    elif event == '-PAUSE-':
        if sc.isPaused():
            if sc._fileisopen:
                sc.resume()
                window['-PAUSE-'].Update("Pause")
                window['-SEND-'].update(disabled=True)
                if sc.reachedFileEnd():
                    sc.restartFile()
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
    elif event == '-PLOT_FULL-':
        window['-TIME_SLIDER-'].update(visible=not values['-PLOT_FULL-'])
        fullgraph = values['-PLOT_FULL-']
        update_figure('')

    #graph time scale
    if event == '-TIME_SLIDER-':
        time_scale = values['-TIME_SLIDER-']
        update_figure('')

    #autoscroll
    if values['-AS-'] != auto_scroll:
        auto_scroll = values['-AS-']

    #port select
    if event == '-PORT_SEL-' or event == '-AUTO-':
        if event == '-PORT_SEL-':
            new_port = values['-PORT_SEL-']
            port_updated = sc.autoFindPort(new_port)
        else:
            port_updated = sc.autoFindPort()
            window['-PORT_SEL-'].update(value = sc.currentPort())
        
        if port_updated:
            if sc.isBusy():
                window['-CON-'].update(visible=False)
                window['-DIS-'].update(visible=True)
            else:
                window['-CON-'].update(visible=True)
                window['-DIS-'].update(visible=False)
            window['-STLINE-'].update(value='')
            window['-RAWDATA-'].update(value='')
            xs = [0]
            ys = [0]
            update_figure('')
            if not sc.isPaused():
                window.write_event_value('-TERMINATE-', value=True)          
                sc.pause()

    #file select
    if event == '-OPEN-':
        window.write_event_value('-TERMINATE-', value=True)
        if not sc.isPaused():     
            sc.pause()
        if sc.openCommandFile(values['-FILE_SEL-']):
            window['-STLINE-'].print("Opened file, press Start to begin.", autoscroll = auto_scroll)