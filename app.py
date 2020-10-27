import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import json
from plotconfigs import *
from dash.dependencies import Output, Input

import matplotlib
from datetime import datetime, timedelta, date
import os
from glob import glob
import numpy as np

parameters = {
    '3-hr precipitation': 'qpf_03h',
    '6-hr precipitation': 'qpf_06h',
    '12-hr precipitation': 'qpf_12h',
    'Total snow depth': 'snod_total',
}

variable_types = {
    'LPMM': 'lpmm',
    'Max': 'max',
    'Spaghetti': 'sp'
}

thresholds = {
    '3-hr precipitation': [0.10, 0.25, 0.50],
    '6-hr precipitation': [0.10, 0.25, 0.50],
    '12-hr precipitation': [0.10, 0.25, 0.50],
    'Total snow depth': [1,3,6,9,12]
}

def get_info(feature=None):
    header = [html.H4("Current Sample Value")]
    if not feature:
        return header
    return header + [html.H6(feature["properties"]["title"])]

def get_available_hours(date):
    subfolders = sorted(glob(JSON_DIR + '/' + str(date) + '/*/'))

    hours = []
    for folder in subfolders:
        HH = folder[-3:-1]
        hours.append(dict(label=HH, value=int(HH)))
    return hours

def get_available_cyles():
    # Add a check for the directory file size here...
    dirs = sorted(glob(JSON_DIR + '/*/'))
    date_times = []
    for folder in dirs:
        subfolders = sorted([f.path for f in os.scandir(folder) if f.is_dir()])
        for target in subfolders:
            datestring = target[-13:]
            date_times.append(datetime.strptime(datestring, '%Y-%m-%d/%H'))
    return date_times

def get_valid_time(cycle_str, fhr):
    dt = datetime.strptime(cycle_str, '%Y-%m-%d/%H') + timedelta(hours=int(fhr))
    valid_time_string = dt.strftime('%Y-%m-%d/%H')
    return valid_time_string

def get_minmax(classes):
    return dict(min=min(classes), max=max(classes))

def get_data(cycle_str, fhr, parm, var_type, levels, threshold=None):
    c = []
    fname = "%s/%s/%s_%s.f%s" % (JSON_DIR, cycle_str, parm, var_type, str(fhr))
    if threshold:
        fname = "%s/%s/%s_%s_%s.f%s" % (JSON_DIR, cycle_str, parm, var_type, threshold,
                                        str(fhr))
    with open(fname, 'r') as f: df = json.load(f)

    # We could probably move these calculations into the create_geojson.py script to
    # avoid having to do this here...
    if not threshold:
        knt = 1
        for feature in df['features']:
            feature['properties']['values'] = levels[knt]
            knt += 1
    return df

info = html.Div(children=get_info(), id="info", className="info",
                style={"position": "absolute", "top": "10px", "right": "10px",
                       "z-index": "1000", 'color': '#000000'})

# ...
# Date and latest model cycle
# ...
current_time = datetime.utcnow()
model_cycles = get_available_cyles()
delta = current_time - model_cycles[-1]
warn_str = "***WARNING: Latest available cycle is over %s hours old!***"
old_data_warn = ""
no_cycle_warn = ""
if delta > timedelta(hours=12):
    n_hours = int((delta.total_seconds() / 3600.))
    old_data_warn = warn_str % (n_hours)

# ...
# Set the initial color configurations
# ...
#c = []
classes = qpf_levs
colorscale = qpf_cols
minmax = get_minmax(classes)
cycle_string = model_cycles[-1].strftime('%Y-%m-%d/%H')
#c = get_data(cycle_string, 3, 'qpf_03h', 'lpmm', classes)

c = dl.GeoJSON(data=get_data(cycle_string, 3, 'qpf_03h', 'lpmm', classes),
               options=dict(style="window.local.module.set_style", weight=1,
                            fillOpacity=0.45),
               hideout=dict(colorscale=colorscale, classes=classes,
                            color_prop="values"),
               hoverStyle=dict(weight=2, opacity=0.7, color='Black'),
               id='contourf')

# Create colorbar
ctg = ["{}".format(cls, classes[i+1]) for i, cls in enumerate(classes[:-1])] \
       + ["{}+".format(classes[-1])]
indices = list(range(len(ctg)))
cbar = dl.Colorbar(min=0, max=len(ctg), tickValues=[item+0.5 for item in indices],
                   tickText=ctg, classes=indices, colorscale=colorscale, width=25,
                   height=700, position="bottomleft", id="cbar")

