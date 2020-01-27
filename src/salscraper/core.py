from    decimal             import  Decimal
from    collections         import  OrderedDict
from    collections.abc     import  Iterable    , Callable
from    enum                import  Enum

from    .                   import  interface   as slsi
from    .                   import  extraction  as slse
from    dateutil.parser     import  parse       as dparse
from    datetime            import  datetime    as dt

import  saltools.logging    as      sltl
import  saltools.common     as      sltc
import  saltools.misc       as      sltm

import  re

FIELD_NONE  = 'Just a string to represent a null value'

class FieldType (
    Enum    ):
    '''Field type.
    '''
    INTEGER             = 0
    FLOAT               = 1
    DECIMAL             = 3
    STRING              = 4
    BOOL                = 5
    DATETIME            = 6
    DATETIME_STR        = 7
    DATETIME_STR_END    = 8
    REQUEST             = 9

class ContainerBase (
    sltc.EasyObj    ):
    '''Base for data containers/processors.

        Args:
            id_         (str                        ): An id.
            extractor   (slse.Extractor             ): A single `Extractor` or a list.
            adapter     (collections.abc.Callable   ): Additional adaption logic for the value returned 
                by the extractor.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('extractor'    , {
            'type'   : slse.Extractor   ,
            'default': None             }),
        ('id_'          , {
            'type'      : str   ,
            'default'   : 'N/A' }),))
    
    def _g_noxt_next    (
        cls         ,
        requests    ):
        requests_noxt   = []
        requests_next   = []

        for request in requests :
            methods = [func.method for coll in request.extractor.collections for func in coll.functions]
            if      slse.EXTRACTORS.NEXT_PAGE in methods    :
                requests_next.append(request)
            else                                            :
                requests_noxt.append(request)
        return requests_noxt, requests_next

    def _extract    (
        self        ,
        r           ,
        c           ):
        '''Generic extraction logic.

            Uses the extractor to get the data from the source.
            Args:
                r       (interface.Response ): Server response.
                c       (object             ): Specific context to be used.
            Returns:
                object  : The parsed value of the field.
        '''
        if      self.extractor != None  :
            return self.extractor.extract(r, c, None)
        else                            :
            return None
    
    def extract     (
        self                ,
        r                   ,
        c           = None  ,
        r_executer  = None  ,
        parser      = None  ,
        r_list      = None  ):
        '''Extracts the data.

            Further manipulation of the data returned by `self._extract`
            Must be overridden 
            Args:
                r   (interface.Response ): Server response.
                c   (object             ): Specific context to be used.
            Returns:
                object  : The parsed value of the field.
        '''
        raise NotImplementedError
class Field         (
    ContainerBase   ):
    EasyObj_PARAMS          = OrderedDict((
        ('type'             , {
            'type'   : FieldType    ,
            'default': 'STRING'     }),
        ('value'            , {
            'default': FIELD_NONE   }),
        ('is_return_value'  , {
            'type'      : bool  ,
            'default'   : False }),
        ('is_save'          , {
            'type'      : bool  ,
            'default'   : True  }),
        ('data_adapter'     , {
            'type'      : slse.Extractor    ,
            'default'   : None              }),))
    FIELD_TYPE_OBJECT_MAP   = {
            FieldType.INTEGER   : lambda x: int(float(x))               ,
            FieldType.FLOAT     : float                                 ,
            FieldType.DECIMAL   : Decimal                               ,
            FieldType.STRING    : str                                   ,
            FieldType.BOOL      : sltc.EasyObj.DEFAULT_PARSERS[bool]    ,
            FieldType.DATETIME  : sltc.EasyObj.DEFAULT_PARSERS[dt]      ,
        }
    
    @classmethod
    def _parse_value (
        cls                     ,
        str_                    ,
        type_                   ,
        is_return_value = False ):
        '''Parses the a string using the correct type parsing logic.

            Args:
                str_            (str        ): The string to parse.
                type_           (FieldType  ): Type.
                is_return_value (bool       ): If True, return str_ on failure, could be harmful when saving to
                    a database.
            Return:
                object  : The parsed value.
        '''
        if      str_ in [None, '']  :
            return None
        value   = None
        if      type_ == FieldType.REQUEST          :
            if      not isinstance(str_, list)  :
                str_    = [str_]
            for x in str_   :
                assert isinstance(x, slsi.Request), 'Value returned by extractor is not of type REQUEST'
            value   = str_        
        elif    type_ == FieldType.DATETIME_STR     :
            try     :
                value   = cls.FIELD_TYPE_OBJECT_MAP[FieldType.DATETIME](str_).isoformat()
                value   = value[:19]
            except  :
                value   = str_
        elif    type_ == FieldType.DATETIME_STR_END :
            try     :
                value   = cls.FIELD_TYPE_OBJECT_MAP[FieldType.DATETIME](str_, False).isoformat()
                value   = value[:19]
            except  :
                value   = str_
        else                                        :
            try     :
                value   = cls.FIELD_TYPE_OBJECT_MAP[type_](str_)
            except  :
                if      is_return_value :
                    value   = str_
        return value

    @sltl.handle_exception  (
        sltl.Level.ERROR    ,
        params_exc          = [
                'self.id_'  ,
                'r'
            ]               )
    def extract             (
        self                ,
        r                   ,
        c           = None  ,
        r_executer  = None  ,
        parser      = None  ,
        r_list      = None  ):
        if self.value != FIELD_NONE :
            return self.value

        value   = self._extract(r, c)
        value   = value if self.data_adapter == None else self.data_adapter.extract(r, c, value)
        value   = self._parse_value(value, self.type, self.is_return_value)
        
        if      self.type       != FieldType.REQUEST    \
                or r_executer   == None                 :
            ret_value   = value
        else                                            :
            value = r_executer(value[0])
            value = parser.parse(value, r_executer, r_list)
            ret_value   = list(value.values())[0]
        return ret_value
        
class Bucket        (
    ContainerBase   ):
    EasyObj_PARAMS          = OrderedDict((
        ('skip_on'      , {
            'type'      : slse.Extractor    ,
            'default'   : None              }),
        ('fields'       , {
            'type'      : [ContainerBase]   ,
            'default'   : None              }),
        ('is_skip_None' , {
            'type'      : bool  ,
            'default'   : False }),
        ('data_adapter' , {
            'type'      : slse.Extractor    ,
            'default'   : None              }),))
    
    @classmethod
    def _EasyObj_parser     (
        cls     ,
        *args   ,
        **kwargs):
        '''Parsing logic for Bucket.

            Logic:
                - If the fields are in `args`, move into `kwargs['fields']`
                - For each field, check if the field's kwargs/args to determine if a sub bucket:
                    - If `args` and `args[2]` is a list or `kwargs` and there is a key 'field'.
        '''
        args    = list(args).copy()
        kwargs  = kwargs.copy()

        if      len(args) > 2   :
            kwargs['fields'] = args[2]
            del args[2]
        
        for i in range(len(kwargs['fields'])):
            value   = kwargs['fields'][i]
            if      isinstance(value, list) :
                if      isinstance(sltm.g_path(value,2, is_return_last=False), list)    :
                    kwargs['fields'][i] = Bucket(*value)
                else                                                                    :
                    kwargs['fields'][i] = Field(*value)
            elif    isinstance(value, dict) :
                if      'fields' in value   :
                    kwargs['fields'][i] = Bucket(**value)
                else                        :
                    kwargs['fields'][i] = Field(**value)
        
        return args, kwargs
    
    def extract (
        self                ,
        r                   ,
        c           = None  ,
        r_executer  = None  ,
        parser      = None  ,
        r_list      = None  ):
        if      self.skip_on and self.skip_on.extract(r, c, None)   :
            return []
        contexts    = self._extract(r, c) if self.extractor != None else [c]
        if      contexts == None                :
            contexts    = [c]
        if      not isinstance(contexts, list)  :
            contexts    = [contexts]
        data        = []
        for context in contexts :
            if      self.is_skip_None and context == None   :
                continue
            data.append(
                    {   
                        field.id_: field.extract(
                            r           , 
                            context     ,
                            r_executer  ,
                            parser      ,
                            r_list      ) for field in self.fields
                    }
                )
        
        return self.data_adapter.extract(r, c, data) if self.data_adapter != None else data
class Rule          (
    ContainerBase   ):
    EasyObj_PARAMS  = OrderedDict((
        ('buckets'          , {
            'type'      : [Bucket]  ,
            'default'   : []        }),
        ('requests'         , {
            'type'      : [Field]   ,
            'default'   : []        }),
        ('data_adapter'     , {
            'type'      : slse.Extractor    ,
            'default'   : None              }),
        ('is_stop_empty'    , {
            'type'      : bool  ,
            'default'   : True  }),))
    
    def _on_init    (
        self    ):
        for request in self.requests    :
            request.type    = FieldType.REQUEST
    
    def extract (
        self                ,
        r                   ,
        c           = None  ,
        r_executer  = None  ,
        parser      = None  ,
        r_list      = None  ):
        if      self._extract(r, c) in [None, []]   :
            return
        
        data        = {
            b.id_   : b.extract(
                r           ,
                c           ,
                r_executer  ,
                parser      ,
                r_list      ) for b in self.buckets }
        len_data    = sum(map(len, data.values()))
        requests_noxt, requests_next = self._g_noxt_next(self.requests)
        requests    = []
        for request in requests_noxt+ requests_next :
            if      request in requests_next    and \
                    self.is_stop_empty          and \
                    len(requests)   == 0        and \
                    len_data        == 0            :
                    break
            x           = request.extract(r, c)
            if      isinstance(x, list) :
                requests.extend(x)
            else                        :
                requests.append(x)
            
        if      self.data_adapter != None   :
            data = self.data_adapter.extract(r, None, data)
        return data, requests
class Parser        (
    sltc.EasyObj    ):
    EasyObj_PARAMS  = OrderedDict((
        ('rules'        , {
            'type'  : [Rule]    }),))

    @sltl.handle_exception  (
        params_exc  = ['r'] )
    def parse               (
        self                ,
        r                   ,
        r_executer          ,
        r_list              ,
        exporter    = None  ):
        data            = {}
        rule_found      = False
        for rule in self.rules:
            extracted   = rule.extract(
                r          ,
                None       ,
                r_executer , 
                self       ,
                r_list     )
            if      extracted == None   :
                continue
            rule_found  = True

            e_buckets, e_requests   = extracted
            for bucket in e_buckets   :
                data[bucket] = e_buckets[bucket]
        
            for e_request in e_requests : 
                r_list.append(e_request)

        assert rule_found, 'No rule is found for the given response.'
        
        if      exporter and len(data) :
            exporter(data)
        
        return data
                