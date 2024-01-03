import gradio as gr
from src.control.control import Chatbot
from chromadb.utils import embedding_functions
import os
import logging 
import time

def run(ctrl: Chatbot, config: {}):
    with gr.Blocks() as qna:
        with gr.Row():
            with gr.Column():
                pass

            with gr.Column(scale=10):
                gr.Markdown(config['title'])
                page_start_warning = gr.Markdown("<center>⚠️ If your document starts with a front cover and/or a table of contents, please enter the page number of the ⚠️ first page with real content.<center/>")
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
                delete_database_btn = gr.Button("Delete current collection", visible=False)
                
            # with gr.Column(scale=7):
            #     collections_list = gr.Radio(choices=[a.name for a in ctrl.client_db.list_collections()],
            #         label="Current collections in the database",
            #         visible=True,
            #         info="Choose a collection to query."
            #     )
            #     delete_database_btn = gr.Button("Delete current collection", visible=False)
                
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
                    clear_btn: gr.update(visible=True),
                    include_images_btn: gr.update(visible=False,value=include_images_),
                    delete_database_btn: gr.update(visible=True),
                    upload_another_doc_btn: gr.update(visible=True),
                    collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()],value=ctrl.retriever.collection.name),
                    page_start_warning: gr.update(visible=False),
                    actual_page_start: gr.update(visible=False),
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
                upload_another_doc_btn: gr.update(visible=True),
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
                input_doc_comp: gr.update(visible=False,value=None),
                input_text_comp: gr.update(visible=True, value=''),
                input_example_comp: gr.update(visible=True),
                clear_btn: gr.update(visible=True),
                collections_list: gr.update(choices=[a.name for a in ctrl.client_db.list_collections()]),
                include_images_btn: gr.update(visible=False),
                histo_text_comp: gr.update(visible=False, value=''),
                upload_another_doc_btn: gr.update(visible=True),
                actual_page_start: gr.update(visible=False),
                page_start_warning: gr.update(visible=False),
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

    return qna
