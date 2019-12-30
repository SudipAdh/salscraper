'''Scraper object defintion

    Implementation of the scraper object.
'''
from    collections         import  OrderedDict
from    saltools.misc       import  g_path
from    enum                import  Enum

from    .                   import  export          as  slsx
from    .                   import  core            as  slsc
from    .                   import  interface       as  slsi
from    .                   import  extraction      as  slse

import  saltools.logging    as      sltl
import  saltools.parallel   as      sltp

import  queue

class Scraper   (
    sltp.NiceFactory    ):
    EasyObj_PARAMS  = OrderedDict((
            ('start_requests'   , {
                },),
            ('parser'           , {
                'type'  : slsc.Parser   },),
            ('interface'        , {
                'type'      : slsi.Interface    ,
                'default'   : slsi.Requests()   },),
            ('data_exporter'    , {
                'default'   : None          ,
                'type'      : slsx.Exporter },),
            ('requests_adapter' , {
                'default'   : 'REQUEST'         ,
                'type'      : slse.Extractor    },),
        ))

    def _on_stop    (
        self    ,
        factory ):
        self.n_data = 0
    def _on_start   (
        self    ,
        factory ):
        pass
    def _on_init    (
        self    ):
        self.is_no_tasks_stop   = True

        for request in self.start_requests  :
            request_dict    = {'url': request} if isinstance(request, str) else request
            request_obj     = self.requests_adapter.extract(
                None            ,
                None            ,
                {}              ,
                **request_dict  )
            self.start_tasks.append(
                sltp.FactoryTask(
                    target  = self.execute_request  ,
                    args    = [request_obj]         ))

        self.n_data             = 0
        self.on_stop            = self._on_stop
        self.on_start           = self._on_start

    @sltl.handle_exception  (
        sltl.Level.ERROR            ,
        is_log_start= True          ,
        params_start= ['request']   ,
        params_exc  = ['request']   )
    def execute_request     (
        self    ,
        request ):
        response    = self.interface.execute_request(request)
        r_list      = []
        data        = self.parser.parse(
            response                        ,
            self.interface.execute_request  ,
            r_list                          ,
            self.data_exporter.export       )
        
        for request in r_list :
            self.tasks_queue.put(
                sltp.FactoryTask(
                    target  = self.execute_request  ,
                    args    = [request]             ))
