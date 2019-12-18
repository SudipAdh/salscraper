from    salscraper          import  extraction  as  slse
from    salscraper          import  interface   as  slsi
from    salscraper          import  core        as  slsc
from    datetime            import  datetime    as dt

from    os.path             import  join    , dirname
from    decimal             import  Decimal
from    pprint              import  pprint

import  saltools.web        as      sltw
import  saltools.logging    as      sltl

import  pytest 

ROOT        = dirname(__file__)
FIX_PATH    = join(ROOT, 'fixtures')

R_01        = slsi.Response.pickle_load(join(FIX_PATH,'r_01.pickle'))
R_02        = slsi.Response.pickle_load(join(FIX_PATH,'r_02.pickle'))

class TestField     (
    ):
    def test_parse_value    (
        self    ):
        values  = {
            '1'             : slsc.FieldType.INTEGER        ,
            '2.5'           : slsc.FieldType.INTEGER        ,
            '23.50'         : slsc.FieldType.FLOAT          ,
            '23.5'          : slsc.FieldType.DECIMAL        ,
            '2019-01-02'    : slsc.FieldType.DATETIME       ,
            '2019-01-03'    : slsc.FieldType.DATETIME_STR   ,
            'hh'            : slsc.FieldType.DATETIME_STR   ,
            'y'             : slsc.FieldType.BOOL           ,
            'something'     : slsc.FieldType.STRING         }
        
        assert [slsc.Field._parse_value(*item) for item in values.items()]  == [
            1                                           ,
            2                                           ,
            23.5                                        ,
            Decimal(23.5)                               ,
            dt(year=2019, month=1, day= 2)              ,
            dt(year=2019, month=1, day= 3).isoformat()  ,
            'hh'                                        ,
            True                                        ,
            'something'                                 ]
        assert slsc.Field._parse_value('23.5', slsc.FieldType.BOOL, True)   == '23.5' 
    def test_extract        (
        self    ):
        case_A1 = slsc.Field(
            **  {
            'id_'       : 'F1'                                                                      ,
            'extractor' : r'x:(//span[@itemprop="text"])[8]//text()-->p-->r:[\d,]+-->p-->?:,<-><()>',
            'type'      : 'FLOAT'                                                                   })
        case_A2 = slsc.Field(
            **  {
            'id_'       : 'F2'                                          ,
            'extractor' : r'x,c:.//a[@class="tag"]/text()-->*>-->_:,'   ,
            'type'      : 'STRING'                                      })
        case_A3 = slsc.Field(
            **{
                'id_'   : 'F3'  ,
                'value' : 10    })
        
        context = sltw.g_xpath(R_01.html_tree, '(//div[@class="quote"])[1]')[0]
        
        assert case_A1.extract(R_01, None     )           == 10000
        assert case_A2.extract(R_01, context  )           == 'CHANGE,DEEP-THOUGHTS,THINKING,WORLD'
        assert case_A3.extract(R_01, None     )           == 10
