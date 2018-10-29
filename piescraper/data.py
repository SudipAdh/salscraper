'''
    Data handlers
'''
__author__      = 'saledddar'
__email___      = 'saledddar@gmail.com'
__copyright__   = '2018, piescraper'

import re
import json
import saltools
import collections

from saltools   import *

####################################################################################################
#   Tests
####################################################################################################

class TESTS():
    class TestContextParser   ():
        source          = '''
            <!doctype html>
            <a href="value">Hello</a>'''
        test_parse      = [
            {
                'args'  : [source, '']    ,
                'assert': 'value'   }]

        def ic_test_parse():
            return ContextParser('fp1',ParserType.XPATH, '//a/@href')

    class TestField         ():
        source_html     = '''
                <!doctype html>
                <a href="value"></a>
            '''
        source_regex    = '123value123'
        source_json     = json.dumps({'a':{'b':'value'}})
        source_text     = '123value'

        test_parse  = [
            {
                'args'  : [source_html, ''],
                'assert': 'value'},
            {
                'args'  : [source_regex, ''],
                'assert': 'value'},
            {
                'args'  : [source_json, ''],
                'assert': 'value'},
            {
                'args'  : [source_text, ''],
                'assert': 'value'},]

        def ic_test_parse():
            def custom_parser(source):
                return  source[3:]
            def adapter(result):
                return [result[x] for x in result if result[x] and len(result[x])][0]

            return Field(
                name            = 'f1'              ,
                required        = False             ,
                max_missing     = 100               ,
                on_max_missing  = None              ,
                parsers         = [
                    ContextParser('fp1', ParserType.XPATH     , '//a/@href'       ),
                    ContextParser('fp2', ParserType.REGEX     , '\d+([a-z]+)\d+'  ),
                    ContextParser('fp3', ParserType.JSON_PATH , ['a','b']         , pick_first= False),
                    ContextParser('fp4', ParserType.CUSTOM    , custom_parser     , pick_first= False)],
                adapter         = adapter           )

    class TestContainer     ():
        source_html     = '''
                <!doctype html>
                <a href="value"></a>
            '''
        test_parse      = [
            {
                'args'  : [source_html , ''],
                'assert': lambda x:                     \
                    x.values        == {'f1': {'fp1': 'value'}} and \
                    x.result_type   == ResultType.DATA          and \
                    x.name          == 'c1'                     and \
                    x.id            == 'f1'}]

        def ic_test_parse():
            return Container(
                'c1'                    ,
                [
                    Field(
                        'f1'            ,
                        False           ,
                        100             ,
                        None            ,
                        [
                            ContextParser(
                                'fp1'               ,
                                ParserType.XPATH    ,
                                '//a/@href'         )],
                        None          )],
                'f1'                    ,
                ResultType.DATA         ,
                None                    ,
                None                    )

####################################################################################################
#   Code
####################################################################################################

#Predefined adapters
FIELD_ADAPTER_FIRST_VALUE   = lambda x: list(x.values())[0]


class ParserType    (Enum):
    '''
        Parser types.
    '''
    XPATH       = 1
    REGEX       = 2
    CUSTOM      = 3
    JSON_PATH   = 4
    SOURCE      = 5

class ResultType    (Enum):
    URLS    = 1
    TASK    = 2
    DATA    = 3

class SourceType    (Enum):
    URL     = 0
    SOURCE  = 1

class BaseCreatorFromDict():
    '''
        A base for classes that uses dict creators.
        Static  :
            dict    , RECURSIVE_PARAMS  : Parameters that result in a call to creator_from_dict.
    '''

    @classmethod
    def creator_from_dict(cls, params):
        '''
            Creates an instance from a dict of params:
            Args    :
                params  : contains the parameters.
            Returns :
                An instance.
        '''

        kwargs = {}
        for x in params :
            if x in cls.RECURSIVE_PARAMS :
                if isinstance(params[x], collections.Iterable):
                    cls_x       = cls.RECURSIVE_PARAMS[x]
                    kwargs[x]   = [cls_x.creator_from_dict(y) if  not isinstance(y, cls_x) else y for y in params[x]]
                else :
                    kwargs[x]   = cls_x.creator_from_dict(params[x]) if not isinstance(params[x], cls_x) else params[x]
            else :
                kwargs[x]   = params[x]
        return cls(** kwargs)

