'''
'''
from    saltools.common     import  EasyObj         , MY_CLASS  
from    .adapter            import  Adapter
from    saltools.web        import  g_xpath
from    saltools.misc       import  g_path
from    decimal             import  Decimal
from    collections         import  OrderedDict
from    collections.abc     import  Iterable
from    .                   import  interface
from    enum                import  Enum

import  saltools.logging    as      stl

import  re

class FieldType         (Enum):
    '''Field type.

        Bucket field type.
    '''
    INTEGER = 0
    FLOAT   = 1
    DECIMAL = 3
    STRING  = 4
    BOOL    = 5
class ExtractorType     (Enum):
    '''Extractor type.

        Extractor type to specify while parsing sources.
    '''
    XPATH       = 0
    REGEX       = 1
    OBJ_PATH    = 2
    CUSTOM      = 3
    EQUALS      = 4
class SourceType        (Enum):
    '''Resource Type.

        The resource type to be parsed for a given request.

    '''
    REQUEST_URL     = 0
    RESPONSE_URL    = 1
    HTML            = 2
    JSON            = 3
    TEXT            = 4
    CONTENT         = 5
    CONTEXT         = 6

#Maps each source type to a lambda that generates the correct object.
SOURCE_TYPE_OBJECT_MAP  = {
    SourceType.REQUEST_URL  : lambda response: response.request_url         ,
    SourceType.RESPONSE_URL : lambda response: response.response_url        ,
    SourceType.HTML         : lambda response: response.html_tree           ,
    SourceType.JSON         : lambda response: response.json                ,
    SourceType.TEXT         : lambda response: response.text                ,
    SourceType.CONTENT      : lambda response: response.content             ,}
#Maps each field type to its predefined type
FIELD_TYPE_OBJECT_MAP   = {
    FieldType.INTEGER   : int       ,
    FieldType.FLOAT     : float     ,
    FieldType.DECIMAL   : Decimal   ,
    FieldType.STRING    : str       ,
    FieldType.BOOL      : bool      }

class Extractor     (EasyObj):
    '''Content extractor.

        Does content extraction for all content types found ExtractorType.

        Args:
            type        (ExtractorType              ): The type of the extractor.
            source_type (SourceType                 ): The type of source to extract from.
            expression  (obj                        ): Parsing expression, the type depends on `self.type`,
                in case of `ExtractorType.CUSTOM`, expression must be a `Callable` with a single argument that 
                returns a `list` or `None`.
            adapter     (collections.abc.Callable   ): Performs custom logic on returned results,
                takes two parameters: 'response' and  `list`.
    '''

    EasyObj_PARAMS  = OrderedDict((
        ('type'         , {
            'default'   : ExtractorType.XPATH       , 
            'type'      : ExtractorType             }),
        ('source_type'  , {
            'default'   : SourceType.CONTEXT        , 
            'type'      : SourceType                }),
        ('adapter'      , {
            'type'      : Adapter       ,
            'default'   : None          }),
        ('expression'   , {}                        )))

    @stl.handle_exception(
        level       = stl.Level.ERROR   , 
        params_exc  = [
            'self.type'             ,
            'self.source_type'      ,
            'self.adapter.functions',
            'self.expression'       ,
            'response.request_url'  ,])
    def extract(
        self            ,
        response        ,
        context = None  ):
        '''Extract data from the given resource.

            Extracts data from `response` using the `ExtractorType` and `expression`.

            Args:
                response    (interface.Response ): The response to parse.
                context     (Object             ): If provided, used instead of parsing response content.
            Returns:
                list   : The list  of data collected.
        '''  

        source  =   context if self.source_type == self.source_type.CONTEXT \
                    else SOURCE_TYPE_OBJECT_MAP[self.source_type](response)
        result  = None
        if      self.type == ExtractorType.XPATH     :
            result  = g_xpath(source, self.expression)
        elif    self.type == ExtractorType.REGEX     :
            result  = re.compile(self.expression).findall(source)
        elif    self.type == ExtractorType.OBJ_PATH  :
            result  = g_path(source, self.expression, return_last= False)
        elif    self.type == ExtractorType.CUSTOM    :
            result  = self.expression(source)   if self.expression != None else  source
        elif    self.type == ExtractorType.EQUALS    :
            result  = source  if source == self.expression else None
        
        if self.adapter:
            return self.adapter.adapt(response, context, result)
        else :
            return result
