from    .                   import  export      as  slsx
from    .                   import  extraction  as  slse
from    datetime            import  datetime    as  dt
from    collections         import  OrderedDict
from    .scraper            import  Scraper

import  saltools.logging    as      sltl
import  saltools.parallel   as      sltp
import  saltools.misc       as      sltm
import  saltools.common     as      sltc
import  saltools.files      as      sltf

import  importlib.util
import  string
import  random
import  json
import  os

class Project(
    sltp.NiceFactory    ):
    EasyObj_PARAMS  = OrderedDict((
        ('root_dir' , { }),))
    
    @classmethod
    def _g_json         (
        cls     ,
        path    ):
        name        = os.path.split(path)[-1][:-5]
        json_dict   = sltm.g_config(path)
        scraper     = Scraper(**json_dict['scraper'  ])
        if      json_dict.get('logger') :
            scraper.logger  = sltc.EasyObj.select_type(**json_dict['logger'])
        return scraper, name
    @classmethod
    def _g_py           (
        cls     ,
        path    ):
        module, name    = sltm.load_module(path)
        return  module.g_scraper(), name
    @classmethod
    def _load_customs   (
        cls         ,
        script_path ):
        path    = os.path.join(
            os.path.dirname(script_path)    ,
            '__custom_extractors.py'        )
        if      not os.path.isfile(path) :
            return
        custom_exts, name   = sltm.load_module(path)
        for ext_name in dir(custom_exts.EXTRACTORS):
            if      callable(getattr(custom_exts.EXTRACTORS, ext_name))     and \
                    not ext_name.startswith('__')                               :
                setattr(slse.EXTRACTORS, ext_name, getattr(custom_exts.EXTRACTORS, ext_name))   
    @classmethod
    def _start_scraper  (
        cls                 ,
        name                ,
        scraper             ,
        settings    = {}    ,
        is_join     = True  ):
        def g_default_logger(
            name        ,
            settings    ):
            default_logger_dict = {
                    'type'      : 'ConsoleLogger'   ,
                    'kwargs'    : {}                ,
                }
            default_logger                  = settings.get('default_logger', default_logger_dict)
            default_logger['kwargs']['id_'] =  name

            default_logger      = getattr(sltl, default_logger['type'])(**default_logger['kwargs'])

            return default_logger
        
        if      scraper.logger        == None   :
            scraper.logger  = g_default_logger(name, settings)
        if      scraper.data_exporter == None   :
            scraper.data_exporter   = slsx.Exporter(**settings['data_exporter'])
        sltl.set_main_logger(scraper.logger)
        scraper.logger.start()
        scraper.start()
        if      is_join:
            scraper.join_exit()
    
    @classmethod
    def run_scraper     (
        cls             ,
        path            ,
        url     = None  ,
        is_join = True  ):
        cls._load_customs(path)
        settings    = sltm.g_config(os.path.join(
            os.path.dirname(path)   ,
            '__settings.json'       ))

        if      path.split('.')[-1] == 'json'   :
            scraper, name   = cls._g_json(path)
        elif    path.split('.')[-1] == 'py'     :
            scraper, name   = cls._g_py(path)
        
        if      url != None :
            scraper.start_tasks.clear()
            scraper.add_request(url)
        try     :
            cls._start_scraper(
                name        ,
                scraper     ,
                settings    ,
                is_join     )
        except Exception as e:
            print(e)
    
    def _on_init        (
        self    ):
        if      not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir)
        self.id_        = os.path.dirname(self.root_dir)
        
        for task in self._load_scrapers():
            self.start_tasks.append(task)
    def _load_scrapers  (
        self    ):
        paths   = sltf.g_filders(
            self.root_dir               ,
            '^(?!__)\w+\.(?:py|json)$'  ,
            True                        ,
            True                        ,
            False                       ,
            False                       )
        
        paths   = [os.path.abspath(x) for x in paths]
        return  [
                sltp.FactoryTask(
                    id_         = os.path.split(path)[-1]   ,
                    target      = type(self).run_scraper    ,
                    args        = [path, None, False]       ,
                    is_process  = True                      ) for path in paths
            ]
        


    