class Result(BaseCreatorFromDict):
    '''
        A parsing result
        Instance    :
            ResultType  , result_type : The type of the extracted data.
            dict        , value       : Th extracted value.
            string      , id          : The field used as id.
            string      , name        : Name of the container.
    '''

    def __init__(self, values, result_type, id, name):
        self.result_type= result_type
        self.values     = values
        self.id         = id
        self.name       = name

    def __repr__(self):
        '''
            overide.
        '''
        return json.dumps(self.values, indent= 2)

class ContextParser(BaseCreatorFromDict):
    '''
        A context parser.
        Instance    :
            string      , name        : The name or id of the parser, optional, can be used by the adapter in case of multiple parsers.
            string      , expression  : Expression as a json path, regex or xpath, in case of custom parser types, this should point to a function.
            ParserType  , parser_type : The type of the parser, json, xpath, regex or custom.
            boolean     , pick_first  : Picks the first element if the result of expression evaluation is an array.
    '''

    RECURSIVE_PARAMS = {}

    def __init__(
        self            ,
        name            ,
        parser_type     ,
        expression      ,
        source_type     ,
        pick_first      ):

        self.parser_type    = parser_type
        self.expression     = expression
        self.name           = name
        self.source_type    = source_type
        self.pick_first     = pick_first

    @unit_test(TESTS.TestContextParser.test_parse, instance_creator= TESTS.TestContextParser.ic_test_parse)
    @handle_exception(level= Level.ERROR, fall_back_value= '')
    def parse(self, source, url):
        '''
            Prases the container.
            Args    :
                obj     , source: Source to parse.
                string  , url   : Url to parse.
            Returns : obj.
        '''
        result  = []
        source  = source if self.source_type == SourceType.SOURCE else url

        if      self.parser_type    == ParserType.XPATH :
            result  = find_xpath(source, self.expression)

        elif    self.parser_type    == ParserType.REGEX :
            result  = re.compile(self.expression).findall(source)

        elif    self.parser_type    == ParserType.JSON_PATH :
            result  = dict_path(json.loads(source), self.expression)

        elif    self.parser_type    == ParserType.CUSTOM :
            result  = self.expression(source) if self.expression else source

        elif self.parser_type       == ParserType.SOURCE :
            result  =   source

        return safe_getitem(result) if self.pick_first else result

class Field(BaseCreatorFromDict):
    '''
        A data field.
        Instance    :
            string              , name              : Field name.
            obj                 , default_value     : Default value.
            boolean             , required          : Scraper will raise an exception if this field is missing.
            int                 , max_missing       : Naximum allowed number of collected data with field missing, -1 to ignore.
            callable(0)         , on_max_missing    : What to do when max_missing is reached. a function.
            ContextParser list  , parsers           : A list of field parsers to extract the field from a source.
            callable(1)         , adapter           : Adapts the results returned by the parsers.
            int                 , found             : Number of found items.
            int                 , missing           : Number of missing items.
    '''

    RECURSIVE_PARAMS    = {
        'parsers'    : ContextParser}

    def __init__(
        self                ,
        name                ,
        required            ,
        max_missing         ,
        on_max_missing      ,
        parsers             ,
        adapter             ):
        '''
            Args    :
                string              , name              : Field name.
                obj                 , default_value     : Default value.
                boolean             , required          : Scraper will raise an exception if this field is missing.
                int                 , max_missing       : Naximum allowed number of collected data with field missing, -1 to ignore.
                callable(0)         , on_max_missing    : What to do when max_missing is reached. a function.
                ContextParser list  , parsers           : A list of field parsers to extract the field from a source.
                callable(1)         , adapter           : Adapts the results returned by the parsers.
        '''
        self.name           = name
        self.required       = required
        self.max_missing    = max_missing
        self.on_max_missing = on_max_missing
        self.parsers        = parsers
        self.adapter        = adapter

        self.found          = 0
        self.missing        = 0

    @handle_exception()
    def report_missing(self):
        '''
            Increases the max_missing counter and executes on_max_missing if needed.
        '''
        self.missing    += 1
        if self.missing >= self.max_missing and self.max_missing != -1 and self.on_max_missing:
            self.on_max_missing()

    @unit_test(TESTS.TestField.test_parse, instance_creator= TESTS.TestField.ic_test_parse)
    @handle_exception(level= Level.ERROR, fall_back_value= '')
    def parse(self, source, url):
        '''
            Prases the container.
            Args    :
                obj     , source: Source to parse.
                string  , url   : Url to parse.
            Returns : Result list.
        '''
        result  = {}
        for field_parser in self.parsers :
            result[field_parser.name]   = field_parser.parse(source, url)

        result  = self.adapter(result) if self.adapter else result

        if not result:
            self.report_missing()
        return result

