'''Web interface.

    An interface.
'''
from    saltools            import  logging     as stl

from    enum                import  Enum
from    saltools.web        import  do_request
from    saltools.common     import  EasyObj
from    urllib.parse        import  urlparse
from    collections         import  OrderedDict
from    lxml.html           import  fromstring  , clean

import  pickle
import  json

class Method    (
    Enum    ):
    GET     = 0
    POST    = 1
    JSON    = 2
    PUT     = 3

class Request   (
    EasyObj ):
    EasyObj_PARAMS  = OrderedDict((
        ('url'          , {}),
        ('method'       , {
            'type'      : Method        ,
            'default'   : Method.GET    }),
        ('params'       , {
            'default': {}           }),
        ('cookies'      , {
            'default': None         }),
        ('session'      , {
            'default': None         },),))

    def __str__ (
        self    ):
        return '{}: {}'.format(self.url, self.params)
    def __repr__(
        self    ):
        return str(self)

    def _on_init(
        self    ):
        uri         = urlparse(self.url)
        self.host   = f'{uri.scheme}://{uri.netloc}'
class Response  (
    EasyObj ):
    ''' A server response.
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('response_url' , {}        ),
        ('request_url'  , {}        ),
        ('request_obj'  , {}        ),
        ('status_code'  , {}        ),
        ('content'      , {}        ),
        ('text'         , {}        ),
        ('is_redirect'  , {}        ),
        ('cookies'      , {}        ),
        ('session'      , {}        )))
    
    @classmethod
    def pickle_dump (
        cls     ,
        r       ,
        path    ):
        html_tree   = r.html_tree
        r.html_tree = None

        with open(path, 'wb') as f:
            pickle.dump(r, f)

        r.html_tree = html_tree
    @classmethod
    def pickle_load (
        cls     ,
        path    ):
        with open(path, 'rb') as f:
            r = pickle.load(f) 
        
        try     :
            r.html_tree = fromstring(r.text)
        except  :
            pass
        
        return r
        
    def __str__ (
        self    ):
        return f'{self.request_url}: {self.status_code}'
    def __repr__(
        self    ):
        return str(self)  
    
    def _on_init(
        self    ):
        uri         = urlparse(self.request_url)
        self.host   = f'{uri.scheme}://{uri.netloc}'
        try         :
            cleaner     = clean.Cleaner(style=True)
            r.html_tree = cleaner.clean_html(fromstring(self.text))
        except      :
            self.html_tree  = None 
        try         :
            self.json       = json.loads(self.text)
        except      :
            self.json       = None

class Interface (
    EasyObj ):
    EasyObj_PARAMS  = OrderedDict((
            ('timeout'  , {
                    'default'   : 10.0  ,
                    'type'      : float ,
                }   ),
        ))

    #Default headers
    HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        } 
    
    def execute_request(
        self    , 
        request ):
        pass
class Requests  (
    Interface   ):
    '''Based on requests module.

        Web interface based on the requests module.
    '''

    @stl.handle_exception   (
        params_exc  = [
                'request',
            ]   )
    def execute_request     (
        self    , 
        request ):
        if      isinstance(request, str)        :
            request     = Request(url= request) 
        if      request.method == Method.GET    :
            r, session = do_request(
                request.url             , 
                request.params          , 
                headers = self.HEADERS  ,
                timeout = self.timeout  )
        elif    request.method == Method.POST   :
            r, session = do_request(
                request.url             , 
                request.params          ,
                is_post = True          ,
                headers = self.HEADERS  ,
                timeout = self.timeout  )
        elif    request.method == Method.JSON   :
            r, session = do_request(
                request.url             ,
                request.params          ,
                is_json = True          ,
                headers = self.HEADERS  ,
                timeout = self.timeout  )
        return Response(
            response_url= r.url         ,
            request_obj = request       ,
            request_url = request.url   ,
            status_code = r.status_code ,
            content     = r.content     ,
            text        = r.text        ,
            is_redirect = r.is_redirect ,
            cookies     = r.cookies     ,
            session     = session       )