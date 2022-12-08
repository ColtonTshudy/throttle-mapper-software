__author__ = "Colton Tshudy"
__version__ = "0.3"
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
        sg.Canvas(key = '-CANVAS-')
    ],
]

serial_col = [ 
    [ 
        sg.Text('Serial Readout')
    ],
    [ 
        sg.Multiline(size=(70,10), font='Tahoma 10', key='-STLINE-', autoscroll=False)
    ],
    [
        sg.Button('Start', key = '-PAUSE-'),
        sg.Button('Terminate', key='-TERMINATE-'),
        sg.Input(size=(25, 5000), enable_events=True, key="-COMMAND-"),
        sg.Button('Send', bind_return_key=True, key='-SEND-'),
        sg.Checkbox('Autoscroll', default=True, key='-AS-')
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
xs = []
ys = []

# variables
paused = True
command = False
terminate = False
auto_scroll = True
restart = False

def update_figure(data):
    axes = fig.axes
    axes[0].clear()
    xs.append(float(data[0])/1000)
    ys.append(float(data[1]))
    axes[0].plot(xs,ys,'-b')
    plt.title('Throttle Voltage', fontsize = 10)
    plt.ylabel('Voltage (v)')
    plt.xlabel('Time (s)')
    plt.gca().set_ylim(ymin=0, ymax=5)
    plt.grid(linestyle=':')
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
            window['-STLINE-'].print(serial_r[1])
            if serial_r[2] != False:
                volts = serial_r[2][0]
                time = serial_r[2][3]
                update_figure([time, volts])

        #check if command file is done
        if dr.endOfFile() and not paused:
            paused = True
            window['-PAUSE-'].Update("Start")
            window['-STLINE-'].print("Reached end of command file.")

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
                if dr.endOfFile():
                    restart = True
            else:
                paused = True
                window['-PAUSE-'].Update("Unpause")

        #send
        elif event == '-SEND-':
            command = values['-COMMAND-'];
            window['-COMMAND-']('')

        #terminate
        elif event == '-TERMINATE-':
            terminate = True

        #autoscroll
        if values['-AS-'] != auto_scroll:
            auto_scroll = values['-AS-']
            window['-STLINE-'].Update(autoscroll=auto_scroll)

        
        
    except KeyboardInterrupt:
        dr.closeRunner()
        window.close()