class Container(BaseCreatorFromDict):
    '''
        A container for fields or other containers.
        Instance    :
            string          , name              : The name of container.
            string          , id                : Field name used to identify and group different children data from multiple containers.
            Field list      , fields            : A list of fields.
            ResultType      , result_type       : Result type for the container.
            ContextParser   , parsers           : Used to extract the context to which the fields parsers are applied.
            callable(1)     , context_adapter   : Adapts the context result.
            callable(1)     , results_adapter   : Adapts the parsing result.
            callable(2)     , custom_parser     : Takes two arguments(source, url) and provides custom parsing behaviour, must return an list of dict.
    '''

    RECURSIVE_PARAMS    = {
        'fields'    : Field,
        'parsers'   : ContextParser}

    def __init__(
        self            ,
        name            ,
        id              ,
        fields          ,
        result_type     ,
        parsers         ,
        context_adapter ,
        results_adapter ,
        custom_parser   ):
        '''
            Args    :
                string          , name              : The name of container.
                string          , id                : Field name used to identify and group different children data from multiple containers.
                Field list      , fields            : A list of fields.
                ResultType      , result_type       : Result type for the container.
                ContextParser   , parsers           : Used to extract the context to which the fields parsers are applied.
                callable(1)     , context_adapter   : Adapts the context result.
                callable(1)     , results_adapter   : Adapts the parsing result.
                callable(2)     , custom_parser     : Takes two arguments(source, url) and provides custom parsing behaviour, must return an list of dict.
        '''
        self.name           = name
        self.fields         = fields
        self.id             = id
        self.result_type    = result_type
        self.parsers        = parsers
        self.context_adapter= context_adapter
        self.results_adapter= results_adapter
        self.custom_parser  = custom_parser

    @unit_test(TESTS.TestContainer.test_parse, instance_creator= TESTS.TestContainer.ic_test_parse)
    @handle_exception()
    def parse(self, source, url):
        '''
            Prases the container.
            Args    :
                obj     , source: Source to parse.
                string  , url   : Url to parse.
            Returns : Result list.
        '''
        #If a custom parser is present, use it
        if self.custom_parser :
            results = []
            for values in self.custom_parser(source, url) :
                results.append(Result(values, self.result_type, values.get(self.id), self.name))
            return results

        #Get the fields context using the parser
        contexts    = []

        #For each context parser, get the found contexts
        if self.parsers and len(self.parsers):
            for parser  in self.parsers :
                result = parser.parse(source, url)
                if type(result) == type([]):
                    contexts.extend(result)
                else :
                    contexts.append(result)
            #Apply the adapter
            contexts = self.context_adapter(contexts) if self.context_adapter else contexts
        else :
            #If no context, use the source
            contexts = [source]

        results = []
        #For each found context, extract fields values
        for context in contexts :
            values  = {field.name: field.parse(context, url) for field in self.fields}
            results.append(Result(values, self.result_type, values.get(self.id), self.name))

        #Apply the adapters and return the results
        return self.results_adapter(results) if self.results_adapter else results
