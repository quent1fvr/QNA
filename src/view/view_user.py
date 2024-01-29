import gradio as gr
from src.control.control import Chatbot
import os
from src.tools.embedding_factory import create_embedding_model
from config import use_open_source_embeddings
import logging 
import time
import json
from chromadb.utils import embedding_functions
theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="blue",
    neutral_hue="stone",
)
def run(ctrl: Chatbot, config: {}):
    with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/ressources/dict_of_folders.json', 'r') as file:
        Dict_of_folders = json.load(file)
        open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'],model_name="text-embedding-ada-002")

        ctrl.retriever.collection = ctrl.client_db.get_collection("tet", embedding_function=open_ai_embedding)

    with gr.Blocks(theme=theme) as qna:
        with gr.Row():
            with gr.Column(scale=1, elem_id="margin-top-row"):
                
                expert_mode = gr.Checkbox(label="Expert mode", value=False, interactive=True,)

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
                    visible=False,
                    info="Choose a collection to query.",
                    elem_classes="margin-top-row",
                )

                metadata_docs_update = gr.Dropdown(choices=set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]),
                    label="Documents in the collection", interactive = True, visible=False
                )
                
                documents_or_folder = gr.Radio(choices=["Documents","Folder"],label="Documents or Folder",visible= False,interactive=True)
                
                
                Folders_list = gr.CheckboxGroup(
                    choices=[folder for folder in Dict_of_folders["Name"]],
                    label="Folder list",
                    interactive=True,
                    visible= False
                    
                ) 
            
                Documents_in_folder = gr.CheckboxGroup(choices=[],label = "Files in Folder",visible= False, interactive = True)
                                                      
                List_documents= gr.CheckboxGroup(choices=set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]),label = "List of Documents",visible=False , interactive = True)
          
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


                clear_btn = gr.Button("Clear Chat", visible=True)
                positive_button = gr.Button("👍", visible=False)
                negative_button = gr.Button("👎", visible=False)
                feedback_input = gr.Textbox(interactive=True, label=" Manual Feedback")   

                input_example_comp = gr.Radio(
                    label="Examples",
                    choices=config['examples'].values(),
                    value="",
                    visible=False,
                )
                


            # Another empty column for centering
            with gr.Column(scale=2):
                
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
                    input_example_comp: gr.update(visible=False),
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

        def input_text_fn2(input_text_, histo_text_, Folders_list_, Document_or_folder_, Documents_):
            # Store the current query
            current_query = input_text_
            
            answer, sources = ctrl.get_response(query=current_query, histo=histo_text_, folder = Folders_list_, doc_or_folder =Document_or_folder_ , documents = Documents_) 
            
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
                input_example_comp: gr.update(value='', visible=False),
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
                metadata_docs_update:gr.update(choices=set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]))
  
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


        selected_folders = []  # Initialize a list to keep track of selected folders

        def update_documents_in_folder(folder_names):
            global selected_folders  # Use the global variable to keep track of selected folders
            # Update the list of selected folders
            selected_folders = folder_names
            files_for_folders = [files for name, files in zip(Dict_of_folders["Name"], Dict_of_folders["Files"]) if name in selected_folders]
            if files_for_folders:
                print("update doc started")
                return {
                    Documents_in_folder: gr.update(
                        choices=files_for_folders[0],  # Assuming you want to update with the files of the first selected folder
                        label="Files in the selected folder",
                        interactive=False
                    ) 
                }
            else:
                return {
                    Documents_in_folder: gr.update(
                        choices=[],  # Assuming you want to update with the files of the first selected folder
                        label="Files in the selected folder",
                        interactive=False
                    ) 
                }
                
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

        def documents_or_folder_choice(choice):
            if choice == 'Documents':
                return {
                    Folders_list: gr.update(visible=False),
                    Documents_in_folder: gr.update(visible=False),
                    List_documents: gr.update(visible=True)
                }
            else:
                return {
                    Folders_list: gr.update(visible=True),
                    Documents_in_folder: gr.update(visible=True),
                    List_documents: gr.update(visible=False)

                }
                
                
                
        def expert_mode_triggered(expert_mode_):
            if expert_mode_:  # If expert mode is selected
                update = {
                    collections_list: gr.update(visible=False), 
                    expert_mode: gr.update(visible=True),
                    Folders_list: gr.update(visible=False),
                    Documents_in_folder: gr.update(visible=False),
                    metadata_docs_update:gr.update(visible = True), 
                    documents_or_folder: gr.update(visible=True),
                    
                }
            else:  # If expert mode is not selected
                update = {
                    collections_list: gr.update(visible=False), 
                    expert_mode: gr.update(visible=True),
                    Folders_list: gr.update(visible=False),
                    Documents_in_folder: gr.update(visible=False),
                    metadata_docs_update:gr.update(visible = False),
                    documents_or_folder: gr.update(visible=False)

                }
            return update
        
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

        Folders_list.input(update_documents_in_folder, inputs=[Folders_list], outputs=[Documents_in_folder])      

        
        documents_or_folder.input(documents_or_folder_choice, inputs=[documents_or_folder], outputs=[Folders_list, Documents_in_folder,List_documents])
        collections_list.input(change_collection,
                        inputs=[collections_list],
                        outputs=[intro_text, collections_list, input_text_comp, input_example_comp, clear_btn, histo_text_comp, metadata_docs_update])


        expert_mode.input(expert_mode_triggered, inputs=[expert_mode],outputs=[expert_mode,collections_list ,expert_mode,Folders_list,Documents_in_folder, metadata_docs_update,documents_or_folder])
        
        input_text_comp \
            .submit(input_text_fn1,
                    inputs=[input_text_comp, histo_text_comp],
                    outputs=[intro_text,histo_text_comp, input_example_comp,
                             source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3],positive_button, negative_button])\
            .then(input_text_fn2,
                  inputs=[input_text_comp, histo_text_comp, Folders_list, documents_or_folder, List_documents],
                  outputs=[intro_text,input_text_comp, histo_text_comp,Folders_list,documents_or_folder, List_documents,
                           source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3],positive_button, negative_button])\
                        
        input_example_comp \
            .input(input_example_fn,
                   inputs=[input_example_comp, histo_text_comp],
                   outputs=[intro_text,input_text_comp, histo_text_comp, input_example_comp,
                            source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
            .then(input_text_fn2,
                  inputs=[input_text_comp, histo_text_comp,Folders_list,documents_or_folder,List_documents],
                  outputs=[intro_text,input_text_comp, histo_text_comp,
                           source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])
        clear_btn.click(clear_fn,
                        inputs=None,
                        outputs=[input_text_comp, histo_text_comp, input_example_comp,intro_text,
                                 source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])




    return qna