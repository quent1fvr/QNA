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
    

    def handle_levels(self, font_style: str):
        # Word-specific style parsing
        if font_style.startswith('Heading '):
            try:
                level = int(font_style.split(' ')[-1])
                return level
            except ValueError:
                return INFINITE

        # PDF-specific style parsing
        elif font_style.startswith('title'):
            try:
                # Assuming title7, title6, etc., corresponds to levels 7, 6, etc.
                level = int(font_style.replace('title', ''))
                return level
            except ValueError:
                return INFINITE
        elif font_style == 'content':
            # Assign a default level for general content
            return INFINITE

        # Default for unrecognized styles
        else:
            return INFINITE

