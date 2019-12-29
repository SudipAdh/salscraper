from    salscraper  import  extraction  as  slse
from    salscraper  import  interface   as  slsi
from    salscraper  import  settings    as  slst

from    os.path     import  join    , dirname   , abspath

import  pytest 

ROOT                = dirname(__file__)
FIX_PATH            = join(ROOT, 'fixtures')

slst.set_param('RESOURCE_FOLDER', join(FIX_PATH, 'resources'))
R_01    = slsi.Response.pickle_load(join(FIX_PATH,'r_01.pickle'))

class   TestEXTRACTORS          (
    ):
    def test_data                   (
        self    ):
        html_element    = R_01.html_tree.xpath('//title')[0]
        json_           = '{"a":1}'
        dict_           = {
            'a' : [
                None        ,
                {
                    'a1b':1 }],
            'b' : {'x' : 2} ,
            'c' : {'x' : 2} ,
            'd' : {'x' : 3} }
        filter_list     = [
            {'x' : 2},
            {'x' : 2},
            {'x' : 3}   ]
        list_           = [0,1,2,3,4,5,6,7,8,9]
        
        assert slse.EXTRACTORS.XPATH            (
            None                                ,
            None                                ,
            R_01.html_tree                      ,
            '(//a[@class="tag"]//text())[1]'    ) == ['change']
        assert slse.EXTRACTORS.EQUALS           (
            None    ,
            None    ,
            'a'     ,
            'a'     ) == 'a'
        assert slse.EXTRACTORS.REGEX            (
            None                ,
            None                ,
            '1abc2'             ,
            pattern = '[a-z]+'  ) == ['abc']
        assert slse.EXTRACTORS.FROM_HTML        (
            None            ,
            None            ,
            html_element    ) == '<title>Quotes to Scrape</title>'
        assert slse.EXTRACTORS.TO_HTML          (
            None                                ,
            None                                ,
            '<title>Quotes to Scrape</title>'   ).xpath('//text()')[0] == 'Quotes to Scrape'
        assert slse.EXTRACTORS.REPLACE          (
            None                    ,
            None                    ,
            '1abc2'                 ,
            pattern     = '[a-z]+'  ,
            replacement = 'x'       ) == '1x2'
        assert slse.EXTRACTORS.IN_LIST          (
            None    ,
            None    ,
            None    ) == [None]
        assert slse.EXTRACTORS.FROM_JSON        (
            None    ,
            None    ,
            json_   ) == {'a':1}
        assert slse.EXTRACTORS.OBJ_PATH         (
            None                ,
            None                ,
            dict_               ,
            path    = 'a.1.a1b' ) == 1        
        assert slse.EXTRACTORS.FILTER           (
            None            ,
            None            ,
            filter_list     ,
            path    = 'x'   ,
            value   = 2     ) == [
                {'x' : 2},
                {'x' : 2}]
        assert slse.EXTRACTORS.FILTER           (
            None            ,
            None            ,
            filter_list     ,
            path    = 'x'   ,
            value   = None  ) == [
                {'x' : 2},
                {'x' : 2},
                {'x' : 3}   ]
        assert slse.EXTRACTORS.ABS_URL          (
            R_01    ,
            None    ,
            '/x'    ) == 'http://quotes.toscrape.com/x'
        assert slse.EXTRACTORS.JOIN_STRS        (
            None        ,
            None        ,
            ['a', 'b']  ) == 'a b'
        assert slse.EXTRACTORS.SLICE            (
            None        ,
            None        ,
            list_       ,
            -1          ,
            0           ,
            -4          ) == [9,5,1]
        assert slse.EXTRACTORS.FORMAT           (
            None    ,
            None    ,
            [1,2]   ,
            '{}-{}' ) == '1-2'
        assert slse.EXTRACTORS.FORMAT           (
            None            ,
            None            ,
            {'a':1,'b':2}   ,
            '{a}-{b}'       ) == '1-2'
        assert slse.EXTRACTORS.UNESCAPE_HTML    (
            None                            ,
            None                            ,
            'Kristj&aacuten V&iacute;ctor'  ) == 'Kristján Víctor'
        assert slse.EXTRACTORS.TO_DICT          (
            None        ,
            None        ,
            [1,2]       ,
            ['a','b']   ) == {'a':1,'b':2}
        assert slse.EXTRACTORS.UPPER            (
            None        ,
            None        ,
            'abc'       ) == 'ABC'
        assert slse.EXTRACTORS.LOWER            (
            None        ,
            None        ,
            'ABC'       ) == 'abc'
        assert slse.EXTRACTORS.RESOURCE         (
            None        ,
            None        ,
            'data_1'    ) == {'a':1}
        assert slse.EXTRACTORS.STRIP            (
            None    ,
            None    ,
            ' a '   ) == 'a'
        assert slse.EXTRACTORS.NONE             (
            None    ,
            None    ,
            ' a '   ) == ' a '
    def test_buckets                (
        self    ):
        b_a = {
            'a1'    : 1 ,
            'a2'    : 2 ,
            'a3'    : [{
                'a31'   : 31    ,
                'a32'   : 32    }]}
        b_b = {
            'b1'    : 'bv1' ,
            'b2'    : 'bv2' }
        b_c = {
            'c1'    : 'cv1' ,
            'c2'    : 'cv2' }
        b_d = {
            'b' : [b_b.copy()               ],
            'c' : [b_c.copy(), b_c.copy()   ]}
        
        assert  slse.EXTRACTORS.B_FLATTEN   (
            None    ,
            None    ,
            b_a     ,
            ['a3']  ) == {'a1':1, 'a2':2, 'a31': 31, 'a32':32}
        assert  slse.EXTRACTORS.B_FLATTEN   (
            None    ,
            None    ,
            b_a     ,
            ['a3']  ,
            True    ) == {'a1':1, 'a2':2, 'a3_a31': 31, 'a3_a32':32}
        assert  slse.EXTRACTORS.B_MULTIPLY  (
            None    ,
            None    ,
            b_d     ,
            'b'     ,
            'c'     ) == {'b':[
                {
                    'b1'    : 'bv1' ,
                    'b2'    : 'bv2' ,
                    'c1'    : 'cv1' ,
                    'c2'    : 'cv2' },
                {
                    'b1'    : 'bv1' ,
                    'b2'    : 'bv2' ,
                    'c1'    : 'cv1' ,
                    'c2'    : 'cv2' },
                ]}
    def test_next_page              (
        self    ):
        urls        = [
            'www.example.come/?page_number=1'               ,
            'www.example.come/abcd/?a=1&p_number=1&x=y'     ,
            'www.example.come/?p=1'                         ,
            'www.example.come/a/123/?page_number=15'        ,
            'www.example.come/a/123/page_number/123/index'  ,
            'www.example.come/a/123/p?p=10'                 ,
            'www.example.come/new/11'                       ,
            'www.example.come/?page-=1'                     ]
        url_param   = 'www.example.come/?page=1&abc=4'

        assert [slse.EXTRACTORS.NEXT_PAGE(
            None    ,
            None    ,
            url     ) for url in urls] == [
                'www.example.come/?page_number=2'               ,
                'www.example.come/abcd/?a=1&p_number=2&x=y'     ,
                'www.example.come/?p=2'                         ,
                'www.example.come/a/123/?page_number=16'        ,
                'www.example.come/a/123/page_number/124/index'  ,
                'www.example.come/a/123/p?p=11'                 ,
                'www.example.come/new/12'                       ,
                'www.example.come/?page-=2'                     ]
        assert slse.EXTRACTORS.NEXT_PAGE(
            None        ,
            None        ,
            url_param   ,
            'abc'       ) == 'www.example.come/?page=1&abc=5'
    def test_request_get            (
        self    ):
        case_A1 = slse.EXTRACTORS.REQUEST(
            None                                ,
            None                                ,
            'www.example.come/?page_number=1'   )
        case_A2 = slse.EXTRACTORS.REQUEST(
            None                                ,
            None                                ,
            {'a':1}                             ,
            'www.example.come/?page_number=1'   ,
            params = {'b':1}                    )
        
        assert  case_A1.url     == 'www.example.come/?page_number=1'
        assert  case_A2.url     == 'www.example.come/?page_number=1'    and\
                case_A2.params  == {'a':1,'b':1}