#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#app = dash.Dash(__name__, prevent_initial_callbacks=True)
#app.css.append_css({'external_url': '/assets/style.css'})
mapbox_url = "https://api.mapbox.com/styles/v1/lcarlaw/ckgr1b7gx2wrq19pcum3lodh8/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoibGNhcmxhdyIsImEiOiJja2drMWM5dm0yMGZkMnFsN3NlNHZseGNmIn0.CKrzXaLRaDJ6ggGZT2eWFg"
mapbox_token = "pk.eyJ1IjoibGNhcmxhdyIsImEiOiJja2drMWM5dm0yMGZkMnFsN3NlNHZseGNmIn0.CKrzXaLRaDJ6ggGZT2eWFg"


#mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{{z}}/{{x}}/{{y}}{{r}}?access_token={access_token}"
#mapbox_token = settings.MAPBOX_TOKEN
#mapbox_ids = ["light-v9", "dark-v9", "streets-v9", "outdoors-v9", "satellite-streets-v9"]
app = dash.Dash(__name__, external_stylesheets=['/assets/style.css'])
app.layout = html.Div(
    [
        html.Div(
            [
                html.H3("GEFSv12 Ensemble Viewer"),
                html.Div(
                    html.Center(
                        [
                            old_data_warn
                        ]
                    ),
                style={'color': 'red', 'fontSize': 25}
                ),

                html.Div([],
                style={'height': '10px'},
                ),

                dcc.Slider(
                    id='fhr',
                    min=3,
                    max=120,
                    value=3,
                    marks={str(fhr): str(fhr) for fhr in np.arange(3,123,3)},
                    step=None
                ),

                dl.Map(center=[42, -88], zoom=6, children=[dl.TileLayer(url=mapbox_url), info, cbar, c],
                style={'width': '100%', 'height': '850px', 'margin': "auto", "display": "block"}),
            ],
            style={'width': '83%', 'height': '100vh', 'display': 'inline-block'},
        ),

        html.Div(
            [
                html.Div(
                    html.Center(
                        [
                            html.Td(
                                id="no-cycle-warn"
                            )
                        ]
                    ),
                style={'color': 'red', 'fontSize': 15, 'font-weight': 'bold'}
                ),

                # Hidden div inside app to store intermediate value
                html.Div(
                    id='hidden-value', style={'display': 'none'}
                ),

                html.Table(
                    [
                        html.Tr(
                            [
                                html.Th("Model Cycle"),
                                html.Th("Hour"),
                                html.Th("Valid Time"),
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td(
                                    id="selected-date"
                                ),
                                html.Td(
                                    id='selected-hour'
                                ),
                                html.Td(
                                    id='valid-time'
                                )
                            ]
                        )
                    ],
                style={'margin-left': '5%', 'border-bottom': '2px solid #E1E1E1', 'width': '90%'}
                ),

                html.Div([],
                style={'height': '10px'},
                ),

                html.H6("Model Cycle Selection"),
                html.Table(
                    [
                        html.Tr(
                            [
                                html.Th('Cycle Date'),
                                html.Th('Hour')
                            ]
                        ),
                        html.Tr(
                            [
                                html.Td(children=[
                                    dcc.DatePickerSingle(
                                        id='date-selection',
                                        min_date_allowed=model_cycles[0].date(),
                                        max_date_allowed=model_cycles[-1].date(),
                                        initial_visible_month=model_cycles[-1].date(),
                                        date=model_cycles[-1].date()
                                    ),
                                ]
                                ),
                                html.Td(
                                    dcc.Dropdown(
                                        id='hour-selection',
                                        options=get_available_hours(model_cycles[-1].date()),
                                        placeholder=str(model_cycles[-1].hour).zfill(2),
                                        value=str(model_cycles[-1].hour).zfill(2)
                                    ),
                                style={'color': '#000000'}
                                )
                            ]
                        ),
                    html.Tr([])
                    ],
                    style={'margin-left': '5%', 'width': '90%'}
                ),

                html.Div([],
                style={'height': '10px'},
                ),

                html.Div(
                    [
                        html.H6("Parameter Selection"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id='parm-selection',
                                    options=[{'label': i, 'value': i} for i in parameters.keys()],
                                    value=list(parameters.keys())[0]
                                ),
                            ],
                            style={'margin-left': '5%', 'width': '90%', 'color': '#000000'},
                        ),

                        html.Div([],
                        style={'height': '10px'},
                        ),

                        html.H6("Variable Selection"),
                        html.Div(
                            [
                                dcc.RadioItems(
                                    id='var-type',
                                    options=[{'label': i, 'value': i} for i in variable_types.keys()],
                                    value=list(variable_types.keys())[0]
                                ),
                            ],
                            style={'margin-left': '5%','width': '90%'},
                        ),

                        html.Div([],
                        style={'height': '10px'},
                        ),

                        # Default to
                        html.H6("Threshold Selection"),
                        html.Div(
                            [
                                dcc.Dropdown(
                                    id='threshold-selection',
                                    options=[{'label': i, 'value': i} for i in thresholds[list(parameters.keys())[0]]],
                                    value=thresholds[list(parameters.keys())[0]][0]
                                ),
                            ],
                            style={'margin-left': '5%', 'width': '90%', 'color': '#000000'},
                        ),
                    ],
                ),
            ],
            style={'width': '16.5%', 'height': '100vh', 'float': 'right',
                   'display': 'inline-block', 'background-color':'#1d1d1d'},
        ),
    ]
)

