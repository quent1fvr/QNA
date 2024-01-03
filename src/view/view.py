import gradio as gr
from src.control.control import Chatbot
from chromadb.utils import embedding_functions
import os
from src.tools.embedding_factory import create_embedding_model
from config import use_open_source_embeddings

theme = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="blue",
    neutral_hue="stone",
)
def run(ctrl: Chatbot, config: {}):
    callback_positive = gr.CSVLogger()
    callback_negative = gr.CSVLogger()
    callback_manual= gr.CSVLogger()

    with gr.Blocks(theme=theme) as qna:
        with gr.Row():
            with gr.Column():
                pass

                # with gr.Column(scale=7):
                #     collections_list = gr.Radio(
                        
                #         choices=ctrl.list_models("/Users/quent1/Documents/Hexamind/ILLUMIO/Illumio3011/Chatbot_llama2_questions/src/model/opensource_models"),
                        
                #         label="Current collections in the database",
                #         visible=True,
                #         info="Choose a model to use."
                #     )
                with gr.Column(scale=7):
                    positive_button = gr.Button("👍")
                    negative_button = gr.Button("👎")
                    feedback_input = gr.Textbox(interactive=True, label=" Manual Feedback")

                delete_database_btn = gr.Button("Delete current collection", visible=False)
            with gr.Column(scale=10):
                gr.Markdown(config['title'])
                intro_text = gr.Markdown(" <center> This application allows you to upload documents and ask questions based on their content. The system will analyze the text, including any text in images for PDFs, and provide answers. Start by uploading a document and then enter your questions. Othewise An example is already included. which let you free to ask questions on the book Le Petit Prince. Some examples of queries are also provided below.", visible=True)

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

            embedding_model = create_embedding_model(use_open_source_embeddings)

            with gr.Column(scale=7):
                collections_list = gr.Radio(choices=[a.name for a in ctrl.client_db.list_collections()],
                    label="Current collections in the database",
                    visible=True,
                    info="Choose a collection to query."
                )
                delete_database_btn = gr.Button("Delete current collection", visible=False)
                
                
            


                

        
        def input_doc_fn(input_doc_, include_images_, actual_page_start_):
            result = ctrl.upload_doc(input_doc_,include_images_, actual_page_start_)
            if result == True:
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
                    intro_text: gr.update(visible=False),

                }
            else:
                gr.Warning("File extension not supported. Only .docx, .pdf and .html are supported.")
                return {
                    input_doc_comp: gr.update(visible=True),
                    input_text_comp: gr.update(visible=False),
                    input_example_comp: gr.update(visible=False),
                    clear_btn: gr.update(visible=False),
                    include_images_btn: gr.update(visible=True,value=include_images_),
                    page_start_warning: gr.update(visible=True),
                    actual_page_start: gr.update(visible=True, value=1),
                    intro_text: gr.update(visible=False)

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
                intro_text: gr.update(visible=False),

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
                intro_text: gr.update(visible=False),

                

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
                upload_another_doc_btn: gr.update(visible=True),
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
                intro_text: gr.update(visible=False),             
            }

        def delete_curr_database():
            ctrl.client_db.delete_collection(ctrl.retriever.collection.name)
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
                intro_text: gr.update(visible=False),

            }

            
        # Modified callback for manual feedback
        def manual_feedback_callback(*args):
            callback_manual.flag(args)
            
            # Return an empty string to clear the Textbox
            return ""

            
        callback_positive.setup([input_text_comp, histo_text_comp], "Positive Feedbacks")
        callback_negative.setup([input_text_comp, histo_text_comp], "Negative Feedbacks")
        callback_manual.setup([input_text_comp, histo_text_comp, feedback_input], "Manual Feedback")

        positive_button.click(lambda *args: callback_positive.flag(args, ), [input_text_comp, histo_text_comp], None, preprocess=False)
        negative_button.click(lambda *args: callback_negative.flag(args, flag_option = "Incorrect answer"), [input_text_comp, histo_text_comp], None, preprocess=False)
        
        feedback_input.submit(manual_feedback_callback, [input_text_comp, histo_text_comp, feedback_input],outputs=[feedback_input], preprocess=False)



        upload_another_doc_btn.click(input_file_clear,
                        inputs=None,
                        outputs=[collections_list, page_start_warning, actual_page_start, input_doc_comp, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, delete_database_btn,upload_another_doc_btn, source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])


        delete_database_btn.click(delete_curr_database,
                        inputs=None,
                        outputs=[intro_text, page_start_warning, actual_page_start, delete_database_btn, input_doc_comp, input_text_comp, input_example_comp, clear_btn, collections_list, include_images_btn, histo_text_comp, upload_another_doc_btn])

        collections_list.input(change_collection,
                        inputs=[collections_list],
                        outputs=[intro_text, actual_page_start, page_start_warning, collections_list, input_text_comp, input_example_comp, clear_btn, include_images_btn, histo_text_comp, input_doc_comp, delete_database_btn,upload_another_doc_btn])

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
                    outputs=[intro_text,histo_text_comp, input_example_comp,
                             source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])\
            .then(input_text_fn2,
                  inputs=[input_text_comp, histo_text_comp],
                  outputs=[intro_text,input_text_comp, histo_text_comp,
                           source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])
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
                        outputs=[input_text_comp, histo_text_comp, input_example_comp,upload_another_doc_btn,
                                 source_text_comp[0], source_text_comp[1], source_text_comp[2], source_text_comp[3]])





    return qna
