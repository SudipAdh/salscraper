'''Data extraction logic.
'''
from    saltools.common     import  EasyObj
from    collections         import  OrderedDict
from    saltools.misc       import  g_path      , join_string_array
from    os.path             import  join        , abspath
from    urllib.parse        import  urlencode
from    lxml.html           import  etree
from    enum                import  Enum
from    .                   import  interface   as  slsi
from    .                   import  settings    as  slst

import  saltools.logging    as      sltl
import  saltools.web        as      sltw
import  saltools.misc       as      sltm
import  saltools.common     as      sltc

import  inspect
import  yaml
import  html
import  re

class SourceType    (
    Enum    ):
    '''Source type.
    '''
    REQUEST_URL     = 0
    RESPONSE_URL    = 1
    HTML            = 2
    JSON            = 3
    TEXT            = 4
    CONTENT         = 5
    CONTEXT         = 6

class EXTRACTORS            (
    ):
        SOURCE_TYPE_OBJECT_MAP  = {
            SourceType.REQUEST_URL  : lambda response: response.request_url         ,
            SourceType.RESPONSE_URL : lambda response: response.response_url        ,
            SourceType.HTML         : lambda response: response.html_tree           ,
            SourceType.JSON         : lambda response: response.json                ,
            SourceType.TEXT         : lambda response: response.text                ,
            SourceType.CONTENT      : lambda response: response.content             }
        METHOD_SOURCE_TYPE_MAP  = {
            'XPATH'     : 'HTML'            ,
            'NEXT_PAGE' : 'REQUEST_URL'     ,
            'FROM_JSON' : 'TEXT'            ,
            }
        ABREV_METHOD_MAP        = {
            '='     : 'EQUALS'          ,
            'x'     : 'XPATH'           ,
            'r'     : 'REGEX'           ,
            's'     : 'FROM_HTML'       ,
            'h'     : 'TO_HTML'         ,
            '?'     : 'REPLACE'         ,
            'l'     : 'IN_LIST'         ,
            'j'     : 'FROM_JSON'       ,
            '!'     : 'FILTER'          ,
            'a'     : 'ABS_URL'         ,
            '_'     : 'JOIN_STRS'       ,
            'p'     : 'OBJ_PATH'        ,
            'f'     : 'FORMAT'          ,
            '/'     : 'SLICE'           ,
            'u'     : 'UNESCAPE_HTML'   ,
            'd'     : 'TO_DICT'         ,
            'o'     : 'ARTHM'           ,
            '>'     : 'UPPER'           ,
            '<'     : 'LOWER'           ,
            'rs'    : 'RESOURCE'        ,
            'st'    : 'STRIP'           ,
            ' '     : 'NONE'            ,
            'b'     : 'TO_BOOL'         ,

            '@'     : 'REQUEST'         ,
            'n'     : 'NEXT_PAGE'       ,

            'bf'    : 'B_FLATTEN'       ,
            'bm'    : 'B_MULTIPLY'      }

        ABREV_SOURCE_MAP        = {
            'q' : 'REQUEST_URL'     ,
            's' : 'RESPONSE_URL'    ,
            'h' : 'HTML'            ,
            'j' : 'JSON'            ,
            't' : 'TEXT'            ,
            'n' : 'CONTENT'         ,
            'c' : 'CONTEXT'         }
    
        @classmethod
        def g_all_names (
            cls ):
            return [
                x[0] for x in inspect.getmembers(cls, predicate=inspect.ismethod)   \
                if x[0] not in ['g_all_names']]
    #----------------------------------------
    # Data extractors
    #----------------------------------------
        @classmethod
        def EQUALS          (
            cls ,
            r   , 
            c   , 
            x   ,
            y   ):
            '''Check if x == y.
                
                Args:
                    x       (object ): Any `object`.
                    y       (object ): Any `object`.
                Returns:
                    object|None   : x if `x` equals `y` else `None`.
            '''
            return x if x == y else None
        @classmethod
        def XPATH           (
            cls     ,
            r       , 
            c       ,
            x       ,
            xpath   ):
            '''Regex extractor.
                
                Args:
                    x       (object ): The html source or element.
                    xpath   (str    ): Xpath expression.
                Returns:
                    list[object]    : A list of matches.
            '''
            return sltw.g_xpath(x, xpath)
        @classmethod
        def REGEX           (
            cls             ,
            r               ,
            c               ,
            x               ,
            pattern = '.*'  ):
            '''Regex extractor.
                
                Args:
                    x       (str    ): The string to extract from.
                    regex   (str    ): Pattern to match.
                Returns:
                    list[str]   : A list of matches.
            '''
            return re.findall(pattern, x)
        @classmethod
        def FROM_HTML       (
            cls     ,
            r       , 
            c       , 
            x       ):
            '''Gets the HTML source of an HTML element as string.
                
                Args:
                    x   (lxml.html.HtmlElement  ): The element to get the source of.
                Returns:
                    str: HTML source of the element.
            '''
            return etree.tostring(x, encoding='unicode').strip()
        @classmethod
        def TO_HTML         (
            cls     ,
            r       , 
            c       , 
            x       ):
            '''Gets the HTML source of an HTML element as string.
                
                Args:
                    x   (str    ): The html source.
                Returns:
                    lxml.html.HtmlElement   : HTML element.
            '''
            return etree.fromstring(x)
        @classmethod
        def REPLACE         (
            cls                 ,
            r                   ,
            c                   ,
            x                   ,
            pattern     = '\n'  ,
            replacement = ' '   ):
            '''Replaces the pattern with the replacement.

                Args:
                    x           (str)   : The string te process.
                    pattern     (str)   : The regex pattern to replace.
                    replacement (str)   : Replacement string.
                Returns:
                    str : The processed string.
            '''
            return re.sub(pattern, replacement, x)
        @classmethod
        def IN_LIST         (
            cls ,
            r   ,
            c   , 
            x   ):
            '''Put in a list

                Args:
                    x (object)  : The object to put in a list.
                Returns:
                    list[object]    : A list containing the object.
            '''
            return [x]
        @classmethod
        def FROM_JSON       (
            cls ,
            r   , 
            c   , 
            x   ):
            '''Creates a dict from json.

                Args:
                    x   (str    ): JSON string.
                Returns:
                    dict    : A dict object.
            '''
            x   = re.sub(',\s+,', ',', x)
            return yaml.load(x, yaml.Loader)
        @classmethod
        def OBJ_PATH        (
            cls                     ,
            r                       ,
            c                       ,
            x                       ,
            path            = 0     ,
            is_return_last  = False ,
            is_check_only   = False ):
            '''Gets the value at the given path.

                Args:
                    x               (object                 ): Can be anything from an object, list, or dict.
                    path            (str|int|list[str|int]  ): Can be an integer in case of indices, a string for dict keys
                        or objects attributes, or list containing both, the list can also be a string like the example :
                            - `path_to.0.name` , this will get the value of path_to from the dict or obj, then gets the 
                                element at index 0, then the property/key name.
                    is_return_last  (bool                   ): If `True`, returns the last available value in the path before 
                        failure.
                Returns:
                    object  : The value found at the given path.
            '''
            result  = g_path(x, path, is_return_last= is_return_last)
            if      is_check_only   :
                return True if result != None else False
            else                    :
                return result
        @classmethod
        def FILTER          (
            cls             ,
            r               ,
            c               ,
            x               ,
            path            ,
            value   = None  ):
            '''Filters the values in an iterable.

                Args:
                    x           (collections.abc.Iterable   ): The iterable to filter.
                    path        (str|int|list[str|int]      ): Can be an integer in case of indices, a string for dict keys
                        or objects attributes, or list containing both, the list can also be a string like the example :
                            - `path_to.0.name` , this will get the value of path_to from the dict or obj, then gets the 
                                element at index 0, then the property/key name.
                    value       (object                     ): The value to filter by.
                Returns:
                    list    : A flitered list.
            '''
            return [y for y in x if (
                (value == None and g_path(y, path, is_return_last= False) != None   )\
                or g_path(y,path) == value                                          )]
        @classmethod
        def ABS_URL         (
            cls ,
            r   ,
            c   ,
            x   ):
            '''Gets the absolute url if a url is not absolute.

                Args:
                    x   (str    ): A url.
                Returns:
                    str : Absolute url.
            '''
            return r.host+ x if x[:4] != 'http' else x
        @classmethod
        def JOIN_STRS       (
            cls         ,
            r           ,
            c           ,
            x           ,
            by  = ' '   ):
            '''Joins a list of string.

                Args:
                    x   (list[str]  ): A list of strings.
                    by  (str        ): The string to join by.
                Returns:
                    str : The full string.
            '''
            return join_string_array(x, by)
        @classmethod
        def SLICE           (
            cls         ,
            r           ,
            c           ,
            x           ,
            start   = 0 ,
            end     = -1, 
            step    = 1 ):
            '''Slice a list.

                Args:
                    x       (list   ): The list to slice.
                    start   (int    ): Start index.
                    end     (int    ): End index.
                    step    (int    ): Step.
                Returns:
                    list    : The slice.
            ''' 
            return x[start:end:step]
        @classmethod
        def FORMAT          (
            cls     ,
            r       ,
            c       ,
            x       ,
            f_str   ):
            '''Format a string.

                Args:
                    x       (dictlist|object    ): List or dict of values.
                    f_str   (str                ): Format string.
                Returns:
                    str : The formatted string.
            '''
            x   = x if (isinstance(x,list) or isinstance(x, dict)) else [x]
            return f_str.format(*x)             \
                    if      isinstance(x, list) \
                    else    f_str.format(**x)
        @classmethod
        def UNESCAPE_HTML   (
            cls ,
            r   ,
            c   ,
            x   ):
            '''Unescape HTML.
                Example:
                    - `Kristj&aacuten V&iacute;ctor` >>> `Kristján Víctor`
                Args:
                    x   (str    ): The html to unescape.
                Returns:
                    str : Escaped HTML.
            ''' 
            return html.unescape(x)           
        @classmethod
        def TO_DICT         (
            cls     ,
            r       ,
            c       ,
            x       ,
            keys    ):
            '''Convers a list to a dict.

                Args:
                    x       (list       ): A list.
                    keys    (list[str]  ): A list of keys.
                Reruns:
                    A dict.
            '''
            return {keys[i]: x[i] for i in range(len(keys))}
        @classmethod
        def ARTHM           (
            cls         ,
            r           ,
            c           ,
            x           ,
            y           ,
            op  = '+'   ):
            '''Performs an arithmetic operation.

                Args:
                    y   (float|int  ): Right operand.
                    op  (str        ): Operator +, -, *, **,/, //, %
            '''
            if      op == '+'   :
                return x+ y
            elif    op == '-'   :
                return x- y
            elif    op == '*'   :
                return x* y
            elif    op == '**'  :
                return x** y
            elif    op == '/'   :
                return x/ y
            elif    op == '//'  :
                return x// y
            elif    op == '%'   :
                return x// y
        @classmethod
        def UPPER           (
            cls     ,
            r       ,
            c       ,
            x       ):
            '''Upper case.

                Args:
                    x       (list|dict  ): A string.
                Returns:
                    str :  x in upper case.
            '''
            return x.upper()
        @classmethod
        def LOWER           (
            cls     ,
            r       ,
            c       ,
            x       ):
            '''lower case.

                Args:
                    x       (list|dict  ): A string.
                Returns:
                    str :  x in lower case.
            '''
            return x.lower()
        @classmethod
        def RESOURCE        (
            cls     ,
            r       ,
            c       ,
            x       ):
            '''Loads a resource

                Args:
                    x       (str    ): resource name.
                Returns:
                    dict    :  The dict loaded from the JSON resource.
            '''
            resource_path   = join(slst.RESOURCE_FOLDER, x+'.json')
            return sltm.g_config(resource_path)
        @classmethod
        def STRIP           (
            cls     ,
            r       ,
            c       ,
            x       ):
            '''Strips a string.

                Args:
                    x       (str    ): string.
                Returns:
                    str :  Stripped string.
            '''
            return x.strip()
        @classmethod
        def NONE            (
            cls     ,
            r       ,
            c       ,
            x       ):
            '''Returns the same object.

                Args:
                    x   (object ): An object.
                Returns:
                    object  :  The same object.
            '''
            return x
        @classmethod
        def PRINT           (
            cls         ,
            r           ,
            c           ,
            x           ):
            '''Prints `x` to the console, use for debuging.

                Args:
                    x   (object ): An object.
                Returns:
                    object  :  The same object `x`.
            '''
            print(x)
            return x
        @classmethod
        def FIRST           (
            cls         ,
            r           ,
            c           ,
            x           ):
            '''Returns the element from a list that is not `None`.

                Args:
                    x   (list   ): A list.
                Returns:
                    object  :  The first not `None` object.
            '''
            first   = None
            for e in x :
                if      e not in [None, ''] :
                    first   = e
                    break
            return first
        @classmethod
        def TO_BOOL         (
            cls ,
            r   , 
            c   , 
            x   ):
            '''`True` if x is not `None`, otherwise `False`.
                
                Args:
                    x       (object ): Any `object`.
                Returns:
                    Bool    : True if `x` exists.
            '''
            return True if x != None else False
    #----------------------------------------
    # Buckets extractors
    #----------------------------------------
        @classmethod
        def B_FLATTEN   (
            cls                     ,
            r                       , 
            c                       , 
            x                       , 
            keys                    , 
            is_full_name    = False ):
            '''Flaten nested arrays or dicts.

                Rises all keys elements to the top level:
                    {'b': '1', 'a': {'a1':'1', 'a2':2}} becomes {'b': '1', 'a1':'1', 'a2':2}.
                
                Args:
                    bucket          (list[dict] ): Data bucket.
                    keys            (list[str]  ): The keys to flatten.
                    is_full_name    (bool       ): If `True`, combine sub-bucket value with flattened fields.
                Return:
                    dict    : Flattened bucket.   
            ''' 
            bucket  = x.copy()
            def g_buckets_values(
                b_name      ,
                s_bucket    ):
                values  = {}
                for f_name, field in s_bucket.items() :
                    if      is_full_name   :
                        f_name  = f'{b_name}_{f_name}'
                    values[f_name]   = field
                return values 

            for key in keys :
                if len(bucket[key]) :
                    values  = g_buckets_values(key, bucket[key][0])
                    del bucket[key]
                    bucket.update(values)
            return bucket
        @classmethod
        def B_MULTIPLY  (
            cls                     ,
            r                       ,
            c                       ,
            buckets                 ,
            bucket_A_name           ,
            bucket_B_name           ,
            new_name        = None  ,
            is_del_buckets  = True  ):
            '''Creates a bucket for each combination of bucket A and B.

                Args:
                    buckets         (dict   ): The buckets dict.
                    bucket_A_name   (str    ): Bucket A name.
                    bucket_B_name   (str    ): Bucket B name.
                    new_name        (str    ): The name for the new bucket. If None it is set to `bucket_A_name`.
                    is_del_buckets  (bool   ): If `True`, delete processed buckets.
                Returns:
                    dict    : The new bucket data.
            '''
            buckets     = buckets.copy()
            bucket_1    = buckets[bucket_A_name]   
            bucket_2    = buckets[bucket_B_name]
            if      not new_name    :
                new_name = bucket_A_name

            new_list    = []
            for values_1 in bucket_1 :
                for values_2  in bucket_2 :
                    values_1 = values_1.copy()
                    values_2 = values_2.copy()
                    values_1.update(values_2)
                    new_list.append(values_1)

            if      is_del_buckets :
                del buckets[bucket_A_name]
                del buckets[bucket_B_name]
            
            buckets[new_name]   = new_list
            
            return buckets
    #----------------------------------------
    # Requests extractors
    #----------------------------------------
        @classmethod
        def REQUEST     (
            cls                         ,
            r                           ,
            c                           ,
            x                           ,
            url     = None              ,
            method  = slsi.Method.GET   ,
            params  = {}                ):
            '''Build a request.

                Args:
                    x       (list[str]|list[dict]   ): The job extracted args or a list of urls.
                    url     (str                    ): The url of the request, If `None`, `x` must be a list of urls.
                    method  (interface.Method       ): Request method.
                    params  (dict                   ): The default params. 
                
                Returns:
                    interface.Request   : The genrated request. 
            ''' 
            if      isinstance(method, str) :
                method  = getattr(slsi.Method, method)
            if      not url                 :
                return slsi.Request(x, params= params, method= method)
            else            :
                args_params  = params.copy()
                args_params.update(x)
                return slsi.Request(url, params= args_params, method= method)
        @classmethod
        def NEXT_PAGE   (
            cls             ,
            r               ,
            c               ,
            x               ,
            param   = None  ):
            '''Gets the next page url.

                Args:
                    x       (str    ): If given, it will be used instead of the curnet request url.
                    param   (str    ): If given, it will be parsed first if found.
                Returns:
                    str : The url for the next page. 
            '''
            possible_params = ['page', 'page_number', 'pg', 'p', '']
            page_number     = None
            full_match      = None
            current_url     = x if isinstance(x, str) else r.request_url

            if      param != None   :
                possible_params.insert(0, param)

            for possible_param in possible_params   :
                pattern         = f'{possible_param}'+ r'\w*?[\/=](\d+)'
                pattern_full    = f'{possible_param}'+ r'\w*?[\/=]\d+'
                if      len(re.findall(pattern, current_url)):
                    page_number = int(re.findall(pattern, current_url)[0]) 
                    full_match  = re.findall(pattern_full, current_url)[0]
                    prefix      = full_match[:-len(str(page_number))]
                    break
            
            assert page_number  != None , 'Cannot find a pagination parameter.'

            return re.sub(pattern_full,prefix+str(page_number+1), current_url)
