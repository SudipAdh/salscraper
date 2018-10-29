'''
    Base scraper class.
'''
__author__      = 'saledddar'
__email___      = 'saledddar@gmail.com'
__copyright__   = '2018, piescraper'

import re
import saltools

from time       import sleep
from pyunet     import unit_test
from enum       import Enum
from saltools   import Level
from .data      import *
from .interface import *

####################################################################################################
#   Testing code
####################################################################################################

class TESTS():

    class TestParser()  :
        source  =   '''
                <div class="c1">
                urls::[
                    url1,
                    url2,
                    url3
                    ]
                </div>
                <div class="fields">
                    <a>value1</a>
                    <a>value2</a>
                </div>
            '''

        test_join_results       = [
            {
                'args'      : [
                    [
                        Result(
                            values      = {
                                'field1': 'value1',
                                'field3': 'value3'} ,
                            name        = 'name1'       ,
                            id          = 'id1'         ,
                            result_type = ResultType.DATA),
                        Result(
                            values      = {
                                'field1': 'valuex',
                                'field2': 'value2',
                                'field4': 'value4'} ,
                            name        = 'name1'       ,
                            id          = 'id1'         ,
                            result_type = ResultType.DATA)]],
                'assert'    : lambda x: x.name      == 'name1' and   \
                                        x.values    == {
                                            'field1': 'value1',
                                            'field3': 'value3',
                                            'field2': 'value2',
                                            'field4': 'value4'}},
            {
                'args'      : [
                    [
                        Result(
                            values      = {'field1': 'value1', 'field3': 'value3'},
                            name        = 'namex'           ,
                            id          = 'id1'             ,
                            result_type = ResultType.DATA   ),
                        Result(
                            values      = {'field1': 'valuex', 'field2': 'value2', 'field4': 'value4'},
                            name        = 'namex'           ,
                            id          = 'id1'             ,
                            result_type = ResultType.DATA   )]],
                'assert'    : lambda x: x.name      == 'namex' and \
                                        x.values    == {'field1': 'value1', 'field3': 'value3'}}]
        test__get_rules         = [
            {
                'args'      : ['root/just_a_url_1'],
                'assert'    : lambda x: len(x)==2},
            {
                'args'      : ['root/just_a_abc_2'],
                'assert'    : lambda x: len(x)==2}]
        test_parse              = [

            ]

        def ic_join_results ():
            return Parser(containers_adapters= {'namex': lambda x: x[0].values})
        def ic___get_rules  ():
            return Parser(
                rules       = [
                        ParsingRule('root/[a-z_]+\d')               ,
                        ParsingRule('root/just_a_[a-z]+_\d')    ]   ,
                containers_adapters = {}                            ,
                )
        def ic_test_parse   ():
            return Parser(
                rules       = [
                        ParsingRule('root/[a-z_]+\d')               ,
                        ParsingRule('root/just_a_[a-z]+_\d')    ]   ,
                containers_adapters = {}                            ,
                )

    class TestScraper() :
        test__adjust_results    = [
            {
                'args'      : [
                    [
                        Result(
                            values      = {
                                'field1': 'value1',
                                'field3': 'value3'} ,
                            name        = 'name1'                       ,
                            id          = 'id1'                         ,
                            result_type = ResultType.DATA               ),
                        Result(
                            values      = {
                                'field1': 'valuex',
                                'field2': 'value2',
                                'field4': 'value4'} ,
                            name        = 'name1'                       ,
                            id          = 'id1'                         ,
                            result_type = ResultType.DATA               ),
                        Result(
                            values      = {
                                'field1': 'value1',
                                'field2': 'value2'}                     ,
                            name        = 'name2'                       ,
                            id          = 'id1'                         ,
                            result_type = ResultType.DATA               ),
                        Result(
                            values      = {
                                'field3': 'value3',
                                'field4': 'value4'} ,
                            name        = 'name2'                       ,
                            id          = 'id1'                         ,
                            result_type = ResultType.DATA               )]],
                'assert'    : lambda x: x[0].values         == {'field1': 'value1', 'field3': 'value3', 'field2': 'value2', 'field4': 'value4'} and \
                                        x[0].name           ==  'name1'             and \
                                        x[0].result_type    == ResultType.DATA      and \
                                        x[0].id             == 'id1'                and \
                                        x[1].values         == {'field1': 'value1', 'field2': 'value2', 'field3': 'value3', 'field4': 'value4'} and \
                                        x[1].name           ==  'name2'             and \
                                        x[1].result_type    == ResultType.DATA      and \
                                        x[1].id             == 'id1'}]
        test__full_url          = [
            {
                'args'  : ['just_a_url_1','root'],
                'assert': 'root/just_a_url_1'},
            {
                'args'  : ['just_a_url_2', 'root_0'],
                'assert': 'root_0/just_a_url_2'},
            {
                'args'  : ['https://just_a_url_3','root'],
                'assert': 'https://just_a_url_3'}]

    class Mocks():
        def mock_do_request(*args, **kwargs):
            '''
                A mock for saltools.do_request
            '''
            return '''
                <root>
                <a href="#next_crawl"></a>
                <a href="#next_scrape"></a>
                <div>scraped_1</div>
                1scraped_2
                </root>
            '''
        def before_do_request():
            '''
                Executed before testing crawl
            '''
            saltools.save_do_request = saltools.do_request
            saltools.do_request = mock_do_request
        def after_do_request():
            '''
                Executed before testing crawl
            '''
            saltools.do_request = saltools.save_do_request
            saltools.save_do_request = None


