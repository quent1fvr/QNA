from src.control.control import Chatbot
from src.data_processing.data_analyzer import DataAnalyzer
from src.data_processing.log_parser import LogParser
import gradio as gr
from chromadb.utils import embedding_functions
import os
import time
import logging
import gradio as gr
import json

class GradioInterface:
    def __init__(self, ctrl, config, log_file_path):
        self.ctrl = ctrl
        self.config = config
        self.log_parser = LogParser(log_file_path)
        self.data_analyzer = None
        self._setup_data()
        self.theme = gr.themes.Soft(
            primary_hue="orange",
            secondary_hue="blue",
            neutral_hue="stone",
        )

    def _setup_data(self):
        df_logs = self.log_parser.read_and_parse_logs()
        df_logs_history = self.log_parser.read_and_parse_history_logs()
        df_feedback = self.log_parser.read_and_parse_feedback_logs()
        df_thumb_feedback = df_feedback[df_feedback['feedback_type'] == 'Thumb Feedback']
        df_manual_feedback = df_feedback[df_feedback['feedback_type'] == 'Manual Feedback']
        self.data_analyzer = DataAnalyzer(df_logs, df_logs_history, df_feedback, df_thumb_feedback, df_manual_feedback)

    def generate_plots(self):
        fig1 = self.data_analyzer.plot_activity_over_time()
        fig2 = self.data_analyzer.plot_query_response_time()
        fig3 = self.data_analyzer.plot_success_vs_failure_rate()
        fig4 = self.data_analyzer.plot_activity_frequency_by_collection()
        fig5 = self.data_analyzer.plot_upload_times_analysis()
        fig7 = self.data_analyzer.query_answer_history()
        fig9 = self.data_analyzer.plot_feedback_analysis()
        fig10 = self.data_analyzer.plot_thumb_feedback_analysis()
        
        return fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10
    
    def refresh_plots(self):
        updated_plots = self.generate_plots()
        return updated_plots


    def gradio_interface(self):
        fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10 = self.generate_plots()
        return fig1, fig2, fig3, fig4, fig5, fig7, fig9, fig10  # Return the interface components



    def run(self, ctrl: Chatbot, config: {}):
        open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'],model_name="text-embedding-ada-002")
        print(ctrl.client_db.list_collections())
        ctrl.retriever.collection = ctrl.client_db.get_collection("tet", embedding_function=open_ai_embedding)

        with gr.Blocks(theme=self.theme) as qna:
            gr.Markdown("## Administrator view")
            with gr.Tabs() as tabs:
                with gr.Tab("Admin view "):
                    with gr.Row():
                        with gr.Column(scale=3):
                            add_collection_btn = gr.Textbox(interactive=True, label=" Add collection", visible=False)

                            collections_list = gr.Radio(choices=[a.name for a in ctrl.client_db.list_collections()],
                                label="Current collections in the database",
                                visible=False,
                            )
                            delete_database_btn = gr.Button("Delete current collection", visible=False) 

                            metadata_docs_update = gr.CheckboxGroup(choices=set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]),
                                label="Documents in the collection", interactive = True 
                            )

                            with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/ressources/dict_of_folders.json', 'r') as file:
                                Dict_of_folders = json.load(file)
                                print(Dict_of_folders)                               
                                
                            folder_name_input = gr.Textbox(interactive=True, label="Add a folder", visible=True)
                            Folder_button = gr.Button(value = "Submit")
                            Folders_list=[]

                            Folders_list = gr.Radio(
                                choices=[folder for folder in Dict_of_folders["Name"]],
                                label="Folders list",
                                interactive=True
                            )

                            Documents_in_folder = gr.CheckboxGroup(choices=[], value= "Files in folder")
                            delete_folder_button = gr.Button(value = "Delete folder")
                            delete_file_in_folder_button = gr.Button(value = "Delete file")
                        with gr.Column(scale=6):
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
                            # collections_list = gr.Dropdown(choices=[a.name for a in ctrl.client_db.list_collections()],
                            #     label="Select a collection for your document ",
                            #     visible=True
                            # )
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

                        open_ai_embedding = embedding_functions.OpenAIEmbeddingFunction(api_key=os.environ['OPENAI_API_KEY'],model_name="text-embedding-ada-002"
        )
                        with gr.Column(scale=3):    
                            pass
                            
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
                                delete_database_btn: gr.update(visible=False),
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
                            delete_database_btn: gr.update(visible=False),
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
                        metadata_docs = set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']])
                        #metadata_doc = ctrl.retriever.collection.get()['metadatas']['doc']
                        print("Total records in the collection: ", metadata_docs)
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
                            actual_page_start: gr.update(visible=True),
                            page_start_warning: gr.update(visible=True),
                            metadata_docs_update:gr.update(choices=set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']]),interactive = True )
                        }
                    def doc_in_collection(collection_name):
                        metadata_docs = set([item['doc'] for item in ctrl.retriever.collection.get()['metadatas']])
                        update = {
                            metadata_docs_update:gr.update(choices=list(metadata_docs),interactive=True),

                        }
                        return update
                    
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
                        
                    def add_collection(collection_name):
                        ctrl.retriever.collection = ctrl.client_db.create_collection(collection_name, embedding_function=embedding_functions.OpenAIEmbeddingFunction(
                        api_key=os.environ['OPENAI_API_KEY'],
                        model_name="text-embedding-ada-002"))
                        return {
                            add_collection_btn: gr.update(visible=True, value=""),
                            delete_database_btn: gr.update(visible=False),
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

                    
                    def create_folder_fctn(docs, folder_name): 
                        Dict_of_folders["Name"].append(folder_name)
                        Dict_of_folders["Files"].append(docs)
                        with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/ressources/dict_of_folders.json', 'w') as file:
                            json.dump(Dict_of_folders, file)

                        gr.Info("Folder created")
                        
                        return{
                        Folders_list: gr.update(choices=[folder for folder in Dict_of_folders["Name"]],label="Folder list", interactive=True)
                        }
                    def delete_folder_fctn(Folders_list_): 
                        folder_name = Folders_list_
                        Dict_of_folders["Files"].remove([files for name, files in zip(Dict_of_folders["Name"], Dict_of_folders["Files"]) if name == folder_name][0])
                        Dict_of_folders["Name"].remove(folder_name)
                        with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/ressources/dict_of_folders.json', 'w') as file:
                            json.dump(Dict_of_folders, file)

                        gr.Info("Folder deleted")
                        
                        return{
                        Folders_list: gr.update(choices=[folder for folder in Dict_of_folders["Name"]],label="Folder list", interactive=True)
                        }

                    def delete_file_in_folder_fctn(folder_name, doc_name):
                        with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/ressources/dict_of_folders.json', 'r') as file:
                            Dict_of_folders = json.load(file)
                            print("Loaded dict_of_folders:", Dict_of_folders)

                        if folder_name in Dict_of_folders["Name"]:
                            folder_index = Dict_of_folders["Name"].index(folder_name)
                            print("Found folder_index:", folder_index)
                            
                            if doc_name[0] in Dict_of_folders["Files"][folder_index]:
                                
                                Dict_of_folders["Files"][folder_index].remove(doc_name[0])
                                print("Removed doc_name:", doc_name)
                                with open('/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/ressources/dict_of_folders.json', 'w') as file:
                                    json.dump(Dict_of_folders, file)
                                    print("Updated dict_of_folders:", Dict_of_folders)
                                gr.Info("Document deleted")
                                return {
                                    Documents_in_folder: gr.update(
                                        choices=Dict_of_folders["Files"][folder_index]
                                    )
                                }
                            else:
                                return "Document not found in the specified folder"
                        else:
                            return "Folder not found"   
                        
                    def update_documents_in_folder(folder_name):
                        files_for_folder = [files for name, files in zip(Dict_of_folders["Name"], Dict_of_folders["Files"]) if name == folder_name][0]
                        print("update doc started")
                        return{
                        Documents_in_folder:gr.update(
                            choices=files_for_folder,
                            label="Files in selected folder",
                            interactive=True
                        ) 
                        }
                        
                    Folders_list.input(update_documents_in_folder, inputs=[Folders_list], outputs=[Documents_in_folder])      
                    upload_another_doc_btn.click(input_file_clear,
                                    inputs=None,
                                    outputs=[collections_list, page_start_warning, actual_page_start, input_doc_comp, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, delete_database_btn,upload_another_doc_btn, source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])

                    delete_database_btn.click(delete_curr_database,
                                    inputs=None,
                                    outputs=[page_start_warning, actual_page_start, delete_database_btn, input_doc_comp, input_text_comp, input_example_comp, clear_btn, collections_list, include_images_btn, histo_text_comp, upload_another_doc_btn])


                    add_collection_btn.submit(add_collection,
                                    inputs=[add_collection_btn],
                                    outputs=[add_collection_btn,page_start_warning, actual_page_start, delete_database_btn, input_doc_comp, input_text_comp, input_example_comp, clear_btn, collections_list, include_images_btn, histo_text_comp, upload_another_doc_btn])
                                                               
                    collections_list.input(change_collection,
                                    inputs=[collections_list],
                                    outputs=[actual_page_start, page_start_warning, collections_list, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, input_doc_comp, delete_database_btn,upload_another_doc_btn,metadata_docs_update])


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
                    Folder_button.click(create_folder_fctn , inputs=[metadata_docs_update,folder_name_input], outputs = [Folders_list])
                    delete_folder_button.click(delete_folder_fctn , inputs=[Folders_list], outputs = [Folders_list])
                    delete_file_in_folder_button.click(delete_file_in_folder_fctn , inputs=[Folders_list,Documents_in_folder], outputs = [Documents_in_folder])
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
                            download_button = gr.File(label="Download Excel", value=self.data_analyzer.dataframe_to_excel(self.data_analyzer.df_logs_history))
                            refresh_button = gr.Button("Refresh Plot")
                            #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       

                    with gr.Row():
                        plot7 = gr.Plot()
                            #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot6])
                                                      
                with gr.Tab("thumbs Feedbacks History"):
                    with gr.Row():
                        with gr.Column(scale=0):  # Small column for the download button
                            refresh_button = gr.Button("Refresh Plot")
                            #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
                            download_button = gr.File(label="Download Excel", value=self.data_analyzer.dataframe_to_excel(self.data_analyzer.df_thumb_feedback))
                    with gr.Row():
                        plot10 = gr.Plot()
                  
                                              
                with gr.Tab("Manual Feedbacks"):
                    with gr.Row():
                        with gr.Column(scale=0):  # Small column for the download button
                            refresh_button = gr.Button("Refresh Plot")
                            #load_button.click(fn=gradio_interface, inputs=[], outputs=[plot1, plot2, plot3, plot4, plot5, plot7,plot8,plot9])                       
                            download_button = gr.File(label="Download Excel", value=self.data_analyzer.dataframe_to_excel(self.data_analyzer.df_manual_feedback))
                    with gr.Row():
                        plot9 = gr.Plot()
            refresh_button.click(fn=self.refresh_plots, inputs=[], outputs=[plot1,plot2,plot3,plot4,plot5,plot7,plot9,plot10])
            
            qna.load(fn=self.gradio_interface, outputs=[plot1, plot2, plot3, plot4, plot5,plot7,plot9,plot10])


        return qna
