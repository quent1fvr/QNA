from src.model.container import Container
from src.tools.index_creation import set_indexes
from src.Readers.reader_word import WordReader
from src.Readers.readers_pdf import Reader, Reader_illumio
from src.Readers.reader_html import Reader_HTML
from src.Readers.reader_excel import ReaderExcel
from src.model.paragraph import Paragraph


class Doc:

    def __init__(self, path='', include_images=True, actual_first_page=1):

        self.title = self.get_title(path)
        self.extension = self.title.split('.')[-1]
        self.id_ = id(self)
        self.path = path
        paragraphs = []
        if self.extension == 'docx':
            paragraphs = WordReader(path).paragraphs
        elif self.extension == 'pdf':
            if "ilumio" in self.title:
                paragraphs = Reader_illumio(path).paragraphs
            else:
                paragraphs = Reader(path, actual_first_page, include_images).paragraphs
        elif self.extension == 'html':
            paragraphs = Reader_HTML(path).paragraphs
        
        else :
            paragraphs = ReaderExcel(path).paragraphs
        self.container = Container(paragraphs, father=self, title=self.set_first_container_title(self.title.split(".")[0],self.extension))
        print(self.id_)
        set_indexes(self.container)
        self.blocks = self.get_blocks()


    def get_title(self,path) -> str:
        if '/' not in path and '\\' not in path:
            res = path
        if '/' in path:
            res = path.split('/')[-1]
        if '\\' in path:
            res = path.split('\\')[-1]
        return res 

    @property
    def structure(self):
        return self.container.structure

    def get_blocks(self):
        def from_list_to_str(index_list):
            index_str = str(index_list[0])
            for el in index_list[1:]:
                index_str += '.' + str(el)
            return index_str

        blocks = self.container.blocks
        for block in blocks:
            block.doc = self.title
            block.index = from_list_to_str(block.index)
        return blocks
    
    def set_first_container_title(self,title,extension) -> Paragraph:
        if extension == 'pdf':
            return Paragraph(text=title,font_style='title0',id_=0,page_id=0)
        elif extension == 'docx':
            return Paragraph(text=title,font_style='title0',id_=0,page_id=1)
        else:
            return Paragraph(text=title,font_style='h0',id_=0,page_id=1)
