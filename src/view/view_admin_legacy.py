import gradio as gr
from src.control.control import Chatbot
from chromadb.utils import embedding_functions
import os
import logging 
import time
import gradio as gr
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import pandas as pd

########## LEGACY -----> refer to admin_view.py ##########

theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="blue",
    neutral_hue="stone",
)

def parse_feedback_log_entry(log_entry):
    match = re.match(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - (Thumb Feedback|Manual Feedback) - (Positive|Negative|Feedback: (.*?)) - Temps: (.+)',
        log_entry
    )
    if match:
        timestamp, feedback_type, _, feedback, response_time = match.groups()
        return {
            "timestamp": timestamp,
            "feedback_type": feedback_type,
            "feedback": feedback if feedback else _,
            "response_time": response_time
        }
    else:
        return None
# Let's redefine the function to correctly parse the 'Sources' field which is multiline and complex.

def parse_log_entry_history(log_entry):
    try:
        # Use regular expressions to extract the timestamp, level, and main message
        match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.*)', log_entry)
        if not match:
            return None
        
        timestamp, level, message = match.groups()

        # Extract collection name
        collection_match = re.search(r'Collection: (.*?)(?=, Query:)', message)
        collection = collection_match.group(1).strip() if collection_match else None

        # Extract query
        query_match = re.search(r'Query: (.*?)(?=, Answer:)', message)
        query = query_match.group(1).strip() if query_match else None

        # Extract answer
        answer_match = re.search(r'Answer: (.*?)(?=,  Sources:)', message)
        answer = answer_match.group(1).strip() if answer_match else None

        # Extract sources
        # Find the entire 'Sources' to 'Temps' section
        sources_section_match = re.search(r'Sources: (.*) - Temps:', log_entry, re.DOTALL)
        sources_section = sources_section_match.group(1).strip() if sources_section_match else None
        
        # Clean up the 'Sources' section to extract the list
        sources = None
        if sources_section:
            # Assume the sources are enclosed in brackets '[]'
            sources_match = re.search(r'\[(.*)\]', sources_section, re.DOTALL)
            if sources_match:
                # Extract the content inside the brackets and split by ', ' to get a list of sources
                sources = sources_match.group(1).split("', '")
        
        # Extract time
        time_match = re.search(r'Temps: (.*)', log_entry)
        time = time_match.group(1).strip() if time_match else None

        # Construct and return the result dictionary
        return {
            "timestamp": timestamp,
            "level": level,
            "collection": collection,
            "query": query,
            "answer": answer,
            "sources": sources,  # Return the cleaned list of sources
            "time": time
        }
    except Exception as e:
        # Print error message for debugging
        print("Error parsing log:", e)
        # Return None if parsing fails
        return None



    



def plot_thumb_feedback_sentiment(df_logs):
    import plotly.express as px

    # Extracting Positive and Negative feedbacks
    thumb_feedback = df_logs[df_logs['Activity'].str.contains('Thumb Feedback')].copy()
    thumb_feedback['Sentiment'] = thumb_feedback['Activity'].apply(lambda x: 'Positive' if 'Positive' in x else 'Negative')

    # Grouping by DateTime and Sentiment
    sentiment_trend = thumb_feedback.groupby([thumb_feedback['DateTime'].dt.date, 'Sentiment']).size().unstack().fillna(0)
    fig2 = px.line(sentiment_trend, title='Thumb Feedback Sentiment Trend Over Time')
    return fig2


def plot_feedback_type_distribution(df_logs):
    import plotly.express as px

    # Assuming 'Activity' column contains feedback type information
    feedback_type_counts = df_logs['Activity'].value_counts().reset_index()
    feedback_type_counts.columns = ['Feedback Type', 'Counts']

    # Create a bar chart using Plotly Express
    fig = px.bar(feedback_type_counts, x='Feedback Type', y='Counts', title='Feedback Type Distribution')
    return fig
def refresh_plots():
    # Call generate_plots to get the updated plot
    updated_fig1,updated_fig2,updated_fig3,updated_fig4,updated_fig5,updated_fig7,updated_fig8,updated_fig9 = generate_plots()
    # Return the updated plot
    return updated_fig1,updated_fig2,updated_fig3,updated_fig4,updated_fig5,updated_fig7,updated_fig8,updated_fig9


