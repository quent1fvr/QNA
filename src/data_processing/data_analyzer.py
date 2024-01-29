import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import tempfile
class DataAnalyzer:
    def __init__(self, df_logs, df_logs_history, df_feedback, df_thumb_feedback, df_manual_feedback):
        self.df_logs = df_logs
        self.df_logs_history = df_logs_history
        self.df_feedback = df_feedback
        self.df_thumb_feedback = df_thumb_feedback
        self.df_manual_feedback = df_manual_feedback
        

    def plot_activity_over_time(self):
        fig1 = px.histogram(self.df_logs, x='DateTime', color='Activity', barmode='group',
                            title='Activity Over Time')

        # Add range selector and slider to the x-axis
        fig1.update_xaxes(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label='1d', step='day', stepmode='backward'),
                    dict(count=7, label='1w', step='day', stepmode='backward'),
                    dict(count=1, label='1m', step='month', stepmode='backward'),
                    dict(count=6, label='6m', step='month', stepmode='backward'),
                    dict(step='all')
                ])
            ),
            rangeslider=dict(visible=True),
            type='date'
        )

        # Updating the hover mode for better interaction
        fig1.update_layout(hovermode='x') 
        fig1.update_layout(
        autosize=True,
        margin=dict(l=0, r=0, t=0, b=0)  # Reduces the padding around the plot
    )  
        return fig1

    def plot_query_response_time(self):
        average_times = self.df_logs[self.df_logs['Activity'] == 'Query'].groupby('Collection')['Time'].mean().reset_index()

        # Create the scatter plot with faceting
        fig2 = px.scatter(self.df_logs[self.df_logs['Activity'] == 'Query'], x='DateTime', y='Time', 
                        color='Collection', facet_col='Collection', facet_col_wrap=2,
                        title='Query Response Time Analysis by Collection')

        # Add a line for the average time in each subplot
        for collection in self.df_logs['Collection'].unique():
            for data in fig2.data:
                filtered_avg_times = average_times[average_times['Collection'] == collection]['Time']
                if not filtered_avg_times.empty:
                    avg_time = filtered_avg_times.values[0]
                if data.name == collection:
                    fig2.add_shape(type='line',
                                xref=data.xaxis, yref=data.yaxis,  # Refer to the subplot's axes
                                x0=data.x.min(), y0=avg_time,
                                x1=data.x.max(), y1=avg_time,
                                line=dict(color='gray', dash='dot', width=2))

        # Update the layout for better readability
        fig2.update_layout(height=1200, width=1200)
        fig2.update_xaxes(tickangle=-45)
        return fig2
        
    def plot_success_vs_failure_rate(self):
        success_count = len(self.df_logs[self.df_logs['LogLevel'] != 'WARNING'])
        fail_count = len(self.df_logs[self.df_logs['LogLevel'] == 'WARNING'])

        df_status = pd.DataFrame({'Status': ['Success', 'Fail'], 'Count': [success_count, fail_count]})
        fig3 = px.pie(df_status, names='Status', values='Count', title='Success vs Failure Rate')
        fig3.update_traces(textinfo='percent+label', hoverinfo='label+value')
        return fig3

    def plot_activity_frequency_by_collection(self):
        query_df = self.df_logs[self.df_logs['Activity'] == 'Query']
        fig4 = go.Figure()

        # Get unique collections from the filtered dataframe
        collections = query_df['Collection'].unique()

        # Add one bar trace per collection for 'Query' activities
        for collection in collections:
            df_collection = query_df[query_df['Collection'] == collection]
            fig4.add_trace(go.Bar(
                x=[collection],  # x is the collection name
                y=[df_collection.shape[0]],  # y is the count of 'Query' activities for the collection
                name=f'{collection}',  # Legend name
                legendgroup='Query'  # Grouping in legend
            ))
        fig4.update_layout(
            barmode='group',
            title='Activity Frequency by Collection (Queries Only)',
            xaxis_title='Collection',
            yaxis_title='Count',
            autosize=True

        )
        return fig4

    def plot_upload_times_analysis(self):
        fig5 = px.box(self.df_logs[self.df_logs['Activity'] == 'Upload'], y='Time', title='Upload Times Analysis')
        fig5.update_traces(hovertemplate="Time: %{y}<br>Count: %{x}")
        return fig5


    def query_answer_history(self):
        df_logs_history_reversed = self.df_logs_history.iloc[::-1]
        columns_without_time = [col for col in df_logs_history_reversed.columns if col != 'Time']

        # Create a Plotly table with the reversed DataFrame
        fig7 = go.Figure(data=[go.Table(
            header=dict(
                values=list(columns_without_time),
                fill_color='orange',
                align='left'
            ),
            cells=dict(
                values=[df_logs_history_reversed[k].tolist() for k in columns_without_time],
                fill_color='white',
                align='left'
            )
        )])

        # Updating the layout of the figure
            # Update the layout for better readability
        fig7.update_layout(height=1200, width=1200, title_text="Query/Answer History ")
        fig7.update_xaxes(tickangle=-45)      
        return fig7  
    
    
    def plot_feedback_analysis(self):
        df_manual_feedback_reversed = self.df_manual_feedback.iloc[::-1][['timestamp', 'feedback']]
        # Create a Plotly table with the reversed and filtered DataFrame
        fig9 = go.Figure(data=[go.Table(
            header=dict(
                values=list(df_manual_feedback_reversed.columns),
                fill_color='orange',
                align='left'
            ),
            cells=dict(
                values=[df_manual_feedback_reversed[k].tolist() for k in df_manual_feedback_reversed.columns],
                fill_color='white',
                align='left'
            )
        )])
        fig9.update_layout(title='Table of Manual Feedbacks')
        fig9.update_layout(height=400, width=1200)
        return fig9


    def plot_thumb_feedback_analysis(self):
        required_columns = ['timestamp', 'feedback', 'collection', 'query', 'answer', 'sources']

        # Create the table with only the specified columns
        fig10 = go.Figure(data=[go.Table(
            header=dict(
                values=[column for column in required_columns if column in self.df_thumb_feedback.columns],
                fill_color='orange',
                align='left'
            ),
            cells=dict(
                values=[self.df_thumb_feedback[column].tolist() for column in required_columns if column in self.df_thumb_feedback.columns],
                fill_color='white',
                align='left'
            )
        )])

        fig10.update_layout(title='Table of Thumb Feedbacks')
        fig10.update_layout(height=400, width=1200)
        return fig10



    def generate_table_from_dataframe(self, dataframe):
        # Convert a DataFrame to a Plotly Table
        columns = dataframe.columns
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(columns), fill_color='orange', align='left'),
            cells=dict(values=[dataframe[k].tolist() for k in columns], fill_color='white', align='left')
        )])
        fig.update_layout(height=400, width=1200)
        return fig


    def dataframe_to_excel(self, dataframe):
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmpfile:
            # Save the DataFrame to the temporary file
            with pd.ExcelWriter(tmpfile.name, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False)
            # Return the path to the temporary file
            return tmpfile.name