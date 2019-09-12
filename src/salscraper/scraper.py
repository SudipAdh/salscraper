'''Scraper object defintion

    Implementation of the scraper object.
'''
from    .extraction         import  Bucket    , Field 
from    .interface          import  Request
from    .                   import  extraction

from    collections         import  OrderedDict
from    saltools.common     import  EasyObj
from    threading           import  Thread
from    enum                import  Enum

import  saltools.logging    as      stl

import  threading
import  queue

class Signals(Enum):
    STOP        = 0

class Scraper(EasyObj):
    '''Scraper class.

        Manages tasks execution and returns task result to callers.

        Args:
            interface       (interface.Interface        ): Web interface.
            consume         (collections.abc.Callable   ): A function to consume the data returned by the parser.
                consume(data) where data is list of dicts.
            logger          (saltools.logging.logger    ): Logger.
            start_requests  (list,Request   | list, str ): Starting urls.
            n_threads       (int    : 1                 ): Number of threads to use.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('interface'        , {}                        ),
        ('consume'          , {}                        ),
        ('logger'           , {}                        ),
        ('start_requests'   , {}                        ),
        ('parser'           , {
            'type'  : extraction.Parser                 }),
        ('n_threads'        , {'default': 1}            )))

    @stl.handle_exception()
    def _on_init(self):
        super().__init__(*args, **kwargs)
        self.request_queue  = queue.Queue()
        self.thread_queue   = queue.Queue()

        self.alive          = False

        for request in self.start_requests :
            self.request_queue.put(request)
        
        for i in range(self.n_threads)  :
            self.thread_queue.put('Thread {}'.format(i))
    
    @stl.handle_exception(log_start= True)
    def start(self  ):
        '''Starts  the scraper.

            Starts the scraper.
        '''
        self.alive          = True
        self.main_thread    = Thread(target= self.loop)

        self.main_thread.start()
    @stl.handle_exception(log_start= True)
    def stop(self   ):
        '''Stops the scraper.

            Stops the scraper.
        '''
        self.request_queue.put(Signals.STOP)
    @stl.handle_exception(log_start= True, log_end= True)
    def loop(self   ):

        while True:
            #Get the new request
            request    = self.request_queue.get()

            #Check for abort
            if request == Signals.STOP :
                break
            else                    :
                #Get thread id
                thread_id = self.thread_queue.get()
                thread = Thread(target= self.execute_request, args= (request, ), name= thread_id)
                thread.start()
        
        self.alive          = False

    @stl.handle_exception(
        level       = stl.Level.ERROR    ,
        log_params  = ['request']       )
    def execute_request(
        self                        ,
        request                     ,
        immediate   = False         ,
        log_params  = ['request']   ):
        '''Executes a request.

            Executes a request by a thread.

            Args:
                request     (Interface.Request  ): The request.
                immediate   (bool               ): If `True`, data is returned instead of consumed
            Returns:
                list    : A list containing parsed data if immediate is `True` 
        '''
        immediate_result    = {}

        try :
            response        = self.interface.execute_request(request)
            data, requests  = self.parser.parse(response)

            for request in requests:
                self.request_queue.put(request)

            for bucket_name, item in data.items():
                data_dicts      = item['data']
                adapter         = item['adapter']
                processed_dicts = []
                for data_dict in data_dicts :
                    processed_dicts.append(self.process_data(
                        response    , 
                        data_dict   , 
                        adapter     ))
                data[bucket_name]   = processed_dicts
            if      immediate   :
                    return data 
            else                :
                self.consume(response, data)
        finally:
            self.thread_queue.put(threading.current_thread().name)
            if      not self.request_queue.qsize()          and\
                    self.thread_queue.qsize() == self.n_threads:
                    self.request_queue.put(Signals.STOP)
    @stl.handle_exception(level= stl.Level.ERROR)
    def process_data(
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
                sub_dicts           = data_dict['data']
                sub_adapter         = data_dict['adapter']
                processed_sub_dicts = []
                for sub_dict in sub_dicts   :
                    processed_dicts.append(self.process_data(
                        response    , 
                        sub_dict    , 
                        sub_adapter ))
                data_dict[key]  = processed_dicts
            elif    isinstance(item, list  ) and len(item) and isinstance(item[0], Request):
                data_dict[key]  = [self.execute_request(request_item, True) for request_item in item]
            else                                         :
                data_dict[key]  = item
        
        if      data_adapter:
            return data_adapter.adapt(None, None, [data_dict])[0]
        else                :
            return data_dict