# Define the log parsing function
def parse_log_entry(entry):
    # Original log format pattern
    original_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - Collection: ([\w\s_]+)[^-]* - Time: ([0-9.]+)'
    match = re.search(original_pattern, entry)

    if match:
        return {
            'DateTime': match.group(1),
            'LogLevel': match.group(2),
            'Activity': match.group(3),
            'Collection': match.group(4).strip(),
            'Time': float(match.group(5))
        }
    
    # Fail log without a collection
    fail_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - .+ - Time: ([0-9.]+)'
    match = re.search(fail_pattern, entry)

    if match:
        return {
            'DateTime': match.group(1),
            'LogLevel': match.group(2),
            'Activity': match.group(3),
            'Collection': 'N/A',
            'Time': float(match.group(4))
        }

    feedback_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+ Feedback) - (Feedback: )?(.*) - Time: ([0-9.]+)'
    match = re.search(feedback_pattern, entry)
    if match:
        return {
            'DateTime': match.group(1),
            'LogLevel': match.group(2),
            'Activity': match.group(3),
            'Collection': 'N/A',  # Or you might want to add feedback text here instead
            'Time': float(match.group(6))  # Use group 6 for the time value
        }   
    return None  # If no pattern matches, return None


    # Read the log file and parse entries
with open('src/Logs/generated_log.log', 'r') as file:
    logs = [parse_log_entry(line) for line in file if parse_log_entry(line)]

    # Create a DataFrame
df_logs = pd.DataFrame(logs)
df_logs['DateTime'] = pd.to_datetime(df_logs['DateTime'])

def is_valid_log_entry(log_entry):
    if log_entry is None:
        return False
    return log_entry.get('query', None) not in [None, ''] and log_entry.get('answer', None) not in [None, '']


# Read the log file and parse each line
with open('src/Logs/generated_log.log', 'r') as file:
    parsed_logs_history = [parse_log_entry_history(line) for line in file if is_valid_log_entry(parse_log_entry_history(line))]

# Filter out None values
parsed_logs_from_file = [log for log in parsed_logs_history if log is not None]

# Create a DataFrame from the parsed logs
df_logs_history = pd.DataFrame(parsed_logs_from_file)

df_logs_history.head() 



with open('src/Logs/generated_log.log', 'r') as file:
    parsed_feedback = [parse_feedback_log_entry(line) for line in file if 'Feedback' in line]

# Filter out None values
parsed_feedback = [feedback for feedback in parsed_feedback if feedback is not None]

# Creating DataFrame from parsed feedback
df_feedback = pd.DataFrame(parsed_feedback)
#print(df_feedback)
# Separating DataFrame for Thumb Feedback and Manual Feedback
df_thumb_feedback = df_feedback[df_feedback['feedback_type'] == 'Thumb Feedback']
df_manual_feedback = df_feedback[df_feedback['feedback_type'] == 'Manual Feedback']
df_manual_feedback = df_manual_feedback.drop('response_time', axis=1)
# Plot 1: Count of Positive vs Negative Thumb Feedback
thumb_feedback_counts = df_thumb_feedback['feedback'].value_counts()



def dataframe_to_excel():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmpfile:
        # Save the DataFrame to the temporary file
        with pd.ExcelWriter(tmpfile.name, engine='xlsxwriter') as writer:
            df_logs_history.to_excel(writer, index=False)
        # Return the path to the temporary file
        return tmpfile.name

def dataframe_to_excel_feedbacks():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmpfile:
        # Save the DataFrame to the temporary file
        with pd.ExcelWriter(tmpfile.name, engine='xlsxwriter') as writer:
            df_manual_feedback.to_excel(writer, index=False)
        # Return the path to the temporary file
        return tmpfile.name
    