class   TestExtractorFunction   (
    ):
    def test_parse_method_type      (
        self    ):
        case_A1 = '=:ABCD,\n,232,ll'
        case_A2 = 'r:xdsfd'
        case_A3 = 'x://a=,TEXT'
        case_A4 = '*FORMAT,JSON:1234'

        case_B1 = 'g:worng!'
        case_B2 = 'j,WRONG:!sds'

        assert  slse.ExtractorFunction._parse_method_type(case_A1)  ==\
            (False, 'EQUALS', 'CONTEXT')
        assert  slse.ExtractorFunction._parse_method_type(case_A2)  ==\
            (False, 'REGEX', 'CONTEXT')
        assert  slse.ExtractorFunction._parse_method_type(case_A3)  ==\
            (False, 'XPATH', 'CONTEXT')
        assert  slse.ExtractorFunction._parse_method_type(case_A4)  ==\
            (True, 'FORMAT', 'JSON')
        
        with pytest.raises(ValueError, match='Method name/abrv g is not found.')    :
            slse.ExtractorFunction._parse_method_type(case_B1)
        with pytest.raises(ValueError, match='Source type WRONG is not found.')     :
            slse.ExtractorFunction._parse_method_type(case_B2)
    def test_parse_value            (
        self    ):
        strs    = [
            '<(123)>'           ,
            '<(False)>'         ,
            '<(hey you!)>'      ,
            'False'             ,
            'True1'             ,
            'y'                 ,
            '123'               ,
            '2.3'               ]
        assert  [slse.ExtractorFunction._parse_value(x) for x  in strs] == [
            '123'       ,
            'False'     ,
            'hey you!'  ,
            False       ,
            'True1'     ,
            True        ,
            123         ,
            2.3         ] 
    def test_parse_kwargs           (
        self    ):
        case_A1 = '*x://*'
        case_A2 = r'r:\d+'
        case_A3 = 'f:f_str=Hello {} {}'
        case_A4 = 'd:*=1!!2!!<(3)>!!<(4)>'
        case_A5 = '/:5<->2<->step=-1'
        case_A6 = '/:5<-><(2)><->step=<(-1)>'
        case_A7 = '=:http://www.example.com'

        assert  slse.ExtractorFunction._parse_kwargs(case_A1)['kwargs'] ==\
            {'xpath' : '//*'}
        assert  slse.ExtractorFunction._parse_kwargs(case_A2)['kwargs'] ==\
            {'pattern' : r'\d+'}
        assert  slse.ExtractorFunction._parse_kwargs(case_A3)['kwargs'] ==\
            {'f_str' : 'Hello {} {}'}
        assert  slse.ExtractorFunction._parse_kwargs(case_A4)['kwargs'] ==\
            {'keys' : [1,2,'3','4']}
        assert  slse.ExtractorFunction._parse_kwargs(case_A5)['kwargs'] ==\
            {'start' : 5, 'end' : 2, 'step' : -1}
        assert  slse.ExtractorFunction._parse_kwargs(case_A6)['kwargs'] ==\
            {'start' : 5, 'end' : '2', 'step' : '-1'}
        assert  slse.ExtractorFunction._parse_kwargs(case_A7)['kwargs'] ==\
            {'y' : 'http://www.example.com'}
    def test_function_parsing       (
        self    ):
        case_A1 = '*x://a'
        case_A2 = '*f:Hello {}'
        case_A3 = '/:end=5'
        case_A4 = 'd:*=a!!b!!c'
        case_A5 = 'd:*keys=a!!b!!c'
        case_A6 = r'r,JSON:\d+'

        obj_A1  = slse.ExtractorFunction(case_A1)
        obj_A2  = slse.ExtractorFunction(case_A2)
        obj_A3  = slse.ExtractorFunction(case_A3)
        obj_A4  = slse.ExtractorFunction(case_A4)
        obj_A5  = slse.ExtractorFunction(case_A5)
        obj_A6  = slse.ExtractorFunction(case_A6)

        assert  obj_A1.method       == slse.EXTRACTORS.XPATH        and\
                obj_A1.kwargs       == {'xpath': '//a'}             and\
                obj_A1.is_list      == True                         and\
                obj_A1.source_type  == slse.SourceType.CONTEXT
        assert  obj_A2.method       == slse.EXTRACTORS.FORMAT       and\
                obj_A2.kwargs       == {'f_str': 'Hello {}'}        and\
                obj_A2.is_list      == True                         and\
                obj_A2.source_type  == slse.SourceType.CONTEXT
        assert  obj_A3.method       == slse.EXTRACTORS.SLICE        and\
                obj_A3.kwargs       == {'end':5}                    and\
                obj_A3.is_list      == False                        and\
                obj_A3.source_type  == slse.SourceType.CONTEXT
        assert  obj_A4.method       == slse.EXTRACTORS.TO_DICT      and\
                obj_A4.kwargs       == {'keys': ['a','b','c']}      and\
                obj_A4.is_list      == False                        and\
                obj_A4.source_type  == slse.SourceType.CONTEXT
        assert  obj_A5.method       == slse.EXTRACTORS.TO_DICT      and\
                obj_A5.kwargs       == {'keys': ['a','b','c']}      and\
                obj_A5.is_list      == False                        and\
                obj_A5.source_type  == slse.SourceType.CONTEXT
        assert  obj_A6.method       == slse.EXTRACTORS.REGEX        and\
                obj_A6.kwargs       == {'pattern': r'\d+'}          and\
                obj_A6.is_list      == False                        and\
                obj_A6.source_type  == slse.SourceType.JSON
    def test_extract                (
        self    ):
        case_1      = slse.ExtractorFunction('*p:a')
        case_2      = slse.ExtractorFunction(' ')

        context_1   = [{'a':1},{'a':2},{'b':2}]
        context_2   = 'a'

        assert  case_1.extract(None, context_1, context_1)  == [
            1       ,
            2       ,
            None    ]
        assert  case_2.extract(None, context_2, context_2)  == 'a'
