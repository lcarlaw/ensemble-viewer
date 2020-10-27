import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import dash_leaflet.express as dlx
import json
import geopandas as gpd
from plotconfigs import *
from dash.dependencies import Output, Input

from datetime import datetime, timedelta, date
import os
from glob import glob


parameters = {
    '3-hr precipitation': 'qpf_03h',
    '6-hr precipitation': 'qpf_06h',
    '12-hr precipitation': 'qpf_12h',
    'Total snow depth': 'snod_total',
}

variable_types = {
    'LPMM': 'lpmm',
    'Max': 'max',
}

def get_info(feature=None):
    header = [html.H4("Current Sample Value")]
    if not feature:
        return header
    return header + [html.H6(feature["properties"]["title"])]

'''
c = []
for pert in range(4):
    with open("%s/qpf_03h_sp_0.1.f6-%s" % (JSON_DIR, pert), 'r') as f: df = json.load(f)
    c.append(dl.GeoJSON(data=df, id=str(pert), options=dict(weight=0.01, fill=False, color='rgba(255,0,255,0.9)'),
                          hoverStyle=dict(weight=5, color='#666', dashArray='')))
'''

def get_available_cyles():
    dirs = sorted(glob(JSON_DIR + '/*/'))
    date_times = []
    date_strings = []
    for folder in dirs:
        subfolders = [ f.path for f in os.scandir(folder) if f.is_dir() ]
        for target in subfolders:
            datestring = target[-13:]
            date_times.append(datetime.strptime(datestring, '%Y-%m-%d/%H'))
            date_strings.append(datestring)
    return date_times, date_strings

def get_minmax(classes):
    return dict(min=min(classes), max=max(classes))

def get_data(cycle_str, fhr, parm, var_type, levels):
    fname = "%s/%s/%s_%s.f%s" % (JSON_DIR, cycle_str, parm, var_type, str(fhr))
    with open(fname, 'r') as f: df = json.load(f)
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
model_cycles, model_cycle_strings = get_available_cyles()
delta = current_time - model_cycles[-1]
warn_str = "***WARNING: Latest available cycle is over %s hours old!***"
old_data_warn = ""
if delta > timedelta(hours=12):
    n_hours = int((delta.total_seconds() / 3600.))
    old_data_warn = warn_str % (n_hours)

# ...
# Set the initial color configurations
# ...
classes = qpf_levs
colorscale = qpf_cols
minmax = get_minmax(classes)
c = dl.GeoJSON(data=get_data(model_cycle_strings[-1], 3, 'qpf_03h', 'lpmm', classes),
               options=dict(style="window.local.module.set_style", weight=0.75),
               hideout=dict(colorscale=colorscale, classes=classes,
                            color_prop="values"),
               hoverStyle=dict(weight=1, opacity=0.7, color='Black'),
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

                dl.Map(center=[42, -88], zoom=6, children=[dl.TileLayer(url=mapbox_url), c, info, cbar],
                style={'width': '100%', 'height': '850px', 'margin': "auto", "display": "block"}),
            ],
            style={'width': '84%', 'height': '100vh', 'display': 'inline-block'},
        ),

        html.Div(
            [
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
                                    "Valid Time"
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
                                        options=[
                                            {'label': '00', 'value': 0},
                                            {'label': '06', 'value': 6},
                                            {'label': '12', 'value': 12},
                                            {'label': '18', 'value': 18},
                                        ],
                                        placeholder=str(model_cycles[-1].hour),
                                        value=str(model_cycles[-1].hour)
                                    )
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
                            style={'margin-left': '5%', 'width': '90%'},
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
                    ],
                ),
            ],
            style={'width': '15.5%', 'height': '100vh', 'float': 'right',
                   'display': 'inline-block', 'background-color':'#1d1d1d'},
        ),
    ]
)

'''
app.layout = html.Div([
    html.H3("Ensemble Model Viewer Test (GEFSv12)"),

    # ...
    # Forecast hour slider
    # ...
    dcc.Slider(
        id='fhr',
        min=3,
        max=120,
        value=3,
        marks={str(fhr): str(fhr) for fhr in np.arange(3,123,3)},
        step=None
    ),

    # ...
    # Parameter selection dropdown
    # ...
    html.H6("Parameter Selection:"),
    html.Div([
        dcc.Dropdown(
            id='parm-selection',
            options=[{'label': i, 'value': i} for i in parameters.keys()],
            value=list(parameters.keys())[0]
        ),
    ],
    style={'width': '25%', 'display': 'inline-block'}),

    html.Div([],style={'width': '5%', 'display': 'inline-block'}),

    # ...
    # Variable type selection
    # ...
    html.Div([
        dcc.RadioItems(
            id='var-type',
            options=[{'label': i, 'value': i} for i in variable_types.keys()],
            value=list(variable_types.keys())[0]
        ),
    ],
    style={'width': '15%', 'display': 'inline-block'}),

    html.Div([
        dcc.DatePickerSingle(
            id='date-selection',
            min_date_allowed=date.today() - timedelta(days=4),
            max_date_allowed=date.today(),
            initial_visible_month=date.today(),
            date=date.today()
        ),
    ],
    style={'width': '25%', 'display': 'inline-block'}),
    #html.H6(id='contour_val'),

    # ...
    # Map specifications
    # ...
    dl.Map(center=[42, -88], zoom=6, children=[dl.TileLayer(), c, info, cbar],
    style={'width': '100%', 'height': '725px', 'margin': "auto", "display": "block"}),
])
'''

# Updating the figure
@app.callback([Output("contourf", "data"),
               Output("contourf", "hideout"),
               Output("cbar", "max"),
               Output("cbar", "tickValues"),
               Output("cbar", "tickText"),
               Output("cbar", "classes"),
               Output("cbar", "colorscale")],
              [Input("fhr", "value"),
               Input("parm-selection", "value"),
               Input("var-type", "value"),
               Input('date-selection', 'date'),
               Input('hour-selection', 'value')])
def update(fhr, parm_selection, var_selection, date, hour):
    cycle_str = date + '/' + str(hour)
    parm = parameters[parm_selection]
    var_type = variable_types[var_selection]

    if parm in ['qpf_03h', 'qpf_06h', 'qpf_12h']:
        classes = qpf_levs
        colorscale = qpf_cols
    elif parm in ['snod_total']:
        classes = snow_levs
        colorscale = snow_cols

    data = get_data(cycle_str, fhr, parm, var_type, classes)
    minmax = get_minmax(classes)
    hideout = dict(colorscale=colorscale, classes=classes, color_prop="values"),

    ctg = ["{}".format(cls, classes[i+1]) for i, cls in enumerate(classes[:-1])] \
           + ["{}+".format(classes[-1])]
    indices = list(range(len(ctg)))
    return data, hideout, len(ctg), indices, ctg, indices, colorscale

# For the sampling output
@app.callback(Output("info", "children"), [Input("contourf", "hover_feature")])
def info_hover(feature):
    return get_info(feature)

# For the cycle selection
@app.callback(
    Output('selected-date', 'children'),
    [Input('date-selection', 'date')])
def update_date(date_value):
    date_object = date.fromisoformat(date_value)
    date_string = date_object.strftime('%Y-%m-%d')
    return date_string

@app.callback(
    Output('selected-hour', 'children'),
    [Input('hour-selection', 'value')])
def update_hour(hour_value):
    return str(hour_value).zfill(2)

if __name__ == '__main__':
    app.run_server(debug=True)
