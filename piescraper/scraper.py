'''
    Base scraper class
    by saledddar@gmail.com, 2018
'''

import re
import saltools

from pyunet import unit_test
from enum import Enum


#-------------------------------------------------------------
#   Testing code
#-------------------------------------------------------------
def mock_do_request(*args,**kwargs):
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

def before_test_request():
    '''
        Executed before testing crawl
    '''
    saltools.save_do_request    = saltools.do_request
    saltools.do_request         = mock_do_request

def after_test_request():
    '''
        Executed before testing crawl
    '''
    saltools.do_request         = saltools.save_do_request
    saltools.save_do_request    = None

#-------------------------------------------------------------
#   Testing code
#-------------------------------------------------------------

class MaxMissingAction(Enum):
    '''
        Options whne max missing for a field is reached.
    '''
    IGNORE      = 0
    EXCEPTION   = 1
    EXIT        = 2

#An adapter to pick the first element
@saltools.handle_exception(level= saltools.Level.ERROR, fall_back_value='')
def adapter_first_index(x):
    return x[0]

class Parser():
    '''
        Parses raw data into the needed information
        Instance    :
            default             : Default value.
            dict_path           : The path to the value in a python dict.
            xpaths              : Xpath expression to extract the value.
            regexs              : Regular expression to extract the value.
            adapters            : Adpaters to adapt extracted value.
    '''
    def __init__(
        self                                ,
        default_value   = 'value'           ,
        dict_path       = ['a']             ,
        xpath           = '//a/text()'      ,
        regex           = '\d+'             ,
        adapter         = lambda x : x[:5]  ,
        ):
        self.default_value = default_value
        self.dict_path      = dict_path
        self.xpath          = xpath
        self.regex          = regex
        self.adapter        = adapter


    @saltools.handle_exception(level=saltools.Level.CRITICAL)
    @unit_test(
        [
            {
            'args'  : [{'a':'Hello world'}] ,
            'assert': 'Hello'}
        ])
    def parse(self,source):
        '''
            Parses the source and extracts information, xpath, regex then adapters are applied.
            Args    :
                source  : The source to be parsed.
            Returns :
                A dict of extracted information.
        '''
        result  = self.default_value
        #Extract json
        if self.dict_path :
            result = saltools.dict_path(source,self.dict_path)
        #Extract xpath
        elif self.xpath :
            result = saltools.find_xpath(source,self.xpath)
        #Extract Regex
        elif self.regex :
            result = re.compile(self.regex).findall(source)
        if self.adapter :
            result = self.adapter(result)
        return result

class Field():
    '''
        A data field.
        Instance    :
            name            : Field name.
            default_value   : Default value.
            required        : Scraper will raise an exception if this field is missing.
            max_missing     : Naximum allowed number of collected data with field missing.
            on_max_missing  : What to do when max_missing is reached.
            parser          : A parser to extract the field from a source.
    '''
    def __init__(
        self                                        ,
        name            = 'field'                   ,
        default_value   = 'value'                   ,
        required        = False                     ,
        max_missing     = 100                       ,
        on_max_missing  = MaxMissingAction.IGNORE   ,
        parser          = Parser()                 ,
        ):
        self.name           = name
        self.default_value  = default_value
        self.required       = required
        self.max_missing    = max_missing
        self.on_max_missing = on_max_missing
        self.parser         = parser

        self.found          = 0
        self.missing        = 0