class ExtractorBase (EasyObj):
    '''Base for all classes that use `Extrator`

        Implements simple extraction logic using `Extractor`.

        Args:
            id_         (str                                ): An id.
            extractor   (Extractor                          ): A single `Extractor` or a list.
            adapter     (collections.abc.Callable           ): In case of many extractors, the adapter is used to 
                combine the multiple values returned by the extractors into one, args for the adapter are the source,
                response and a list of extracted values, arguments are: response, context, value/s.
            is_pipeline (bool                       :False  ): If `True`, the list of extractors are applied in 
                sequence to the source.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('id_'              , {
            'default'   : 'N/A'}    ),
        ('extractor'        , {
            'type'   : Extractor                    ,
            'default': None                         }),
        ('adapter'          , {
            'type'      : Adapter   ,
            'default'   : None      }),
        ('is_pipeline'      , {
            'type'      : bool      ,
            'default'   : False     ,
            'parser'    : bool      }),))
    
    def _extract(
        self    ,
        response,
        context ):
        '''Extracts the data.

            Uses the extractor/s to get the data from the source.
            Args:
                response    (interface.Response  ): Server response.
                context     (object             ): Specific context to be used.
            Returns:
                object  : The parsed value of the field.
        '''
        if      self.extractor == None              :
            return 
        if      isinstance(self.extractor, list)    :
            if      self.is_pipeline    :
                for extractor in self.extractor    :
                    context     = extractor.extract(response, context)
                value   = context
            else                        :
                value  = [ 
                    x.extract(response, context) for x in self.extractor]
        else    :
            value  = self.extractor.extract(response, context)
        return self.adapter.adapt(response, context, value) if self.adapter else value
    def extract(
        self    ,
        response,
        context ):
        '''Extracts the data.

            Further manipulation of the data returned by `self._extract`
            Must be overridden 
            Args:
                response(interface.Response ): Server response.
                context (object             ): Specific context to be used.
            Returns:
                object  : The parsed value of the field.
        '''
        raise NotImplementedError
class Field         (ExtractorBase):
    '''A single parsing element.

        A single parsing element.

        Args:
            type        (FieldType                  ): Field type.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('type'     , {
            'type'   : FieldType            ,
            'default': FieldType.STRING     }),
        ('value'    , {
            'default': None     }),))
    
    def extract(
        self    ,
        response,
        context ):
        if self.value   :
            return self.value
        value   = self._extract(response, context)
        try             :
            return FIELD_TYPE_OBJECT_MAP[self.type](value)
        except          :
            return value