class ExtractorFunction     (
    EasyObj ):
    '''Extractor function.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('method'       , {
            'default'   : 'JOIN_STRINGS'    ,
            'adapter'   : lambda m          :\
                            getattr(EXTRACTORS, m) if isinstance(m, str) else       \
                            lambda self, r, c, x, **kwargs: m(r, c, x **kwargs)}    ),
        ('kwargs'       , {
            'type'      : dict  ,     
            'default'   : {}    ,}),
        ('is_list'      , {
            'type'      : bool  ,
            'default'   : False }),
        ('source_type'  , {
            'type'      : SourceType            ,
            'default'   : SourceType.CONTEXT    }),))
        
    @classmethod
    def _parse_value        (
        cls     ,
        str_    ):
        '''Parses the value of a kwarg.

            Logic:
                - If the value is raw `<(value)>`, return the value witout further parsing.
                - Try parsing to int, float, bool in order, if all failed, return the value as a string.
            
            Args:
                str_    (str    ): The string to parse.
            Returns:
                object  : The parsed string as an object.
        '''
        open_       = slst.ESC_OPEN.replace('(', r'\(')
        close       = slst.ESC_CLOSE.replace(')', r'\)')
        raw_pattern = f'{open_}(.*?){close}'
        raw_value   = g_path(re.findall(raw_pattern, str_),is_return_last=False)
        if      raw_value != None:
            return raw_value

        types   = [int, float, bool]
        for type_ in types:
            try     :
                return sltc.EasyObj.DEFAULT_PARSERS[type_](str_)
            except  :
                pass
        return str_
    @classmethod
    def _parse_method_type  (
        cls     ,
        str_    ):
        pattern                         = r'^(\*?)(.+?)(?:,(\w+?))?(?::.*)?$$'
        is_list, method_, source_type_  = re.findall(pattern, str_, re.DOTALL)[0]
        
        is_list = True if is_list == '*' else False
        
        if      len(method_) < 4                        :
            method  = EXTRACTORS.ABREV_METHOD_MAP.get(method_)
        else                                            :
            method  = method_
        if      method not in EXTRACTORS.g_all_names()  :
            raise ValueError(f'Method name/abrv {method_} is not found.')
        
        source_type = source_type_
        if      source_type_ == ''                              :
            source_type = 'CONTEXT'
        elif    len(source_type_) < 4                           :
            source_type = EXTRACTORS.ABREV_SOURCE_MAP.get(source_type)
        if      source_type not in SourceType._member_names_    :
            raise ValueError(f'Source type {source_type_} is not found.')
        
        return is_list, method, source_type
    @classmethod
    def _parse_kwargs       (
        cls     ,
        str_    ):
        kwargs  = {}
        is_list, method, source_type    = cls._parse_method_type(str_)
        pattern_kwargs                  = r'(?:.*?):(.*)'
        pattern                         = r'(?:([\w*]*?)?=)?(.+?)(?:<->|$)'
        kwargs_str                      = re.findall(pattern_kwargs, str_)

        if      len(kwargs_str) != 0    :
            kwargs_str                      = kwargs_str[0]
            kwargs_strs                     = re.findall(pattern, kwargs_str)
            names   = getattr(EXTRACTORS, method).__code__.co_varnames[4:]
            try     :
                for i in range(len(kwargs_strs)):
                    k_name  = kwargs_strs[i][0]
                    is_kist = k_name[:1] == '*'
                    k_name  = k_name.replace('*', '')

                    if      k_name == ''    :
                        k_name  = names[i]
                    kwargs[k_name]  = [cls._parse_value(x) for x in kwargs_strs[i][1].split(slst.LIST_SEPARATOR)]   \
                                        if is_kist                                  \
                                        else   cls._parse_value(kwargs_strs[i][1]   )
            except  :
                raise ValueError(f'Kwargs cannot be parsed {str_}')
        return {
            'is_list'       : is_list       , 
            'method'        : method        , 
            'source_type'   : source_type   , 
            'kwargs'        : kwargs        }
    @classmethod
    def _EasyObj_parser     (
        cls     ,
        *args   ,
        **kwargs):
        '''Parsing logic for ExtractorFunction.
        '''
        if      not len(kwargs) and len(args) == 1 and isinstance(args[0], str) :
            return [], cls._parse_kwargs(args[0])
        else                                                                    :
            return args, kwargs

    @sltl.handle_exception  (
        sltl.Level.ERROR    ,
        params_exc          = [
                'self.method'       ,
                'self.kwargs'       ,
                'self.source_type'  ,
                'self.is_list'      ,
                'r'                 ,
                'c'                 ,
                'x'                 ,
            ]               )
    def extract             (
        self        , 
        r           , 
        c           ,
        x           , 
        **kwargs    ):
        '''Extraction logic.
        '''
        kwargs.update(self.kwargs)

        if      self.is_list    :
            return [self.method(r, c, y, **kwargs) for y in x]
        else                    : 
            return self.method(r, c, x, **kwargs)
class ExtractorCollection   (
    EasyObj ):
    EasyObj_PARAMS  = OrderedDict((
        ('functions'    , {
            'type'      : [ExtractorFunction]   ,
            'default'   : ['JOIN_STRS']         },),))
    
    @classmethod
    def _EasyObj_parser     (
        cls     ,
        *args   ,
        **kwargs):
        '''Parsing logic for Extractor.

            Logic :
                - If `functions` is in kwargs, put the value into args, empty kwargs.
                - If the first arg is a string, split by `slst.EXTRACTORS_SEPARATOR` and put into args.
        '''
        kwargs  = kwargs.copy()
        args    = list(args).copy()

        if      kwargs.get('functions')   :
            args    = [kwargs['functions']]
            del kwargs['functions']
        if      isinstance(args[0], str)    :
            args = [args[0].split(slst.EXTRACTORS_SEPARATOR)]
        return args, kwargs

    def extract             (
        self    ,
        r       ,
        c       ,
        x       ,
        **kwargs):
        start_fn    = self.functions[0]
        if      c == None       and \
                r != None           :
            if      start_fn.source_type == SourceType.CONTEXT  :
                source_type_    = EXTRACTORS.METHOD_SOURCE_TYPE_MAP.get(start_fn.method.__name__, 'TEXT')
                source_type_    = getattr(SourceType, source_type_)
            else                                                : 
                source_type_    = start_fn.source_type
            c   = EXTRACTORS.SOURCE_TYPE_OBJECT_MAP[source_type_](r)
        if      x == None       :
            if      start_fn.source_type == SourceType.CONTEXT  :
                x   = c
            else                                            :
                x   = EXTRACTORS.SOURCE_TYPE_OBJECT_MAP[start_fn.source_type](r)

        for function in self.functions:
            x = function.extract(r, c, x, **kwargs)
        return x
class Extractor             (
    EasyObj ):
    '''Data extractor
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('collections'  , {
            'type'      : [ExtractorCollection  ],
            'default'   : ['JOIN_STRS']         },),))
    
    @classmethod
    def _EasyObj_parser     (
        cls     ,
        *args   ,
        **kwargs):
        '''Parsing logic for Extractor.

            Logic :
                - If `collections` is in kwargs, put the value into args, empty kwargs.
                - If the first arg is a string, split by `slst.COLLECTIONS_SEPARATOR` and put into args.
        '''
        kwargs  = kwargs.copy()
        args    = list(args).copy()

        if      kwargs.get('collections')   :
            args    = [kwargs['collections']]
            del kwargs['collections']
        if      isinstance(args[0], str)    :
            args = [args[0].split(slst.COLLECTIONS_SEPARATOR)]
        return args, kwargs

    @sltl.handle_exception  (
        sltl.Level.ERROR            ,
        params_exc          = None  )
    def extract             (
        self    ,
        r       ,
        c       ,
        x       ,
        **kwargs):
        values  = []
        for collection in self.collections  :
            values.append(collection.extract(r, c, x, **kwargs))
        return values if len(self.collections) > 1 else values[0]
