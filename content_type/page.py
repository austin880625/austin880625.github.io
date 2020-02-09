import os
import markdown
from .content import Content

class Page(Content):
    def __init__(self, name):
        Content.__init__(self, name)
        self.permalink += ".html"
        self.title = self.meta.get("title")
        self.content = ""
        if self.file_type == ".md":
            self.content = markdown.markdown(self.raw_content, extensions=['extra', 'markdown_del_ins'])
    def get_content(self):
        return self.content