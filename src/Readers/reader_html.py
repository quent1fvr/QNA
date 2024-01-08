from pyquery import PyQuery as pq
from src.model.paragraph import Paragraph
from bs4 import BeautifulSoup
from src.tools.table_converter import table_converter

class Reader_HTML:
    def __init__(self, path):
        self.path = path
        self.paragraphs = self.read_html_2(path)

    #without beautifulsoup but doesn't work fine
    def read_html(self, path):
        with open(path, 'r') as html_file:
            doc = pq(html_file.read())

        # Remove script and style elements
        doc('script').remove()
        doc('style').remove()

        paragraphs = []
        for index, elem in enumerate(doc('*')):
            # Check if the element is a leaf (does not contain other elements)
            if not pq(elem).find('*'):
                text = pq(elem).text().strip()
                if text:
                    paragraphs.append(Paragraph(text=text, font_style=elem.tag, id_ = index, page_id=1))
        return paragraphs

    #with beautifulsoup
    def read_html_2(self,path):
        HTMLFile = open(path, "r") 
        # Reading the file 
        reader = HTMLFile.read() 
        paragraphs = []
        # Creating a BeautifulSoup object and specifying the parser 
        S = BeautifulSoup(reader, 'html.parser') 
        for tag in S(['style', 'script', 'footer', 'header', 'nav', 'aside', 'form']):
            tag.decompose()

        # Get all elements that do not contain other elements
        leaf_elements = [elem for elem in S.body.descendants if elem.name is not None and not elem.find_all()]
        paragraphs = []
        for index, elem in enumerate(leaf_elements):
            text = elem.get_text(strip=True, separator='\n')
            if text:
                p = Paragraph(text=text, font_style=elem.name, id_ = index, page_id=1)
                paragraphs.append(p)
        paragraphs = self.concatenate_paragraphs_with_same_font_style(paragraphs)
        paragraphs = [p.rearrange_paragraph() for p in paragraphs]
        return paragraphs
    
    def concatenate_paragraphs_with_same_font_style(self,paragraphs: [Paragraph]):
        i = 0
        while i < len(paragraphs)-1:
            if paragraphs[i].font_style == "th":
                paragraphs = self.create_table(paragraphs,i)
                i += 1
            elif paragraphs[i].font_style == "li":
                paragraphs,i = self.create_list(paragraphs,i)
                i += 1
            elif paragraphs[i].font_style == paragraphs[i+1].font_style:
                paragraphs[i].text += "\n" + paragraphs[i+1].text
                paragraphs.pop(i+1)
            else:
                i += 1
        return paragraphs


    def create_table(self, paragraphs, i: int):
        table = []
        titles = []
        content = []
        while i < len(paragraphs) and paragraphs[i].font_style == "th":
            titles.append(paragraphs[i].text)
            paragraphs.pop(i)
        table.append(titles)
        length = len(titles)
        temp = 0
        while i < len(paragraphs) and paragraphs[i].font_style == "td":
            if temp == length:
                temp = 0
                content.append(paragraphs[i].text)
                table.append(content)
                content = []
            else:
                content.append(paragraphs[i].text)
                paragraphs.pop(i)
                temp += 1
        table.append(content)
        paragraphs.insert(i,Paragraph(table_converter(table),font_style="table",id_=i,page_id=1))
        return paragraphs
    
    def create_list(self, paragraphs, i: int):
        list_content = []
        while i < len(paragraphs) and paragraphs[i].font_style in ["ul", "ol", "li"]:
            if paragraphs[i].font_style == "li":
                list_content.append(paragraphs[i].text)
                paragraphs.pop(i)
            elif paragraphs[i].font_style in ["ul", "ol"]:
                sublist, i = self.create_list(paragraphs, i+1)
                list_content.append(sublist)
            else:
                i += 1
        list_paragraph = Paragraph(text=self.format_list(list_content), font_style="list", id_=i, page_id=1)
        paragraphs.insert(i, list_paragraph)
        return paragraphs, i
    
    def format_list(self,list_content):
        res = ""
        for i in range(len(list_content)):
            if type(list_content[i]) == str:
                res += f"{i+1}. {list_content[i]}\n"
            else:
                res += f"{i+1}. {self.format_list(list_content[i])}\n"
        return res
    
    