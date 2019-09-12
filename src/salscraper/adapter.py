'''Various data and objects adapters. 
'''
from    saltools.common     import  EasyObj
from    collections         import  OrderedDict
from    saltools.misc       import  g_safe          , join_string_array
from    .                   import  interface

import  saltools.logging    as      stl    

class AdapterFunction   (EasyObj):
    '''AdapterFunction
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('method'   , {
            'default': 'JOIN_STRINGS'   
            'adapter': lambda x: x if isinstance(x, str) else       \
                lambda self, r, c, l, **kwargs: x(r, c, l, **kwargs)}),
        ('kwargs'   , {
            'type'      : dict  ,     
            'default'   : {}    ,})))
            
    @stl.handle_exception(level= stl.Level.ERROR)
    def adapt(self, r, c, l, **kwargs):
        if      isinstance (self.method, str)   :
            f = getattr(type(self), self.method)
        else                                    :
            f = self.method
        kwargs.update(self.kwargs)
        return f(r, c, l, **kwargs)
        
    ############################################################
    #################### Extractor
    ############################################################

    #Gets the first value of a list
    FIRST_VALUE = lambda r, c, l: g_safe(l, 0)
    #Returns the absolute urls for each url in list l
    ABSOLUTE_URL= lambda r, c, l: [r.host+ x if 'http' not in x else x for x in l] 
    #Join a list of strings
    JOIN_STRINGS= lambda r, c, l, d= ' ': join_string_array(l, d)

    ############################################################
    #################### Data
    ############################################################
    def FLATTEN(r, c, data, keys= {}):
        '''Flaten nested arrays or dicts.

            Rises all keys elements to the top level:
                {'b': '1', 'a': {'a1':'1', 'a2':2}} becomes {'b': '1', 'a1':'1', 'a2':2}.
            
            Args:
                r   (interface.Response ): The response object.
                c   (Object             ): The context object.
                data(list, dict         ): Data.
                keys(list, str          ): The keys to flatten.
        ''' 
        def g_sub_buckets_values(sub_buckets):
            values  = {}
            if      len(sub_buckets):
                data_bucket = list(sub_buckets[0].values())[0][0]
                values      = {key:value for key, value in data_bucket.items()}
            return values 

        if not len(data):
            return
        
        #Flatten all
        if not len(keys):
            keys = [key for key in data[0]     if  \
                isinstance(data[0][key], list) and \
                len(data[0][key])              and \
                isinstance(data[0][key][0], dict)  ]

        buckets     = data
        for bucket in buckets :
            for key in keys :
                values  = g_sub_buckets_values(bucket[key])
                del bucket[key]
                bucket.update(values)
        return buckets

    ############################################################
    #################### Requests
    ############################################################
    def URL_GET(r, c, urls, params= {}):
        '''Simple get request.
            
            Generates a simple get request.

            Args:
                response    (interface.Response ): The response object.
                context     (Object             ): Context if there is.
                url         (str                ): The job url.
                params      (dict               ): The default params.
                request     (interface.Request  ): The preconstructed request object. 
            
            Returns:
                interface.Request   : The genrated request. 
        '''
        return [ interface.Request(
                url                 ,
                interface.Method.GET,
                params              ,
                None                ,
                r.session           ) for url in urls]
class Adapter           (EasyObj):
    '''Data adapter, processes data using one or many adapters
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('functions'    , {
            'type'      : AdapterFunction                   ,
            'default'   : AdapterFunction('JOIN_STRINGS')   }),))
    
    def _on_init(self):
        self.functions  = self.functions if isinstance(self.functions, list) else [self.functions]
 
    @stl.handle_exception(level= stl.Level.ERROR)
    def adapt(self, r, c, l, **kwargs):
        '''Uses the functions s a pipline to adapt the given value l.
        '''

        for function in self.functions:
            l = function.adapt(r, c, l, **kwargs)
        return l






        