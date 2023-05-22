# install dependencies
# pip install dash dash-core-components dash-html-components dash-table pandas

import dash
# import dash_core_components as dcc
from dash import dcc
# import dash_html_components as html
from dash import html
# import dash_table
from dash import dash_table
from dash.dependencies import Input, Output, State
import json
import pandas as pd
import io
import base64


df = pd.read_csv('sheet.csv',encoding="utf-8", sep=',', index_col=0)
df['is_contacted'] = False

center_lat = df.Latitude.mean()
center_lon = df.Longitude.mean()

app = dash.Dash(
    external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
)
server = app.server
# dashboard and table layout
def app_layout(df):
    center_lat = df.Latitude.mean()
    center_lon = df.Longitude.mean()

    return html.Div([
        
        html.Div([
            html.Button('Export Selected Data', id='export-button'),
            dcc.Download(id='download-selected-data')
        ], className='three columns'),

        html.Div([
            dcc.Graph(
                id='graph',
                figure={
                    'data': [{
                        'lat': df.Latitude, 'lon': df.Longitude, 'type': 'scattermapbox', 
                        'marker': {
                            'color': df.is_contacted.map({True: 'red', False: 'blue'}),
                            'size': 8
                        }, 
                        'text': [f"{name}, {nachname}" for name, nachname in zip(df.Name, df.Nachname)],
                    }],
                    'layout': {
                        'mapbox': {
                            'accesstoken': (
                                'pk.eyJ1IjoiY2hyaWRkeXAiLCJhIjoiY2ozcGI1MTZ3M' +
                                'DBpcTJ3cXR4b3owdDQwaCJ9.8jpMunbKjdq1anXwU5gxIw'
                            ),
                            'center': {'lat': center_lat, 'lon': center_lon},
                            'zoom': 4.5
                        },
                        'margin': {
                            'l': 0, 'r': 1, 'b': 1, 't': 2
                        },
                    }
                }
            )
        ], className='four columns', style={'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2vw', 'marginTop': '2vw'}),
        
        
            html.Div([
        html.Div(
            children=html.Pre(id='lasso', style={'overflowY': 'scroll', 'height': '25vw'}),
        )
    ], 
             className='four columns', style={'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '3vw'}),
            
                    html.Div([
            html.Button('Export State', id='download-button'),
            dcc.Download(id='download-state')
        ], className='three columns'),

        html.Div([            dash_table.DataTable(                id='df-table',                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
            )
        ], className='four columns', style={'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '3vw','overflowY': 'scroll', 'height': '15vw'})
    ], className="row")

# Add the file upload button to the layout
app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Data')
    ),
    html.Div(id='output-data-upload'),

    app_layout(df)
])

@app.callback(
    Output('download-selected-data', 'data'),
    [Input('export-button', 'n_clicks')],
    [State('graph', 'selectedData')])
def export_selected_data(n_clicks, selectedData):
    if n_clicks is not None:
        if selectedData is not None:
            
            df_selected = pd.DataFrame(selectedData['points'])
            point_indices = df_selected["pointIndex"]
            all_selected = df[df.index.isin(point_indices) | (df['is_contacted'] == True)]
            all_selected.loc[:, 'is_contacted'] = True
            csv_string = all_selected.to_csv(encoding='utf-8', sep=",")
            return dict(content=csv_string, filename='selected-data.csv')
        else:
            return None

#export state
@app.callback(Output('download-state', 'data'),
              [Input('download-button', 'n_clicks')])
def download_state(n_clicks):
    if n_clicks is not None:
        df_string = df.to_csv(encoding='utf-8', sep=",")
        return dict(content=df_string, filename='save-state.csv') 
    

@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_df(contents, filename):

    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df_new = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=',', index_col=0)
            global df
            df = pd.read_csv('sheet.csv',encoding="utf-8", sep=',', index_col=0)
            df['is_contacted'] = False
            df.update(df_new)
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])
        
        # Update the layout with the new data
        return html.Div([
            app_layout(df),
            html.P('Last selection')
        ])
    else:
        return None

@app.callback(
    Output('lasso', 'children'),
    [Input('graph', 'selectedData')])
def display_data(selectedData):
    if selectedData is None:
        return "Not Selection"
    return json.dumps(selectedData, indent=2)



if __name__ == '__main__':
    app.run_server(debug=True)