####################################################################################################
#   Main code
####################################################################################################

class ParsingRule(BaseCreatorFromDict):
    '''
        A parsing rule for a url pattern.
        Instance    :
            string      , url_re      : Regular expression to identify urls.
            Container   , containers  : Data containers.
    '''

    RECURSIVE_PARAMS    = {
        'containers'    : Container}

    def __init__(
        self            ,
        url_re          ,
        containers      ):
        '''
            Args    :
                string      , url_re      : Regular expression to identify urls.
                Container   , containers  : Data containers.
        '''
        self.url_re             = re.compile(url_re)
        self.containers         = containers

class Parser(BaseCreatorFromDict):
    '''
        Holds the arsing logic for a scraper.
        Instance    :
            ParsingRule list    , rules                   : The parsing rules for different url patterns.
            dict                , containers_adapters     : A dict containing adapters to join multiple field containers.
    '''

    RECURSIVE_PARAMS    = {
        'rules'    : ParsingRule}

    def __init__(
        self                    ,
        rules                   ,
        containers_adapters     ):
        '''
            Ars    :
                ParsingRule list    , rules                   : The parsing rules for different url patterns.
                dict                , containers_adapters     : A dict containing adapters to join multiple field containers.
        '''
        self.rules                  = rules
        self.containers_adapters    = containers_adapters

    @unit_test(TESTS.TestParser.test__get_rules, instance_creator= TESTS.TestParser.ic___get_rules)
    @saltools.handle_exception()
    def __get_rules(self, url):
        '''
            Get the parsing rules for the given url.
            Args    :
                url     : The url to parse.
            Returns : The parsing rules for the given url.
        '''
        rules   = [x for x in self.rules if x.url_re.match(url)]

        assert len(rules)>0,'No parsing rules are found for {}'.format(url)

        return rules

    @unit_test(TESTS.TestParser.test_parse, instance_creator= TESTS.TestParser.ic_test_parse)
    @saltools.handle_exception()
    def parse(self, source, url):
        '''
            Parses the source of the given url using the correct rule.
            Args    :
                source  : The html source.
                url     : The url.
        '''
        #Get parsing rules
        rules   = self.__get_rules(url)
        results = []

        for rule in rules :
            for container in rule.containers :
                results.extend(container.parse(source, url))

        return results

    @unit_test(TESTS.TestParser.test_join_results, instance_creator= TESTS.TestParser.ic_join_results)
    @saltools.handle_exception()
    def join_results(self, results):
        '''
            Join containers using the specified functions.
            Args    :
                containers  : Containers to join.
        '''
        if not len(results):
            return None

        joined_result  = {}
        adapter = self.containers_adapters.get(results[0].name)

        #If an adapter is specified
        if adapter  :
            joined_result = adapter(results)
        else        :
            for result in results:
                for key in result.values.keys():
                    joined_result[key] = result.values[key] if not joined_result.get(key) else joined_result[key]

        return Result(joined_result, name= results[0].name, result_type= results[0].result_type, id= results[0].id)

    def creator_from_dict(params):
        '''
            Creates an instance from a dict of params:
            Args    :
                params  : contains the parameters.
            Returns :
                An instance.
        '''
        params['rules']    = [ParsingRule.creator_from_dict(x) for x in params['rules']]
        return Parser(** params)

