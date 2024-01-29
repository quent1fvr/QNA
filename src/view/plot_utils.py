import plotly.express as px
import plotly.graph_objects as go

def create_histogram(df, x, color, title):
    fig = px.histogram(df, x=x, color=color, barmode='group', title=title)
    # Additional styling and configuration...
    return fig

def create_scatter_plot(df, x, y, color, title):
    fig = px.scatter(df, x=x, y=y, color=color, title=title)
    # Additional styling and configuration...
    return fig

def create_pie_chart(df, names, values, title):
    fig = px.pie(df, names=names, values=values, title=title)
    # Additional styling and configuration...
    return fig

def create_bar_chart(df, x, y, title):
    fig = go.Figure(data=[go.Bar(x=df[x], y=df[y])])
    fig.update_layout(title=title)
    # Additional styling and configuration...
    return fig

# Additional plotting utilities...
