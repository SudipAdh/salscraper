'''
    A wrpper around various web automation libraries and tools.
'''
__author__      = 'saledddar'
__email___      = 'saledddar@gmail.com'
__copyright__   = '2018, piescraper'

from saltools import do_request


class InterfaceBase():
    def __init__():
        pass


class RequestsInterface(InterfaceBase):

    def request_source(request_dict):
        return do_request(**request_dict).text