class Job           (ExtractorBase):
    '''Job to be performed by the scraper.

        A Request to be executed by the scraper on the fly.

        Args:
            method          (interface.Method   ): Requests method.
            request_adapter (Adapter            ): Request adapter, params are `interface.response`, context (`object`), 
                extracted values (`list`, `object`), returns a `list` of `Interface.Request`.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('request_adapter'  , {
            'type'      : Adapter           ,
            'default'   : Adapter('GET')    },),))

    def extract(
        self            ,
        response        ,
        context = None  ):
        args        = self._extract(response, context)
        return self.request_adapter.adapt(
            response    , 
            context     , 
            args        )
class Bucket        (ExtractorBase):
    '''Data collection bucket.

        Data and urls extraction logic.

        Args:
            buckets         (Bucket     ): Sub-buckets.
            fields          (Field      ): Fields.
            job             (Job        ): A new request to be executed by the scraper.
            data_adapter    (Adapter    ): Bucket adapter.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('buckets'          , {'type': MY_CLASS , 'default': [] }),
        ('fields'           , {'type': Field    , 'default': [] }),
        ('jobs'             , {'type': Job      , 'default': [] }),
        ('is_empty_on_None' , {
            'type'      : bool      ,
            'default'   : False     ,
            'parser'    : bool      }),
        ('data_adapter'     , {
            'type'      : Adapter   ,
            'default'   : None      })))

    def extract(
        self            ,
        response        ,
        context = None  ):

        data_dicts      = []
        if      self.extractor  != None :
            bucket_contexts = self._extract(response, context)
            if      self.is_empty_on_None   :
                return []
        else                            :
            bucket_contexts = [None]
        if      not isinstance(bucket_contexts, list):
            bucket_contexts  = [bucket_contexts]
            
        for bucket_context in bucket_contexts   :
            context_dict    = {}
            
            for field in self.fields    :
                context_dict[field.id_]   = field.extract(response, bucket_context)
            for bucket in self.buckets  :
                context_dict[bucket.id_]  = {
                    'data'      : bucket.extract(response, bucket_context)  ,
                    'adapter'   : bucket.adapter                            }
            
            for job in self.jobs    :
                context_dict[job.id_]     = job.extract(response, bucket_context)
            
            data_dicts.append(context_dict)
        return data_dicts

class ParsingRule   (EasyObj):
    '''Single parsing rule.
        
        A single parsing rule.

        Args:
            source_selector (Extractor      ): Extractor to select the source.
            buckets         (list, Bucket   ): A list of buckets to collect data.
            jobs            (list, Job      ): A list of jobs to collect new urls, jobs.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('source_selector'  , {'type': Extractor    }),
        ('buckets'          , {
            'type'      : Bucket        ,
            'default'   : []            }),
        ('jobs'             , {
            'type'      : Job   ,
            'default'   : []    }),
        ('data_adapter'     , {
            'type'      : Adapter   ,
            'default'   : None      }),))

    def check(
        self        ,
        source      ):
        '''Checks if the rule is a match for the given source.

            Checks if the rule is a match for the given source, The correct source should
            be passed depending on `self.source_selector`.

            Args:
                source  (object ): The source to parse.
            Returns:
                bool    : True if the source should be parsed by this rule.
        '''
        return True if self.source_selector.extract(source) else False
class Parser        (EasyObj):
    '''Parsing logic.

        Implements the parsing logic for a given website.

        Tests a given resource (`Interface.Response`) against a set of rules, if a match is found, the resource is parsed
            following that rule. 
        The resource is tested against the rules depending on the source type following `SourceType` enum order, 


        Args:
            rules           (ParsingRule                    ): Parsing rules.
            is_unique_rule  (bool                   : True  ): If True, when a given resource is matched with a rule,
                no further rules are tested against it. 
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('rules'            , {'type'   : ParsingRule   }),
        ('is_unique_rule'   , {'default': True          })))

    def parse(
        self    ,
        response):
        '''Parses the response using the correct rule.

            Parses the web response using the correct rule following the order
                in SourceType

            Args:
                response    (interface.Response ): The response object.
            Returns:
                list, ParserResult  : The parsing result generated by all matching parsing rules.
        '''
        data            = {}
        requests        = []
        rule_found      = False
        
        for rule in self.rules:
            if      rule.check(response):
                for b in rule.buckets:
                    data[b.id_]    = {
                        'data'      : b.extract(response)   ,
                        'adapter'   : b.data_adapter        }
                for j in rule.jobs  :
                    requests        +=j.extract(response)
                
                rule_found  = True

                if      self.is_unique_rule and rule_found:
                    break

            if      self.is_unique_rule and rule_found:
                break
        
        assert rule_found, 'No rule is found for the given response.'
        
        return data, requests, rule.data_adapter
                