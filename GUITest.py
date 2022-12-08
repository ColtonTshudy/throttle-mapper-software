__author__ = "Colton Tshudy"
__version__ = "0.20"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import DynoRunner as dr

sg.theme('DefaultNoMoreNagging')

matplotlib_col = [
    [ 
        sg.Canvas(key = '-CANVAS-')
    ],
]

serial_col = [ 
    [ 
        sg.Text('Serial Readout')
    ],
    [ 
        sg.Multiline(size=(70,10), font='Tahoma 10', key='-STLINE-', autoscroll=True)
    ],
    [
        sg.Button('Start', key = '-PAUSE-'),
        sg.Button('Terminate'),
        sg.Input(size=(25, 5000), enable_events=True, key="-COMMAND-"),
        sg.Button('Send', bind_return_key=True),
    ],
]

layout = [
    [ 
        sg.Column(matplotlib_col),
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

# variables
paused = True

def update_figure(data):
    axes = fig.axes
    x = float(data[0])/1000
    y = float(data[1])
    axes[0].plot(x,y,'bo')
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack()

while True:
    try:
        serial_r = dr.checkSerial(paused)
        if serial_r != False:
            window['-STLINE-'].print(serial_r[1],)
            if(serial_r[2] != False):
                volts = serial_r[2][0]
                time = serial_r[2][3]
                update_figure([time, volts])

        event, values = window.read(timeout = 1) #1ms timeout
        if event == 'Exit' or event == sg.WIN_CLOSED:
                break
        elif event == 'Send':
            print(values['-COMMAND-'])
            window['-COMMAND-']('')
        elif event == '-PAUSE-':
            if paused:
                paused = False
                window['-PAUSE-'].Update("Pause")
            else:
                paused = True
                window['-PAUSE-'].Update("Unpause")            
        
    except KeyboardInterrupt:
        dr.closeRunner()
        window.close()