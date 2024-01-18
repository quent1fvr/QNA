import gradio as gr
from src.control.control import Chatbot
import os
from src.tools.embedding_factory import create_embedding_model
from config import use_open_source_embeddings
import logging 
import time
theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="blue",
    neutral_hue="stone",
)
def run(ctrl: Chatbot, config: {}):


    with gr.Blocks(theme=theme) as qna:
        with gr.Row():
            with gr.Column(scale=2, elem_id="margin-top-row"):
                collections_listB = gr.Dropdown(
                    choices=[a.name for a in ctrl.client_db.list_collections()],
                    label="Current collections in the database",
                    value=ctrl.client_db.list_collections()[0].name if ctrl.client_db.list_collections() else None,
                    visible=False,
                    info="Choose a collection to query.",
                    elem_classes="margin-top-row",
                )                    
                
                collections_list = gr.Dropdown(
                    choices=[a.name for a in ctrl.client_db.list_collections()],
                    label="Current collections in the database",
                    value=ctrl.client_db.list_collections()[0].name if ctrl.client_db.list_collections() else None,
                    visible=True,
                    info="Choose a collection to query.",
                    elem_classes="margin-top-row",
                )
                positive_button = gr.Button("👍", visible=False)
                negative_button = gr.Button("👎", visible=False)
                feedback_input = gr.Textbox(interactive=True, label=" Manual Feedback")             
            with gr.Column(scale=6):
                 
                gr.Markdown(config['title'])
                intro_text = gr.Markdown(" Ask questions on any PDF, Word or HTML document.", visible=True)


                histo_text_comp = gr.Chatbot(
                    visible=False,
                    value=[],
                )
                
                input_text_comp = gr.Textbox(
                    label="",
                    lines=1,
                    visible=True,
                    max_lines=3,
                    interactive=True,
                    placeholder="Posez votre question ici",
                )


                clear_btn = gr.Button("Clear Chat", visible=False)

                input_example_comp = gr.Radio(
                    label="Examples",
                    choices=config['examples'].values(),
                    value="",
                    visible=True,
                )
                
                source_text_comp = []
                for i in range(4):
                    source_text_comp.append(gr.Textbox(
                        lines=4,
                        max_lines=4,
                        interactive=False,
                        visible=False,
                    ))
                    

            embedding_model = create_embedding_model(use_open_source_embeddings)
                
            collections = ctrl.client_db.list_collections()
            # Determine the default collection name
            default_collection_name = collections[0].name if collections else None

            # Instantiate the default collection outside the change_collection function
            if default_collection_name:
                ctrl.retriever.collection = ctrl.client_db.get_collection(
                    default_collection_name, embedding_function=embedding_model)
                            
                        


                

        
        def input_doc_fn(input_doc_, include_images_, actual_page_start_,collections_list_):
            start_time = time.time()
            result = ctrl.upload_doc(input_doc_,include_images_, actual_page_start_,collections_list_)
            end_time = time.time()
            temps_execution = end_time - start_time


            if result == True:
                return {
                    input_text_comp: gr.update(visible=True),
                    input_example_comp: gr.update(visible=True),
                    clear_btn: gr.update(visible=True),
                    collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()],value=ctrl.retriever.collection.name),
                    intro_text: gr.update(visible=False),

                }
            else:
                gr.Warning("File extension not supported. Only .docx, .pdf and .html are supported.")
                return {
                    input_text_comp: gr.update(visible=False),
                    input_example_comp: gr.update(visible=False),
                    clear_btn: gr.update(visible=False),
                    intro_text: gr.update(visible=False)

                }
            

        def input_file_clear():
            update_ = {
                clear_btn: gr.update(visible=False),
                input_text_comp: gr.update(value='', visible=False),
                histo_text_comp: gr.update(value='', visible=False),
                input_example_comp: gr.update(value='', visible=False),
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
                intro_text: gr.update(visible=False),
                positive_button: gr.update(visible=True),
                negative_button: gr.update(visible=True)

            }
            for i in range(4):
                update_[source_text_comp[i]] = gr.update(visible=False)
            return update_

        def input_text_fn2(input_text_, histo_text_):
            # Store the current query
            current_query = input_text_
            answer, sources = ctrl.get_response(query=current_query, histo=histo_text_)
            
            # Update the last entry in the history with the current query and the answer
            histo_text_[-1] = (current_query, answer)

            update_ = {
                histo_text_comp: gr.update(value=histo_text_),
                input_text_comp: gr.update(value=''),
                intro_text: gr.update(visible=False),
                positive_button: gr.update(visible=True),
                negative_button: gr.update(visible=True),
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
                intro_text: gr.update(visible=False),


            }
            for i in range(4):
                update_[source_text_comp[i]] = gr.update(visible=False)
            return update_

        def clear_fn():
            update_ = {
                input_text_comp: gr.update(value=''),
                histo_text_comp: gr.update(value='', visible=False),
                input_example_comp: gr.update(value='', visible=True),
                intro_text: gr.update(visible=False),

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
            ctrl.retriever.collection = ctrl.client_db.get_collection(collection_name, embedding_function=embedding_model)
            return {
                input_text_comp: gr.update(visible=True, value=''),
                input_example_comp: gr.update(visible=True),
                clear_btn: gr.update(visible=True),
                collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                histo_text_comp: gr.update(visible=False, value=''),
                intro_text: gr.update(visible=False),             
            }

        def delete_curr_database():
            ctrl.client_db.delete_collection(ctrl.retriever.collection.name)
            gr.Info(f"Collection {ctrl.retriever.collection.name} deleted from the database")
            return {
                input_text_comp: gr.update(visible=False, value=''),
                input_example_comp: gr.update(visible=False),
                clear_btn: gr.update(visible=False),
                collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                histo_text_comp: gr.update(visible=False, value=''),
                intro_text: gr.update(visible=False),

            }

            
        # Modified callback for manual feedback
        def manual_feedback_callback(feedback_text):
            logging.info(f"Feedback: {feedback_text} ", extra={'category': 'Manual Feedback', 'elapsed_time': 0})
            gr.Info("Feedback sent successfully")

            # Return an empty string to clear the Textbox
            return ""
        
        def get_sources_contents():
            # Extract the visible sources' contents from the source_text_comp array
            sources_contents = [source.value for source in source_text_comp]  
            return sources_contents

        def callback_positive_and_log(feedback_type, histo_text_):
            query = histo_text_[-1][0] if histo_text_ else ""  # Retrieve the last query
            answer = histo_text_[-1][1] if histo_text_ else None
            sources_contents = get_sources_contents()
            logging.info(f"Feedback: {feedback_type}, Collection: {ctrl.retriever.collection.name}, Query: {query}, Answer: {answer}, Sources: {sources_contents}", extra={'category': 'Thumb Feedback', 'elapsed_time': 0})

        # Similar for callback_negative_and_log

        def callback_negative_and_log(feedback_type, histo_text_):
            query = histo_text_[-1][0] if histo_text_ else ""  # Retrieve the last query
            answer = histo_text_[-1][1] if histo_text_ else None
            sources_contents = get_sources_contents()
            logging.info(f"Feedback: {feedback_type}, Collection: {ctrl.retriever.collection.name}, Query: {query}, Answer: {answer}, Sources: {sources_contents}", extra={'category': 'Thumb Feedback', 'elapsed_time': 0})

        positive_button.click(
            lambda histo_text_comp: callback_positive_and_log("Positive", histo_text_comp),
            inputs=[histo_text_comp],
            outputs=None,
            preprocess=False
        )

        negative_button.click(
            lambda histo_text_comp: callback_negative_and_log("Negative", histo_text_comp),
            inputs=[histo_text_comp],
            outputs=None,
            preprocess=False
        )


        feedback_input.submit(manual_feedback_callback, [feedback_input],outputs=[feedback_input], preprocess=False)


        collections_list.input(change_collection,
                        inputs=[collections_list],
                        outputs=[intro_text, collections_list, input_text_comp, input_example_comp, clear_btn, histo_text_comp])


        
        input_text_comp \
            .submit(input_text_fn1,
                    inputs=[input_text_comp, histo_text_comp],
                    outputs=[intro_text,histo_text_comp, input_example_comp,
                             source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3],positive_button, negative_button])\
            .then(input_text_fn2,
                  inputs=[input_text_comp, histo_text_comp],
                  outputs=[intro_text,input_text_comp, histo_text_comp,
                           source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3],positive_button, negative_button])\
                        
        input_example_comp \
            .input(input_example_fn,
                   inputs=[input_example_comp, histo_text_comp],
                   outputs=[intro_text,input_text_comp, histo_text_comp, input_example_comp,
                            source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
            .then(input_text_fn2,
                  inputs=[input_text_comp, histo_text_comp],
                  outputs=[intro_text,input_text_comp, histo_text_comp,
                           source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])
        clear_btn.click(clear_fn,
                        inputs=None,
                        outputs=[input_text_comp, histo_text_comp, input_example_comp,
                                 source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])





    return qna