class Scraper():
    '''
        Base scraper class, contains standard methods and base scraping strcuture
        Scrapers should inherit from this class, override it's method when needed
        Instance    :
            name                : the name or id of the scraper.
            root                : The root url.
            date_format         : Scraped date format, will be converted to YYYY-MM-DD.
            time_format         : Scraped time format, will be converted to HH:MM:SS.
            fields              : Fields definitions.
            before_save         : Executed just before saving the data.
            current_url         : The current url.
            crawl_parser        : Parser to extract the pages urls
            scrape_parser       : Parser to extract the data from page source
    '''
    def __init__(self                       ,
            name           = 'scraper'      ,
            root           = 'root'         ,
            date_format    = '%Y-%m-%d'     ,
            time_format    = '%Y-%m-%d'     ,
            fields         = [
                                Field(
                                    name='field1'                                                       ,
                                    default_value= 'value_1'                                            ,
                                    parser = Parser(None, None, '//div/text()', None, saltools.join_array_text)) ,
                                Field(
                                    name='field2'                                                       ,
                                    default_value= 'value_2'                                            ,
                                    parser = Parser(None, None, None, '\d(\w+)', lambda x:x[0]))        ,
                                Field(
                                    name='field3'                                                       ,
                                    default_value= 'value_3'                                            ,
                                    parser = Parser(None, None, None, None, None))                      , ]
                                            ,
            before_save    = None           ,
            crawl_parser   = Parser(
                                default_value   = ''                ,
                                dict_path       = None              ,
                                xpath           = '//a[1]/@href'    ,
                                regex           = None              ,
                                adapter         = None              ) ,
            scrape_parser  = Parser(
                                default_value   = ''                ,
                                dict_path       = None              ,
                                xpath           = '//a[2]/@href'    ,
                                regex           = None              ,
                                adapter         = None              ) ,
        ):
        self.name           = name
        self.root           = root
        self.date_format    = date_format
        self.time_format    = time_format
        self.fields         = fields
        self.before_save    = before_save
        self.crawl_parser   = crawl_parser
        self.scrape_parser  = scrape_parser

        self.crawled        = set()
        self.scraped        = set()

        self.to_crawl       = set()
        self.to_scrape      = set()

        #Check if root ends with /
        self.root = self.root+ ('/' if self.root[-1] !='/' else '')

    @saltools.handle_exception(level=saltools.Level.CRITICAL)
    @unit_test(
        [
            {
            'args'  : ['just_a_url_1'] ,
            'assert': 'root/just_a_url_1'},
            {
            'args'  : ['just_a_url_2','root_0'] ,
            'assert': 'root_0/just_a_url_2'},
            {
            'args'  : ['https://just_a_url_3'] ,
            'assert': 'https://just_a_url_3'}
        ])
    def full_url(self, url, root = None):
        '''
            Gets the full url from a relatie url.
            Args    :
                url     : The url.
                root    : Custom root, if none, self.root is used.
            Returns     : The full url
        '''
        if url[:4] == 'http':
            return url
        else :
            #Set root to self.root if not specified.
            root    = self.root if not root else root
            root    = root+ ('/' if root[-1] !='/' else '')

            #Check if url starts with /
            url = root+ (url[1:] if url[0] =='/' else url)
        return url

    @saltools.handle_exception(level=saltools.Level.CRITICAL)
    @unit_test(
        [
            {
            'before': before_test_request                       ,
            'args'  : ['']                                      ,
            'assert': {'crawl': ['#next_crawl'], 'scrape': ['#next_scrape']} ,
            'after' : after_test_request                        ,}
        ])
    def crawl(self, url):
        '''
            Crawls a page to extract pages to scrape and to crawl.
            Args    :
                url     : The url to crawl.
            Returns : A dict with a list of urls to scrape and a list of urls to cralws.
        '''

        source  = saltools.do_request(url)

        crawl   = self.crawl_parser.parse(source)
        scrape  = self.scrape_parser.parse(source)

        #Add the urls to the crawling list
        for x in crawl :
            if x not in self.crawled :
                self.to_crawl.add(x)

        #Add the urls to the scraping list
        for x in scrape :
            if x not in self.scraped :
                self.to_scrape.add(x)

        return { 'crawl' : crawl, 'scrape': scrape}

    @saltools.handle_exception(level=saltools.Level.CRITICAL)
    @unit_test(
        [
            {
            'before': before_test_request                       ,
            'args'  : ['']                                      ,
            'assert': {
                'field1': 'scraped_1',
                'field2': 'scraped_2',
                'field3': 'value_3'} ,
            'after' : after_test_request                        ,}
        ])
    def scrape(self, url):
        '''
            Scrape the url for data.
            Args    :
                url : The url to scrape.
            Returns :
                A dict of scraped fields names and their values.
        '''
        source = saltools.do_request(url)
        return self.adapt({
            field.name: field.parser.parse(source) or field.default_value for field in self.fields
        })

    @saltools.handle_exception(level=saltools.Level.CRITICAL)
    def adapt(self, data):
        '''
            Adapt the scraped data.
            Args :
                The data to process
        '''
        return data
