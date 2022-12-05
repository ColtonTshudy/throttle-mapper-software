__author__ = "Colton Tshudy"
__version__ = "0.1"
__email__ = "coltont@vt.edu"
__status__ = "Prototyping"

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import DynoRunner as ac

sg.theme('DefaultNoMoreNagging')

layout = [
    [ 
        sg.Text('Throttle% Over Time'),
    ],
    [ 
        sg.Canvas(key = '-CANVAS-')
    ],
    [ 
        sg.Text('Serial Readout')
    ],
    [
        sg.Button('Start'),
        sg.Button('Terminate'),
        sg.Input(size=(25, 5000), enable_events=True, key="-COMMAND-"),
        sg.Button('Send', bind_return_key=True),
    ],
]

window = sg.Window('Window Title',
                layout,
                default_element_size=(12, 1),
                resizable=True,finalize=True)

#matplotlib
fig = plt.figure(figsize = (5,3))
fig.add_subplot(111).plot([],[])
figure_canvas_agg = FigureCanvasTkAgg(fig,window['-CANVAS-'].TKCanvas)
figure_canvas_agg.draw()
figure_canvas_agg.get_tk_widget().pack()

while True:
    try:
        event, values = window.read()
        if event == 'Exit' or event == sg.WIN_CLOSED:
                break
        elif event == 'Send':
            print(values['-COMMAND-'])
            window['-COMMAND-']('')
        
    except KeyboardInterrupt:
        window.close()

def update_figure(data):
    axes = fig.axes
    x = [int(i[0])/1000 for i in data]
    y = [int(i[1]) for i in data]
    axes[0].plot(x,y,'b-')
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack()