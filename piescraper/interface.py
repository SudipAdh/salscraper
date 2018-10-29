'''
    A wrpper around various web automation libraries and tools.
'''
__author__      = 'saledddar'
__email___      = 'saledddar@gmail.com'
__copyright__   = '2018, piescraper'

from saltools import do_request


class InterfaceBase():
    def __init__(self):
        pass


class RequestsInterface(InterfaceBase):

    def request_source(self, request_dict):
        return do_request(**request_dict).text
