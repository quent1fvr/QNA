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
import numpy as np

def plot_thumb_feedback_sentiment(df_logs):
    import plotly.express as px

    # Extracting Positive and Negative feedbacks
    thumb_feedback = df_logs[df_logs['Activity'].str.contains('Thumb Feedback')]
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
with open('generated_log.log', 'r') as file:
    logs = [parse_log_entry(line) for line in file if parse_log_entry(line)]

    # Create a DataFrame
df_logs = pd.DataFrame(logs)
print(df_logs)


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
    #fig1.show()
    
    
    # Dashboard 2: Response Time Analysis
    average_times = df_logs[df_logs['Activity'] == 'Query'].groupby('Collection')['Time'].mean().reset_index()

    # Then, create the scatter plot with faceting
    average_times = df_logs[df_logs['Activity'] == 'Query'].groupby('Collection')['Time'].mean().reset_index()

    # Then, create the scatter plot with faceting
    fig2 = px.scatter(df_logs[df_logs['Activity'] == 'Query'], x='DateTime', y='Time', 
                    color='Collection', facet_col='Collection', facet_col_wrap=2,
                    title='Query Response Time Analysis by Collection')

    # Go through each collection and add a line for the average time
    for collection in df_logs['Collection'].unique():
        if collection in average_times['Collection'].values:
            avg_time = average_times[average_times['Collection'] == collection]['Time'].values[0]

            # Find the subplot corresponding to the current collection
            for i, annotation in enumerate(fig2.layout.annotations):
                if annotation.text == f"Collection={collection}":
                    row, col = (i // 2) + 1, (i % 2) + 1
                    # Add a horizontal line for the average time
                    fig2.add_shape(type='line',
                                xref='x' + str(col), yref='y' + str(row),  # Refer to the subplot's axes
                                x0=fig2.data[0].x.min(), y0=avg_time,
                                x1=fig2.data[0].x.max(), y1=avg_time,
                                line=dict(color='gray', dash='dot', width=2),
                                row=row, col=col)  # Specify the subplot to draw the line in

    # Update the layout for better readability
    fig2.update_layout(height=1200, width=1200)
    fig2.update_xaxes(tickangle=-45)

    #fig2.show()
    df_logs['DateTime'] = pd.to_datetime(df_logs['DateTime'])

    df_logs['JitteredDateTime'] = df_logs['DateTime'] + pd.to_timedelta(np.random.uniform(-0.5, 0.5, size=len(df_logs)), unit='h')

    fig2bis = px.scatter(df_logs[df_logs['Activity'] == 'Query'], x='JitteredDateTime', y='Time', 
                    color='Collection', title='Query Response Time Analysis')

    # Adjust the layout for better readability
    fig2bis.update_layout(height=600, width=1200)
    fig2bis.update_traces(marker=dict(size=12, opacity=0.6, line=dict(width=0.5, color='DarkSlateGrey')))
    fig2bis.update_xaxes(tickangle=-45)

    #fig2bis.show()
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
            name=f'{collection} - Query',  # Legend name
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
    
    fig6 = plot_feedback_type_distribution(df_logs)

    # Plot 7: Thumb Feedback Sentiment Trend
    fig7 = plot_thumb_feedback_sentiment(df_logs)

    # Generate word cloud for Manual Feedback
    # fig8 = generate_word_cloud(df_logs)



    return fig1, fig2, fig2bis, fig3, fig4, fig5 , fig6 , fig7
import gradio as gr

print(df_logs)
fig1, fig2, fig2bis, fig3, fig4, fig5 , fig6 , fig7 = generate_plots()

def plot_feedback_type_distribution(df_logs):
    import plotly.express as px

    # Assuming 'Activity' column contains feedback type information
    feedback_type_counts = df_logs['Activity'].value_counts().reset_index()
    feedback_type_counts.columns = ['Feedback Type', 'Counts']
    print(feedback_type_counts)
    # Create a bar chart using Plotly Express
    fig = px.bar(feedback_type_counts, x='Feedback Type', y='Counts', title='Feedback Type Distribution')
    return fig


def gradio_interface():
    return fig1, fig2, fig2bis, fig3, fig4, fig5, fig6, fig7

def run(ctrl: Chatbot, config: {}):
    with gr.Blocks() as qna:
        gr.Markdown("## Administrator view")
        with gr.Tabs() as tabs:
            with gr.Tab("Admin view "):
                with gr.Row():
                    with gr.Column(scale=10):
                        gr.Markdown(config['title'])
                        page_start_warning = gr.Markdown("The administrator is allowed to upload / delete a collection. If your document starts with a front cover and/or a table of contents, please enter the page number of the first page with real content. Document supported: .pdf, .docx, html")
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
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Response Time Analysis"):
                with gr.Row():
                    with gr.Column():
                        plot2 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Plot 2bis"):
                with gr.Row():
                    with gr.Column():
                        plot2bis = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Success VS Failure Rate"):
                with gr.Row():
                    with gr.Column():
                        plot3 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Activity Frequency"):
                with gr.Row():
                    with gr.Column():
                        plot4 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Upload Time"):
                with gr.Row():
                    with gr.Column():
                        plot5 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Feedback Type"):
                with gr.Row():
                    with gr.Column():
                        plot6 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
            with gr.Tab("Plot 7"):
                with gr.Row():
                    with gr.Column():
                        plot7 = gr.Plot()
                        load_button = gr.Button("Refresh Dashboard")
                        load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])
        qna.load(fn=gradio_interface, outputs=[plot1, plot2, plot2bis, plot3, plot4, plot5, plot6, plot7])


    return qna
