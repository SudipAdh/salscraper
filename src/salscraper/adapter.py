'''Various data and objects adapters. 
'''
from    saltools.common     import  EasyObj
from    collections         import  OrderedDict
from    saltools.misc       import  g_path      , join_string_array
from    urllib.parse        import  urlencode
from    .                   import  interface
from    lxml                import  etree

import  saltools.logging    as      sltl    
import  saltools.web        as      sltw

import  json
import  html
import  re

class AdapterFunction   (EasyObj):
    '''AdapterFunction
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('method'   , {
            'default': 'JOIN_STRINGS'                                   ,
            'adapter': lambda x: (x if isinstance(x, str) else          \
                lambda self, r, c, l, **kwargs: x(r, c, l, **kwargs))}) ,
        ('kwargs'   , {
            'type'      : dict  ,     
            'default'   : {}    ,}),
        ('is_list'  , {
            'type'      : bool  ,
            'parser'    : bool  ,
            'default'   : False }),))
            
    def adapt(self, r, c, x, **kwargs):
        if      isinstance (self.method, str)   :
            f = getattr(type(self), self.method)
        else                                    :
            f = self.method
        kwargs.update(self.kwargs)
        if      self.is_list    :
            return [f(r, c, y, **kwargs) for y in x]
        else                    : 
            return f(r, c, x, **kwargs)
         
        
    ############################################################
    #################### Extractor
    ############################################################
    #Gets all urls in a string
    REGEX           = lambda r, c, x, regex: re.compile(regex).findall(x)
    #Gets the html source
    SOURCE          = lambda r, c, x: etree.tostring(x, encoding='unicode')
    #Removes all line breaks
    ONE_LINE        = lambda r, c, x, p = ' ': x.replace('\n', p)
    #Put in a list
    LIST            = lambda r, c, x: [x]
    #Json string to dict
    JSON            = lambda r, c, x: json.loads(x)
    #Dict path
    OBJ_PATH        = lambda r, c, x, path= 0, is_return_last= False: g_path(x, path, is_return_last= is_return_last)
    #Filter a list
    FILTER          = lambda r, c, x, key, value: [y for y in x if g_path(y, key)== value] 
    #Returns the absolute urls
    ABSOLUTE_URL    = lambda r, c, x: r.host+ x if 'http' not in x else x 
    #Join a list of strings
    JOIN_STRINGS    = lambda r, c, x, d= ' ': join_string_array(x, d)
    #Slice any list
    SLICE           = lambda r, c, x, start=0, end= -1, step=1 : x[start:end:step]
    #Format a string
    FORMAT_ARGS     = lambda r, c, x, s: s.format(*x) 
    FORMAT_KWARGS   = lambda r, c, x, s: s.format(**x) 
    #Unescape html
    UNESCAPE_HTML   = lambda r, c, x    : html.unescape(x) 
    #Dict            
    DICT            = lambda r, c, x, keys: {
        g_path(keys, i): g_path(x, i) for i in range(len(keys))}

    ############################################################
    #################### Data
    ############################################################
    def FLATTEN (
        r                   , 
        c                   , 
        bucket              , 
        keys                , 
        is_full_name= False ):
        '''Flaten nested arrays or dicts.

            Rises all keys elements to the top level:
                {'b': '1', 'a': {'a1':'1', 'a2':2}} becomes {'b': '1', 'a1':'1', 'a2':2}.
            
            Args:
                r   (interface.Response ): The response object.
                c   (Object             ): The context object.
                data(list, dict         ): Data.
                keys(list, str          ): The keys to flatten.
        ''' 
        def g_buckets_values(buckets):
            values  = {}
            for b_name, s_bucket in buckets.items() :
                for f_name, field in s_bucket[0].items() :
                    if      is_full_name   :
                        f_name  = b_name+ f_name
                    values[f_name]   = field
            return values 

        for key in keys :
            if len(bucket[key]) :
                values  = g_buckets_values(bucket[key][0])
                del bucket[key]
                bucket.update(values)
        return bucket
    def MULTIPLY(
        r               , 
        c               , 
        buckets         , 
        keys            ,
        name_index  = 0 ):
        b_1 = buckets[keys[0]]   
        b_2 = buckets[keys[1]]

        new_list    = []
        for e_1 in b_1  :
            for e_2  in b_2  :
                e_1 = e_1.copy()
                e_2 = e_2.copy()
                e_1.update(e_2) 
                new_list.append(e_1)
        return {
            keys[name_index]    : new_list
            }


    ############################################################
    #################### Requests
    ############################################################
    def GET         (
        response        , 
        context         , 
        args            ,
        url     = None  , 
        params  = {}    ):
        '''Get request.
            
            Generates a simple get request.

            Args:
                response    (interface.Response ): The response object.
                context     (Object             ): Context if there is.
                args        (str                ): The job extracted args.
                params      (dict               ): The default params. 
            
            Returns:
                interface.Request   : The genrated request. 
        '''
        if      not isinstance(args, list)  :
            args    = [args]
        if      not url                     :
            return [interface.Request(arg, params= params) for arg in args]
        else                                :
            requests    = []
            for arg in args :
                arg_params  = params.copy()
                arg_params.update(arg)
                requests.append(
                    interface.Request(url, params= arg_params))
            return requests
    def NEXT_PAGE   (
        response            , 
        context             , 
        args                ,
        page_param  = 'page'):
        current_url = response.request_url
        page_number = int(sltw.g_url_param(current_url, page_param))
        
        return  [current_url.replace(
            urlencode({page_param   : page_number   })  , 
            urlencode({page_param   : page_number+1 })  )]

class Adapter           (EasyObj):
    '''Data adapter, processes data using one or many adapters
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('functions'    , {
            'type'      : AdapterFunction                   ,
            'default'   : AdapterFunction('JOIN_STRINGS')   }),))
    
    def _on_init(self):
        self.functions  = self.functions if isinstance(self.functions, list) else [self.functions]
    
    @sltl.handle_exception(
        sltl.Level.ERROR    )
    def adapt(self, r, c, x, **kwargs):
        '''Uses the functions s a pipline to adapt the given value l.
        '''

        for function in self.functions:
            x = function.adapt(r, c, x, **kwargs)
        return x






        