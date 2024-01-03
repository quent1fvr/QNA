import string

INFINITE = 10000

class Paragraph:
    def __init__(self, text : str, font_style : str, id_ : int, page_id : int):
        self.font_style = font_style
        self.id_ = int(str(2)+str(page_id)+str(id_))
        self.page_id = page_id
        self.level = self.handle_levels(font_style)
        self.is_structure = self.level < INFINITE
        self.text = text

    @property
    def blank(self):
        """
        checks if the paragraph is blank: i.e. it brings some signal (it may otherwise be ignored)
        """
        text = self.text.replace('\n', '')
        return set(text).isdisjoint(string.ascii_letters)
    
    def rearrange_paragraph(self):
        """
        rearrange the paragraph to have a better structure
        """
        if self.font_style == "code":
            self.text = "\n\nCode :```\n" + self.text + "\n```\n\n"
        elif self.font_style == "table":
            self.text = "\n\nTable :\n" + self.text + "\n\n"
        return self
    
    def handle_levels(self, font_style : str):
        if len(font_style) != 5 and 'title' in font_style:
            return int(font_style[-1])
        elif len(font_style) == 2 and font_style[0] == 'h':
            return int(font_style[-1])
        else:
            return INFINITE
        
