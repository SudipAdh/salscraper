'''Scraper object defintion

    Implementation of the scraper object.
'''
from    .extraction         import  Bucket      , Field 
from    .interface          import  Request     , Requests

from    collections         import  OrderedDict
from    saltools.misc       import  g_path
from    enum                import  Enum

from    .                   import  export          as  slsx
from    .                   import  extraction      as  slse

import  saltools.logging    as      sltl
import  saltools.parallel   as      sltp

import  queue

class Signals(Enum):
    STOP        = 0

class Scraper(sltp.NiceFactory):
    EasyObj_PARAMS  = OrderedDict((
        ('start_requests'   , {
            },),
        ('parser'           , {
            'type'  : slse.Parser   },),
        ('interface'        , {
            'default'   : Requests()    },),
        ('data_exporter'    , {
            'default'   : None          ,
            'type'      : slsx.Exporter },),))

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
        for request in self.start_requests  :
            self.start_tasks.append(
                sltp.FactoryTask(
                    target  = self.execute_request  ,
                    args    = [request]             ))
        self.n_data         = 0
        self.on_stop        = self._on_stop
        self.on_start       = self._on_start

    @sltl.handle_exception  (
        sltl.Level.ERROR            ,
        is_log_start= True          ,
        params_start= ['request']   ,
        params_exc  = ['request']   )
    def execute_request     (
        self                        ,
        request                     ,
        immediate   = False         ):
        immediate_result    = {}
        response                        = self.interface.execute_request(request)
        data, requests, data_adapter    = self.parser.parse(response)

        for request in requests:
            self.tasks_queue.put(
                sltp.FactoryTask(
                    target  = self.execute_request  ,
                    args    = [request]             ))

        for bucket_id, item in data.items():
            data_dicts      = item['data']
            adapter         = item['adapter']
            processed_dicts = []
            for data_dict in data_dicts :
                processed_dicts.append(self.process_data(
                    response    , 
                    data_dict   , 
                    adapter     ))
            data[bucket_id]   = processed_dicts
        if      data_adapter :
            data = data_adapter.adapt(response, None, data)
        if      immediate   :
                return data 
        elif    len(data)   :
            if      self.data_exporter != None  :
                self.data_exporter.export(data)
            self.n_data +=1
    def process_data        (
        self            ,
        response        ,
        data_dict       ,
        data_adapter    ):
        '''Processes the parsing result data.
            
            Processes the data results returned by the parser.

            Args:
                response    (Interface.response         ): The response object.
                data_dict   (dict                       ): Data to process.
                data_adapter(collections.ABC.Callable   ): Data adapter.
            Returns:
                dict    : The parsed data.
        '''
        for key, item in data_dict.items():
            if      isinstance(item, dict               ):
                sub_dicts           = item['data']
                sub_adapter         = item['adapter']
                processed_sub_dicts = []
                for sub_dict in sub_dicts   :
                    processed_sub_dicts.append(self.process_data(
                        response    , 
                        sub_dict    , 
                        sub_adapter ))
                data_dict[key]  = processed_sub_dicts
            elif    isinstance(item, list  )            \
                    and isinstance(g_path(item), Request):
                data_dict[key]  = [self.execute_request(request_item, True) for request_item in item]
            else                                         :
                data_dict[key]  = item
        
        if      data_adapter:
            return data_adapter.adapt(response, None, data_dict)
        else                :
            return data_dict