class TestBucket    (
    ):
    def test_parse              (
        self    ):
        case_A1 = {
                'id_'       : 'B1'                          ,
                'fields'    : [
                    [
                        'x://a' , 
                        'F1'    ,
                    ],
                    {
                        'id_'       : 'F2'  , 
                        'extractor' : 'p:0' ,
                    },
                ]                                           ,
                'is_skip_None'  : 'Y'                       ,
                'data_adapter'  : 'B_FLATTEN:*=a!!b!!c'     ,
            }
        case_A2 = {
                'id_'       : 'B2'                          ,
                'fields'    : [
                    [
                        'x://a' , 
                        'F1'    ,
                    ],
                    {
                        'id_'       : 'F2'  , 
                        'extractor' : 'p:0' ,
                    },
                    {
                        'id_'       : 'B2_1',
                        'fields'    : [
                            {
                                'x://2',
                            },
                        ]                   ,
                    },
                    [
                        None    ,
                        'B2_2'  ,
                        [
                            [
                                'p:0'       , 
                                'B2_2F1'    ,
                            ]   ,
                        ]       ,
                    ],
                ]                                           ,
                'is_skip_None'      : 'Y'                   ,
                'data_adapter'      : 'B_FLATTEN:*=a!!b!!c' ,
            }
        
        b_A1    = slsc.Bucket(**case_A1)
        b_A2    = slsc.Bucket(**case_A2)

        assert  b_A1.fields[0].id_                          == 'F1'                     and \
                b_A1.fields[0].extractor.collections[0]     \
                    .functions[0].method                    == slse.EXTRACTORS.XPATH    and \
                b_A1.fields[1].id_                          == 'F2'                     and \
                b_A1.fields[1].extractor.collections[0]     \
                    .functions[0].method                    == slse.EXTRACTORS.OBJ_PATH and \
                b_A1.fields[1].extractor.collections[0]     \
                    .functions[0].kwargs                    == {'path': 0 }             and \
                b_A1.is_skip_None                           == True
        
        assert  b_A2.fields[0].id_                          == 'F1'                     and \
                b_A2.fields[0].extractor.collections[0]     \
                    .functions[0].method                    == slse.EXTRACTORS.XPATH    and \
                isinstance(b_A2.fields[2], slsc.Bucket)                                 and \
                isinstance(b_A2.fields[3], slsc.Bucket)                                 and \
                b_A2.fields[3].fields[0].id_                == 'B2_2F1'
    def test_extract_simple     (
        self    ):
        case_A1 = {
            'id_'       : 'B1',
            'extractor' : 'x://div[@class="quote"]',
            'fields'    : [
                {
                    'id_'       : 'author'                                                  ,
                    'extractor' : 'x,c:.//small[@itemprop="author"]//text()-->JOIN_STRS'    },
                {
                    'id_'       : 'quote'                                                   ,
                    'extractor' : 'x,c:.//span[@itemprop="text"]//text()-->JOIN_STRS'       }]}
        
        b_A1    = slsc.Bucket(**case_A1)

        assert  b_A1.extract(R_01, None)[:2]    == [
            {
                'author'    : 'Albert Einstein',
                'quote'     : '“The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.”'},
            {
                'author'    : 'J.K. Rowling',
                'quote'     : '“It is our choices, Harry, that show what we truly are, far more than our abilities.”'},]
    def test_extract_complex    (
        self    ):
        case_A1 = {
                'id_'       : 'B1'                      ,
                'extractor' : 'x://div[@class="quote"]' ,
                'fields'    : [
                    {
                        'id_'       : 'author'                                              ,
                        'extractor' : 'x:.//small[@itemprop="author"]//text()-->JOIN_STRS'  ,
                    },
                    {
                        'id_'       : 'quote'                                               ,
                        'extractor' : 'x:.//span[@itemprop="text"]//text()-->p-->/:0<->45'  ,
                    },
                    {
                        'id_'       : 'tag'                         ,
                        'extractor' : 'x:.//div[@class="tags"]/a'   ,
                        'fields'    : [
                            {
                                'id_'       : 'name'            ,
                                'extractor' : 'x:./text()-->p'  ,
                            },
                            {
                                'id_'       : 'url'                 ,
                                'extractor' : 'x:./@href-->p-->a'   ,
                            },
                        ],
                    },
                ]                                       ,
            }
        case_A2 = {
                'id_'           : 'B1'                      ,
                'extractor'     : 'x://div[@class="quote"]' ,
                'fields'        : [
                    {
                        'id_'       : 'tag'                     ,
                        'extractor' : 'x:.//div[@class="tags"]' ,
                        'fields'    : [
                            {
                                'id_'       : 'name'                ,
                                'extractor' : 'x:./a/text()-->p'    ,
                            },
                            {
                                'id_'       : 'url'                 ,
                                'extractor' : 'x:./a/@href-->p-->a' ,
                            },
                        ],
                    },
                ]                                           ,
                'data_adapter'  : '*bf:*=tag<->y'           ,
            }

        b_A1    = slsc.Bucket(**case_A1)
        res_A1  = b_A1.extract(R_01, None)
        b_A2    = slsc.Bucket(**case_A2)
        res_A2  = b_A2.extract(R_01, None)

        assert  res_A1[0]   == {
                'author'    : 'Albert Einstein'                                 ,
                'quote'     : '“The world as we have created it is a process'   ,
                'tag'       : [
                    {
                        'name'  : 'change'                                                  ,
                        'url'   : 'http://quotes.toscrape.com/tag/change/page/1/'           ,
                    },
                    {
                        'name'  : 'deep-thoughts'                                           ,
                        'url'   : 'http://quotes.toscrape.com/tag/deep-thoughts/page/1/'    ,
                    },
                    {
                        'name'  : 'thinking'                                                ,
                        'url'   : 'http://quotes.toscrape.com/tag/thinking/page/1/'         ,
                    },
                    {
                        'name'  : 'world'                                                   ,
                        'url'   : 'http://quotes.toscrape.com/tag/world/page/1/'            ,
                    }
                ]                                                               ,
            }
        assert  res_A2[4]   == {
                'tag_name'      : 'be-yourself'                                         ,
                'tag_url'       : 'http://quotes.toscrape.com/tag/be-yourself/page/1/'  ,
            }
