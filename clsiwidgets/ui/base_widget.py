import logging
from ipywidgets import DOMWidget

class BaseWidget(object):
    DEFAULT_BORDER = {'border': '2px solid lightgray',
                      'padding': '10px'}

    BUTTON_STYLE = {'height': '40px',
                    'width': '150px'}

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(self.__class__.__module__)

    def get_widget(self):
        if isinstance(self, DOMWidget):
            return self
        logging.error("Not a valid widget! Try to overwrite get_widget or inherit DOMWidget!")
        raise RuntimeWarning("Not a valid widget!")

    def add_datatype(self, datatype):
        raise NotImplementedError