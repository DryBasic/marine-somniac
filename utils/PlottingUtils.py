import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure


class PlottingUtils:
    @staticmethod
    def plot_feature(df: pd.DataFrame, plot='line') -> Figure:
        plot = {
            'line': px.line,
            'scatter': px.scatter
        }[plot]
        if len(df.columns) == 2:
            fig = plot(df,
                x='time',
                y=df.columns[1],
                #markers=True
            )
        else:
            fig = make_subplots(
                rows=len(df.columns)-1, cols=1,
                shared_xaxes=True
            )
            for i, col in enumerate([c for c in df.columns if c != 'time']):
                fig.add_trace(
                    go.Scatter(x=df['time'], y=df[col], name=col),
                    row=i+1, col=1
                )
        fig.update_layout(margin={'t':0})
        return fig