class TestParser    (
    ):
    def test_non_nested (
        self    ):
        D_B1        = {
                'id_'       : 'B1'                      ,
                'extractor' : 'x://div[@class="quote"]' ,
                'fields'    : [
                    {
                        'id_'       : 'author'                                              ,
                        'extractor' : 'x:.//small[@itemprop="author"]//text()-->JOIN_STRS'  ,
                    },
                ]                                  ,
            }
        D_B2        = {
                'id_'       : 'B2'                      ,
                'extractor' : 'x://div[@class="quote"]' ,
                'fields'    : [
                    {
                        'id_'       : 'author'                                              ,
                        'extractor' : 'x:.//small[@itemprop="author"]//text()-->JOIN_STRS'  ,
                    },
                ]                                  ,
            }
        D_B3        = {
                'id_'       : 'B3'                      ,
                'extractor' : 'x://div[@class="quote"]' ,
                'fields'    : [
                    {
                        'id_'       : 'tag'                                 ,
                        'extractor' : 'x:.//a[@class="tag"]//text()-->p'    ,
                    },
                ]                                  ,
            }
        RL_1        = {
                'id_'       : 'RL1'                             ,
                'extractor' : '=,s:http://quotes.toscrape.com/' ,
                'buckets'   : [D_B1, D_B2]                      ,
            }
        RL_2        = {
                'id_'       : 'RL2'                         ,
                'extractor' : 'r,s:.*'                      ,
                'buckets'   : [D_B3]                        ,
                'requests'  : [['x://a/@href-->p-->a-->@']] ,
            }
        case_1      = {
            'rules' : [
                RL_1    ,
                RL_2    ,
            ]}

        l_1     = []
        parser  = slsc.Parser(**case_1)
        data    = parser.parse(R_01, None, l_1)
        
        assert data['B2'][0]    == {'author'   : 'Albert Einstein' }
        assert data['B1'][0]    == {'author'   : 'Albert Einstein' }
        assert data['B3'][0]    == {'tag'      : 'change'          }
        assert data['B3'][6]    == {'tag'      : 'life'            }
        assert len(l_1)         == 1
    def test_nested     (
        self    ):
        D_B1        = {
                'id_'           : 'B1'                          ,
                'extractor'     : 'x:(//div[@class="quote"])[1]',
                'fields'        : [
                    {
                        'id_'       : 'author'                                              ,
                        'extractor' : 'x:.//small[@itemprop="author"]//text()-->JOIN_STRS'  ,
                    },
                    {
                        'id_'       : 'author_r'                                    ,
                        'type'      : 'REQUEST'                                     ,
                        'extractor' : 'x:.//a[text()="change"]/@href-->p-->a-->@'   ,
                    },
                ]                                           ,
                'data_adapter'  : '*bf:*=author_r<->y'      ,
            }
        D_B2        = {
                'id_'       : 'B2'                              ,
                'extractor' : 'x:(//div[@class="quote"])[1]'    ,
                'fields'    : [
                    {
                        'id_'       : 'author'                                      ,
                        'extractor' : 'x:.//small[@itemprop="author"]//text()-->_'  ,
                    },
                ]                                       ,
            }
        RL_1        = {
                'extractor' : '=,s:http://quotes.toscrape.com/' ,
                'buckets'   : [D_B1]                            ,
            }
        RL_2        = {
                'extractor' : '=,s:http://quotes.toscrape.com/tag/change/page/1/'   ,
                'buckets'   : [D_B2]                                                ,
            }

        case_1      = {
            'rules' : [
                RL_1    ,
                RL_2    ,
            ]}
        l_1         = []
    
        parser  = slsc.Parser(**case_1)
        
        assert  parser.parse(R_01, lambda x: R_02, l_1) == {
            'B1': [{'author': 'Albert Einstein', 'author_r_author': 'Albert Einstein'}]}

        
        