class   TestExtractor           (
    ):
    def test_extractor_parsing      (
        self    ):
        args        = [
            [
                [['JOIN_STRS', 'IN_LIST']]  , 
                [['JOIN_STRS', 'IN_LIST']]  ]
            ]
        kwargs      = {'collections': args[0]}
        str_        = 'JOIN_STRS-->IN_LIST|=|JOIN_STRS-->IN_LIST'
        kwargs_str  = {'collections': str_}

        exts    = [
            slse.Extractor(*args)           ,
            slse.Extractor(**kwargs)        ,
            slse.Extractor(str_)            ,
            slse.Extractor(**kwargs_str)    ]
        
        for ext in exts :
            assert  ext.collections[0].functions[0].method == slse.EXTRACTORS.JOIN_STRS
            assert  ext.collections[1].functions[1].method == slse.EXTRACTORS.IN_LIST
    def test_extract                (
        self    ):
        case_A1 = 'x:(//a[@class="tag"]//text())[1]-->p-->l-->p-->r:(.*)nge-->p-->>'
        case_A2 = 'x:(//a[@class="tag"]//text())[1]-->p|=|x:(//a[@class="tag"]//text())[2]-->p'
        case_A3 = 'x:(//div[@class="quote"])[1]//a[@class="tag"]/@href-->*a-->*@'

        res_A3  = slse.Extractor(case_A3).extract(
            R_01    ,
            None    ,
            None    )

        assert slse.Extractor(case_A1).extract(
            R_01    ,
            None    ,
            None    ) == 'CHA'
        assert slse.Extractor(case_A2).extract(
            R_01    ,
            None    ,
            None    ) == ['change', 'deep-thoughts']
        assert [x.url for x in res_A3]  == [
            'http://quotes.toscrape.com/tag/change/page/1/'         ,
            'http://quotes.toscrape.com/tag/deep-thoughts/page/1/'  ,
            'http://quotes.toscrape.com/tag/thinking/page/1/'       ,
            'http://quotes.toscrape.com/tag/world/page/1/'          ]