# For the sampling output
@app.callback(Output("info", "children"), [Input("contourf", "hover_feature")])
def info_hover(feature):
    return get_info(feature)

# For the cycle selection
# For any user-selected date, this callback will query the available cycle hours using
# get_available_hours and additionally update the Hour dropdown menu. We don't want a
# user to select a date and then see an error that model data doesn't exist.
@app.callback(
    [Output('selected-date', 'children'),
     Output('hour-selection', 'options'),
     Output('hour-selection', 'placeholder'),
     Output('hour-selection', 'value'),
     Output('no-cycle-warn', 'children')],
    [Input('date-selection', 'date')])
def update_date(date_value):
    date_object = date.fromisoformat(date_value)
    date_string = date_object.strftime('%Y-%m-%d')
    hours = get_available_hours(date_object)

    # No cycles available for this date. Apply warning to the top of the app. Instead of
    # throwing a visible error now,
    if len(hours) < 1:
        no_cycle_warn = "No cycles available for: %s" % (date_string)
        hours = get_available_hours(model_cycles[-1].date())
        latest_available = hours[-1]['label']
        date_string = str(model_cycles[-1].date())

    # Good to go. Update with the selected date, and default to the most recent hour.
    else:
        latest_available = hours[-1]['label']
        no_cycle_warn = ""
    return date_string, hours, latest_available, latest_available, no_cycle_warn

# Update the cycle hour in the top display table
@app.callback(
    Output('selected-hour', 'children'),
    [Input('hour-selection', 'value')])
def update_hour(hour_value):
    return str(hour_value).zfill(2)

'''
@app.callback(Output('individual-member-selection', 'value'),
                [Input('var-type', 'value')])
def individual_members(selection):
    members = [{'label': i, 'value': i} for i in perts]
    print(members)
    return members[0]
'''

# Updating the figure
@app.callback([Output("contourf", "data"),
               Output("contourf", "hideout"),
               Output("contourf", "options"),
               Output("cbar", "max"),
               Output("cbar", "tickValues"),
               Output("cbar", "tickText"),
               Output("cbar", "classes"),
               Output("cbar", "colorscale"),
               Output("valid-time", "children")],
              [Input("fhr", "value"),
               Input("parm-selection", "value"),
               Input("var-type", "value"),
               Input("threshold-selection", "value"),
               Input('date-selection', 'date'),
               Input('hour-selection', 'value')])
def update(fhr, parm_selection, var_selection, threshold, date, hour):
    cycle_str = date + '/' + str(hour).zfill(2)
    valid_time = get_valid_time(cycle_str, fhr)
    parm = parameters[parm_selection]
    var_type = variable_types[var_selection]

    # From the parameter request, set the color table and scale
    if parm in ['qpf_03h', 'qpf_06h', 'qpf_12h']:
        classes = qpf_levs
        colorscale = qpf_cols

    elif parm in ['snod_total']:
        classes = snow_levs
        colorscale = snow_cols

    if var_type == 'sp':
        colorscale = []
        for color in spag_cols:
            colorscale.append(matplotlib.colors.to_hex(list(color[0:3])))
        classes = spag_levs
        data = get_data(cycle_str, fhr, parm, var_type, classes, threshold=threshold)
        hideout = dict(colorscale=colorscale, classes=classes, color_prop="values"),
        ctg = ["{}".format(cls, classes[i+1]) for i, cls in enumerate(classes[:-1])] \
               + ["{}+".format(classes[-1])]
        indices = list(range(len(ctg)))
        options = dict(style="window.local.module.set_style", weight=1,
                       fillOpacity=0.025)
        #options = dict(fill=False)
    else:
        data = get_data(cycle_str, fhr, parm, var_type, classes)
        minmax = get_minmax(classes)
        hideout = dict(colorscale=colorscale, classes=classes, color_prop="values"),

        ctg = ["{}".format(cls, classes[i+1]) for i, cls in enumerate(classes[:-1])] \
               + ["{}+".format(classes[-1])]
        indices = list(range(len(ctg)))
        options = dict(style="window.local.module.set_style", weight=1, fillOpacity=0.45)

    return data, hideout, options, len(ctg), indices, ctg, indices, colorscale, valid_time


if __name__ == '__main__':
    app.run_server(debug=True)
