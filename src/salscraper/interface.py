'''Web interface.

    An interface.
'''
from    saltools            import  logging     as stl

from    enum                import  Enum
from    saltools.web        import  do_request
from    saltools.common     import  EasyObj
from    urllib.parse        import  urlparse
from    collections         import  OrderedDict
from    lxml.html           import  fromstring

import  json

class Method(Enum):
    GET     = 0
    POST    = 1
    JSON    = 2
    PUT     = 3

class Request   (EasyObj):
    EasyObj_PARAMS  = OrderedDict((
        ('url'          , {}        ),
        ('method'       , {
            'default': Method.GET   }),
        ('params'       , {
            'default': {}           }),
        ('cookies'      , {
            'default': None         }),
        ('session'      , {
            'default': None         })))

    def __str__(self):
        return '{}: {}'.format(self.url, self.params)
    def __repr__(self):
        return str(self)

    def _on_init(self):
        self.host = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(self.url))       
class Response  (EasyObj):
    ''' A server response.
         
    '''
    EasyObj_PARAMS  = OrderedDict((
        ('response_url' , {}        ),
        ('request_url'  , {}        ),
        ('status_code'  , {}        ),
        ('content'      , {}        ),
        ('text'         , {}        ),
        ('is_redirect'  , {}        ),
        ('cookies'      , {}        ),
        ('session'      , {}        )))
    
    def __str__ (self):
        return '{}: {}'.format(self.request_url, self.status_code)
    def __repr__(self):
        return str(self)  
    
    def _on_init(self):
        self.host       = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(self.request_url))
        try         :
            self.html_tree  = fromstring(self.text)
        except      :
            self.html_tree  = None 
        try         :
            self.json       = json.loads(self.text)
        except      :
            self.json       = None

class Interface (EasyObj):
    EasyObj_PARAMS  = OrderedDict((
        ('timeout'   , {
            'default'   : 10.0   ,
            'type'      : float },),))

    #Default headers
    HEADERS = { 'User-Agent': 
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'} 
    def execute_request(self, request):
        pass
class Requests  (Interface):
    '''Based on requests module.

        Web interface based on the requests module.
    '''

    @stl.handle_exception()
    def execute_request(self, request):
    
        if isinstance(request, str):
            request     = Request(url= request) 
        if request.method == Method.GET :
            sp, session = do_request(
                request.url             , 
                request.params          , 
                headers = self.HEADERS  ,
                timeout = self.timeout  )
        
        return Response(
            response_url= sp.url        ,
            request_url = request.url   ,
            status_code = sp.status_code,
            content     = sp.content    ,
            text        = sp.text       ,
            is_redirect = sp.is_redirect,
            cookies     = sp.cookies    ,
            session     = session       )