# In your Gradio app
download_button = gr.File(label="Download Excel", value=dataframe_to_excel())
# Function to generate plots
def generate_plots():
    
    fig1 = px.histogram(df_logs, x='DateTime', color='Activity', barmode='group',
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
    #fig1.show()
# Let's assume df_logs is your DataFrame and it's already defined

# Calculate the average times
    average_times = df_logs[df_logs['Activity'] == 'Query'].groupby('Collection')['Time'].mean().reset_index()

    # Create the scatter plot with faceting
    fig2 = px.scatter(df_logs[df_logs['Activity'] == 'Query'], x='DateTime', y='Time', 
                    color='Collection', facet_col='Collection', facet_col_wrap=2,
                    title='Query Response Time Analysis by Collection')

    # Add a line for the average time in each subplot
    for collection in df_logs['Collection'].unique():
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

    # Show the figure
    #fig2.show()

    # Dashboard 3: Success vs Failure Rate
    success_count = len(df_logs[df_logs['LogLevel'] != 'WARNING'])
    fail_count = len(df_logs[df_logs['LogLevel'] == 'WARNING'])

    df_status = pd.DataFrame({'Status': ['Success', 'Fail'], 'Count': [success_count, fail_count]})
    fig3 = px.pie(df_status, names='Status', values='Count', title='Success vs Failure Rate')
    fig3.update_traces(textinfo='percent+label', hoverinfo='label+value')
    #fig3.show()
    query_df = df_logs[df_logs['Activity'] == 'Query']

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

    # Update layout
    fig4.update_layout(
        barmode='group',
        title='Activity Frequency by Collection (Queries Only)',
        xaxis_title='Collection',
        yaxis_title='Count',
        autosize=True

    )

    # Dashboard 5: Upload Times Analysis
    fig5 = px.box(df_logs[df_logs['Activity'] == 'Upload'], y='Time', title='Upload Times Analysis')
    fig5.update_traces(hovertemplate="Time: %{y}<br>Count: %{x}")
    

    df_logs_history_reversed = df_logs_history.iloc[::-1]

    # Create a Plotly table with the reversed DataFrame
    fig7 = go.Figure(data=[go.Table(
        header=dict(
            values=list(df_logs_history_reversed.columns),
            fill_color='orange',
            align='left'
        ),
        cells=dict(
            values=[df_logs_history_reversed[k].tolist() for k in df_logs_history_reversed.columns],
            fill_color='white',
            align='left'
        )
    )])

    # Updating the layout of the figure
        # Update the layout for better readability
    fig7.update_layout(height=1200, width=1200, title_text="Query/Answer History ")
    fig7.update_xaxes(tickangle=-45)

    # Showing the figure
    #fig7.show()
    
    fig8 = go.Figure(data=[
        go.Bar(x=thumb_feedback_counts.index, y=thumb_feedback_counts.values)
    ])
    fig8.update_layout(title='Count of Positive vs Negative Thumb Feedback', xaxis_title='Feedback', yaxis_title='Count')
    fig8.update_layout(height=400, width=1200)
    fig8.update_xaxes(tickangle=-45)

    # Table of Manual Feedbacks
    df_manual_feedback_reversed = df_manual_feedback.iloc[::-1]

# Create a Plotly table with the reversed DataFrame
    fig9 = go.Figure(data=[go.Table(
        header=dict(
            values=list(df_manual_feedback_reversed.columns),
            fill_color='lightblue',
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


    return fig1,fig2,fig3,fig4,fig5,fig7,fig8,fig9

fig1,fig2, fig3, fig4, fig5 , fig7,fig8,fig9  = generate_plots()

def plot_feedback_type_distribution(df_logs):

    # Assuming 'Activity' column contains feedback type information
    feedback_type_counts = df_logs['Activity'].value_counts().reset_index()
    feedback_type_counts.columns = ['Feedback Type', 'Counts']
    #print(feedback_type_counts)
    # Create a bar chart using Plotly Express
    fig = px.bar(feedback_type_counts, x='Feedback Type', y='Counts', title='Feedback Type Distribution')
    return fig


def gradio_interface():
    return fig1, fig2, fig3, fig4, fig5, fig7, fig8 , fig9

def run(ctrl: Chatbot, config: {}):
    with gr.Blocks(theme=theme) as qna:
        gr.Markdown("## Administrator view")
        with gr.Tabs() as tabs:
            with gr.Tab("Admin view "):
                with gr.Row():
                    with gr.Column(scale=10):
                        gr.Markdown(config['title'])
                        page_start_warning = gr.Markdown("The administrator is allowed to upload / delete a collection. If your document starts with a front cover and/or a table of contents, please enter the page number of the first page with real content.")
                        actual_page_start = gr.Number(
                            label="Start page (default = 1)",
                            visible=True,
                            interactive=True,
                            container=True,
                            value=1,
                        )

                        include_images_btn = gr.Checkbox(
                            label="Analyse text from images. This option is definitely slower, particularly on big documents. (ONLY for .pdf)",
                            value=False,
                            visible=True,
                            container=True,
                        )

                        input_doc_comp = gr.File(
                            label="Upload a file",
                            scale=1,
                            min_width=100,
                        )
                        
                        histo_text_comp = gr.Chatbot(
                            visible=False,
                            value=[],
                        )
                        input_text_comp = gr.Textbox(
                            label="",
                            lines=1,
                            visible=False,
                            max_lines=3,
                            interactive=True,
                            placeholder="Posez votre question ici",
                        )

                        clear_btn = gr.Button("Clear Chat", visible=False)

                        input_example_comp = gr.Radio(
                            label="Examples",
                            choices=config['examples'].values(),
                            value="",
                            visible=False,
                        )
                        
                        source_text_comp = []
                        for i in range(4):
                            source_text_comp.append(gr.Textbox(
                                lines=4,
                                max_lines=4,
                                interactive=False,
                                visible=False,
                            ))
                        upload_another_doc_btn = gr.Button("Upload another document", visible=False)

                    open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'], model_name="text-embedding-ada-002")
                    with gr.Column(scale=7):
                        collections_list = gr.Radio(choices=[a.name for a in ctrl.client_db.list_collections()],
                            label="Current collections in the database",
                            visible=True,
                            info="Choose a collection to query."
                        )
                        delete_database_btn = gr.Button("Delete current collection", visible=True) 
                def input_doc_fn(input_doc_, include_images_, actual_page_start_):
                    start_time = time.time()
                    result = ctrl.upload_doc(input_doc_,include_images_, actual_page_start_)
                    end_time = time.time()
                    if result == True:
                        temps_execution = end_time - start_time
                        logging.info(f"Temps d'exécution pour upload_doc: {temps_execution} secondes", extra={'category': 'Upload', 'elapsed_time': temps_execution})

                        return {
                            input_doc_comp: gr.update(visible=False),
                            input_text_comp: gr.update(visible=True),
                            input_example_comp: gr.update(visible=True),
                            clear_btn: gr.update(visible=False),
                            include_images_btn: gr.update(visible=True,value=include_images_),
                            delete_database_btn: gr.update(visible=True),
                            upload_another_doc_btn: gr.update(visible=True),
                            collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()],value=ctrl.retriever.collection.name),
                            page_start_warning: gr.update(visible=True),
                            actual_page_start: gr.update(visible=True),
                        }
                    else:
                        logging.warning(f"Le document n'a pas été téléchargé avec succès.", extra={'category': 'Fail', 'elapsed_time':0})
                        gr.Warning("File extension not supported. Only .docx, .pdf and .html are supported.")
                        return {
                            input_doc_comp: gr.update(visible=True),
                            input_text_comp: gr.update(visible=False),
                            input_example_comp: gr.update(visible=False),
                            clear_btn: gr.update(visible=False),
                            include_images_btn: gr.update(visible=True,value=include_images_),
                            page_start_warning: gr.update(visible=True),
                            actual_page_start: gr.update(visible=True, value=1),
                        }
                            
                def input_file_clear():
                    update_ = {
                        input_doc_comp: gr.update(visible=True, value=None),
                        clear_btn: gr.update(visible=False),
                        input_text_comp: gr.update(value='', visible=False),
                        histo_text_comp: gr.update(value='', visible=False),
                        input_example_comp: gr.update(value='', visible=False),
                        include_images_btn: gr.update(visible=True),
                        upload_another_doc_btn: gr.update(visible=False),
                        delete_database_btn: gr.update(visible=True),
                        page_start_warning: gr.update(visible=True),
                        actual_page_start: gr.update(visible=True, value=1),
                        collections_list: gr.update(value=None, choices=[a.name for a in ctrl.client_db.list_collections()]),
                    }
                    for i in range(4):
                        update_[source_text_comp[i]] = gr.update(visible=False, value='hello')
                    return update_


                def input_text_fn1(input_text_, histo_text_):
                    histo_text_.append((input_text_, None))
                    update_ = {
                        histo_text_comp: gr.update(visible=True, value=histo_text_),
                        input_example_comp: gr.update(visible=False,),
                    }
                    for i in range(4):
                        update_[source_text_comp[i]] = gr.update(visible=False)
                    return update_

                def input_text_fn2(input_text_, histo_text_):
                    answer, sources = ctrl.get_response(query=input_text_, histo=histo_text_)
                    histo_text_[-1] = (input_text_, answer)
                    update_ = {
                        histo_text_comp: gr.update(value=histo_text_),
                        input_text_comp: gr.update(value=''),
                    }
                    for i in range(min(len(sources), 3)):
                        s = sources[i]
                        if i != 0:
                            prev = sources[i - 1]
                            if prev.index == s.index:
                                continue
                        source_label = f'{s.index}   {s.title}                        score = {s.distance_str}'
                        source_text = s.content
                        update_[source_text_comp[i]] = gr.update(visible=True, value=source_text, label=source_label)
                    return update_

                def input_example_fn(input_example_, histo_text_):
                    histo_text_.append((input_example_, None))
                    update_ = {
                        input_text_comp: gr.update(value=input_example_),
                        histo_text_comp: gr.update(visible=True, value=histo_text_),
                        input_example_comp: gr.update(visible=False, value=''),
                    }
                    for i in range(4):
                        update_[source_text_comp[i]] = gr.update(visible=False)
                    return update_

                def clear_fn():
                    update_ = {
                        input_text_comp: gr.update(value=''),
                        histo_text_comp: gr.update(value='', visible=False),
                        input_example_comp: gr.update(value='', visible=True),
                        upload_another_doc_btn: gr.update(visible=False),
                    }
                    for i in range(4):
                        update_[source_text_comp[i]] = gr.update(visible=False, value='hello')
                    return update_

                def list_all_chroma_collections():
                    update = {
                        collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                    }
                    return update

                def change_collection(collection_name):
                    ctrl.retriever.collection = ctrl.client_db.get_collection(collection_name, embedding_function=open_ai_embedding)
                    return {
                        delete_database_btn: gr.update(visible=True),
                        input_doc_comp: gr.update(visible=True,value=None),
                        input_text_comp: gr.update(visible=False, value=''),
                        input_example_comp: gr.update(visible=False),
                        clear_btn: gr.update(visible=False),
                        collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                        include_images_btn: gr.update(visible=True),
                        histo_text_comp: gr.update(visible=False, value=''),
                        upload_another_doc_btn: gr.update(visible=False),
                        actual_page_start: gr.update(visible=True),
                        page_start_warning: gr.update(visible=True),
                    }

                def delete_curr_database():
                    start_time = time.time()
                    ctrl.client_db.delete_collection(ctrl.retriever.collection.name)
                    end_time = time.time()
                    logging.info(f"Collection {ctrl.retriever.collection.name} deleted from the database", extra={'category': 'Deletion', 'elapsed_time': end_time-start_time})
                    gr.Info(f"Collection {ctrl.retriever.collection.name} deleted from the database")
                    return {
                        delete_database_btn: gr.update(visible=False),
                        input_doc_comp: gr.update(visible=True,value=None),
                        input_text_comp: gr.update(visible=False, value=''),
                        input_example_comp: gr.update(visible=False),
                        clear_btn: gr.update(visible=False),
                        collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                        include_images_btn: gr.update(visible=True),
                        histo_text_comp: gr.update(visible=False, value=''),
                        upload_another_doc_btn: gr.update(visible=False),
                        actual_page_start: gr.update(visible=True, value=1),
                        page_start_warning: gr.update(visible=True),
                    }

                upload_another_doc_btn.click(input_file_clear,
                                inputs=None,
                                outputs=[collections_list, page_start_warning, actual_page_start, input_doc_comp, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, delete_database_btn,upload_another_doc_btn, source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])

                delete_database_btn.click(delete_curr_database,
                                inputs=None,
                                outputs=[page_start_warning, actual_page_start, delete_database_btn, input_doc_comp, input_text_comp, input_example_comp, clear_btn, collections_list, include_images_btn, histo_text_comp, upload_another_doc_btn])

                collections_list.input(change_collection,
                                inputs=[collections_list],
                                outputs=[actual_page_start, page_start_warning, collections_list, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, input_doc_comp, delete_database_btn,upload_another_doc_btn])

                input_doc_comp \
                    .upload(input_doc_fn,
                            inputs=[input_doc_comp, include_images_btn, actual_page_start],
                            outputs=[page_start_warning, actual_page_start, input_doc_comp, input_text_comp,upload_another_doc_btn,
                                    input_example_comp, include_images_btn, clear_btn, histo_text_comp, delete_database_btn,collections_list, source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
                    .then(list_all_chroma_collections,
                        inputs=None,
                        outputs=[collections_list])
                
                input_doc_comp \
                    .clear(input_file_clear,
                            inputs=None,
                            outputs=[page_start_warning, actual_page_start, input_doc_comp, clear_btn, upload_another_doc_btn, input_text_comp, histo_text_comp, input_example_comp, include_images_btn, delete_database_btn,
                                        source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\

                input_text_comp \
                    .submit(input_text_fn1,
                            inputs=[input_text_comp, histo_text_comp],
                            outputs=[histo_text_comp, input_example_comp,
                                    source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
                    .then(input_text_fn2,
                        inputs=[input_text_comp, histo_text_comp],
                        outputs=[input_text_comp, histo_text_comp,
                                source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])
                input_example_comp \
                    .input(input_example_fn,
                        inputs=[input_example_comp, histo_text_comp],
                        outputs=[input_text_comp, histo_text_comp, input_example_comp,
                                    source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
                    .then(input_text_fn2,
                        inputs=[input_text_comp, histo_text_comp],
                        outputs=[input_text_comp, histo_text_comp,
                                source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])
                clear_btn.click(clear_fn,
                                inputs=None,
                                outputs=[input_text_comp, histo_text_comp, input_example_comp,upload_another_doc_btn,
                                        source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]]) 
            with gr.Tab("Activity Over Time"):
                with gr.Row():
                    with gr.Column():
                        plot1 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")

            with gr.Tab("Response Time Analysis"):
                with gr.Row():
                    with gr.Column():
                        plot2 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
            with gr.Tab("Success VS Failure Rate"):
                with gr.Row():
                    with gr.Column():
                        plot3 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
            with gr.Tab("Activity Frequency"):
                with gr.Row():
                    with gr.Column():
                        plot4 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
            with gr.Tab("Upload Time"):
                with gr.Row():
                    with gr.Column():
                        plot5 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
            with gr.Tab("Query/Answer"):
                with gr.Row():
                    # Assuming you want the download button at the top right corner
                    with gr.Column(scale=0):  # Small column for the download button
                        download_button = gr.File(label="Download Excel", value=dataframe_to_excel)
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       

                with gr.Row():
                    plot7 = gr.Plot()
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot6])
                        
            with gr.Tab("Thumbs Feedbacks"):
                with gr.Row():
                    with gr.Column():
                        plot8 = gr.Plot()
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
                        
            with gr.Tab("Manual Feedbacks"):
                with gr.Row():
                    with gr.Column(scale=0):  # Small column for the download button
                        refresh_button = gr.Button("Refresh Plot")
                        #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
                        download_button = gr.File(label="Download Excel", value=dataframe_to_excel_feedbacks)
                with gr.Row():
                    plot9 = gr.Plot()
            refresh_button.click(fn=refresh_plots, inputs=[], outputs=[plot1,plot2,plot3,plot4,plot5,plot7,plot8,plot9])

                                                
                        
                        
        qna.load(fn=gradio_interface, outputs=[plot1, plot2, plot3, plot4, plot5,plot7, plot8,plot9])


    return qna