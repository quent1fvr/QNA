import docx
import os
from src.model.paragraph import Paragraph

class WordReader:

    def __init__(self, path):
        self.path = path
        self.paragraphs = self.get_word_paragraphs()

    def get_word_paragraphs(self):
        """
        Fetches paragraphs from a Word document.

        Returns:
            list: List of Paragraph objects from the document.
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"The file {self.path} does not exist.")

        try:
            doc = docx.Document(self.path)
            paragraphs = self.to_paragraph_objects(doc.paragraphs)  # Convert to  Paragraph objects
            return paragraphs
        except Exception as e:
            raise ValueError(f"Error reading the .docx file. Original error: {str(e)}")

    def determine_style(self, paragraph):
        """
        Determines the style of the paragraph based on its attributes.

        Returns:
            str: Style of the paragraph.
        """
        # Check for heading styles first
        if paragraph.style.name.startswith('Heading 1'):
            return "title1"
        elif paragraph.style.name.startswith('Heading 2'):
            return "title2"
        elif paragraph.style.name.startswith('Heading 3'):
            return "title3"
        elif paragraph.style.name.startswith('Heading 4'):
            return "title4"
        elif paragraph.style.name.startswith('Heading 5'):
            return "title5"
    
        # If not a heading, check the runs within the paragraph
        for run in paragraph.runs:
            font = run.font
            fontname = font.name
            size = font.size
        
            # Convert size to points (from twips)
            if size:
                size_in_points = size.pt

                # Map based on font name and size as in the PDF reader
                if fontname == "XFQKGD+Consolas":
                    return "code"
                elif (size_in_points >= 9 and size_in_points < 11.5) or fontname == "Wingdings-Regular":
                    return "content"    
        # If none of the above conditions match, default to 'content'
        return "content"
    

    def to_paragraph_objects(self, doc_paragraphs):
        """
        Convert docx paragraphs to Paragraph objects for further processing.
        """
        paragraph_objects = []
        for idx, paragraph in enumerate(doc_paragraphs):
            style = self.determine_style(paragraph)

            # Assuming page_id is always 1 for simplicity, change as needed.
            p_obj = Paragraph(text=paragraph.text, font_style=style, id_=idx, page_id=1)
            paragraph_objects.append(p_obj)
            paragraphs = self.rearrange_paragraphs(paragraph_objects)

        return paragraphs


    def rearrange_paragraphs(self, paragraphs : [Paragraph]):
        #associate paragraphs with the same font style
        i = 0
        while i < len(paragraphs):
            paragraphs[i] = paragraphs[i].rearrange_paragraph()
            i+=1
        return paragraphs


    def display_paragraphs(self):
        """
        Prints the paragraphs from the document to the console.
        """
        for paragraph in self.paragraphs:
            print(paragraph.text)
            print('-' * 40)  # separator for clarity

# if __name__ == '__main__':
#     reader = WordReader("Illumio_Core_REST_API_Developer_Guide_23.3.docx")
#     reader.display_paragraphs()