class Scraper(BaseCreatorFromDict):
    '''
        Base scraper class, contains standard methods and base scraping strcuture
        Scrapers should inherit from this class, override it's method when needed
        Instance    :
            string          , name                : the name or id of the scraper.
            string,         , root                : The root url.
            string set      , to_crawl            : The urls to crawl first.
            Parser          , parser              : Parsing rules for urls.
            Logger          , logger              : Logger.
            int             , request_rate        : Maximum number of requests allowed per minute.
            InterfaceBase   , interface           : Interface for sending requests to servers.
            string set      , crawled             : Urls already crawled.
            int             , sleep_time          : Time in seconds to wait between each request.
            dict list       , collected           : Collected data.
    '''

    RECURSIVE_PARAMS    = {
        'parser'    : Parser}

    def __init__(
        self            ,
        name            ,
        root            ,
        to_crawl        ,
        parser          ,
        logger          ,
        request_rate    ,
        interface       ):
        '''
            Args    :
                string          , name                : the name or id of the scraper.
                string,         , root                : The root url.
                string list     , to_crawl            : The urls to crawl first.
                Parser          , parser              : Parsing rules for urls.
                Logger          , logger              : Logger.
                int             , request_rate        : Maximum number of requests allowed per minute.
                InterfaceBase   , interface           : Interface for sending requests to servers.
        '''
        self.name               = name
        self.root               = root
        self.to_crawl           = set(to_crawl)
        self.parser             = parser
        self.logger             = logger
        self.request_rate       = request_rate
        self.interface          = interface

        self.crawled            = set()

        # Check if root ends with /
        self.root               = self.root + ('/' if self.root[-1] != '/' else '')
        self.sleep_time         = 60.0/request_rate
        self.collected          = []

    @unit_test(TESTS.TestScraper.test__full_url)
    @saltools.handle_exception()
    def __full_url(self, url, root= None):
        '''
            Gets the full url from a relative url.
            Args    :
                url     : The url.
                root    : Custom root, if none, self.root is used.
            Returns     : The full url
        '''

        root    = self.root if not root else root

        if url[:4] == 'http':
            return url
        else:
            root = root + ('/' if root[-1] != '/' else '')
            # Check if url starts with /
            url = root + (url[1:] if url[0] == '/' else url)

        return url

    @saltools.handle_exception()
    def __parser_rec(self, url):
        '''
            Uses the parser to get the desired data, if the parser returns a url instead, the method is recursively called.
            Args    :
                url     : The url to parse.
        '''
        data            = []
        source          = self.interface.request_source(self.build_request(url))

        self.logger.log(Level.INFO,{'Action':'Sleep'})
        sleep(self.sleep_time)

        results         = self.parser.parse(source, url)
        self.crawled.update(url)

        #For result in results
        for result in results:
            #If some tasks, scrape them all
            if result.result_type       == ResultType.TASK  :
                for url in result.values.values() :
                    data.extend(self.__parser_rec(url))
            #If urls, add them to the crawling stack
            elif result.result_type     == ResultType.URLS   :
                self.to_crawl.update([x for x in result.values.values() if x not in self.crawled])

            #If data, return the values
            else                                        :
                data.append(result)
        return data

    @unit_test(TESTS.TestScraper.test__adjust_results)
    @saltools.handle_exception()
    def __adjust_results(self, results):
        '''
            Adjsuts data collected from multiple sources to a single data structure.
            Args    :
                data    : The data containers.
        '''
        data    = []

        #Call join_containers for containers with the same names and ids
        names   = set([result.name for result in results])
        for name in names :
            same_names  = [result for result in results if result.name == name]
            ids         = set([same_name.id for same_name in same_names])
            for id in ids :
                #Get containers with same ids
                same_ids = [same_name for same_name in same_names if same_name.id == id]

                #For each field
                data.append(self.parser.join_results(same_ids))
        data  = list(sorted(data, key= lambda x: x.name))
        data  = list(sorted(data, key= lambda x: x.id))
        return data

    @saltools.handle_exception()
    def __start(self):
        '''
            Crawler loop.
        '''
        while len(self.to_crawl) and not self.stop_on():
            url     = self.to_crawl.pop()
            data    = self.__parser_rec(url)

            #Adjust the data and add it to the collected data list
            self.collected.extend(self.__adjust_results(data))


    @saltools.handle_exception()
    def start(self):
        '''
            Starts the scraper.
        '''
        self.logger.log(Level.INFO, {'Action':'Start'})
        self.on_start()
        self.logger.log(Level.INFO, {'Action':'Started'})
        self.__start()

    @saltools.handle_exception()
    def stop(self):
        '''
            Stops the scraper.
        '''
        self.logger.log(Level.INFO, {'Action':'Stop'})
        self.on_stop()
        self.logger.log(Level.INFO, {'Action':'Stopped'})

    @saltools.handle_exception()
    def build_request(self, url):
        '''
            Executed before start.
        '''
        return {
            'is_post'   : False ,
            'url'       : url   ,
            }

    @saltools.handle_exception()
    def stop_on(self):
        '''
            Stops the scraper if returns True.
        '''
        return False

    @saltools.handle_exception()
    def on_start(self):
        '''
            Executed before start.
        '''
        pass

    @saltools.handle_exception()
    def on_stop(self):
        '''
            Executed before stop.
        '''
        pass

    def creator_from_dict(params):
        '''
            Creates an instance from a dict of params:
            Args    :
                params  : contains the parameters.
            Returns :
                An instance.
        '''
        params['parser']    = Parser.creator_from_dict(params['parser'])
        return Scraper(** params)
