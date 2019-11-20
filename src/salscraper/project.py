from    saltools.common     import  EasyObj
from    collections         import  OrderedDict
from    saltools.files      import  g_filders
from    .scraper            import  Scraper
from    .                   import  export      as slsx

import  saltools.logging    as      sltl
import  saltools.misc       as      sltm

import  importlib.util
import  json
import  os

class Project(EasyObj):
    EasyObj_PARAMS  = OrderedDict((
        ('root_dir' , { }),))
    
    @classmethod
    def run_project     (
        cls     ,
        path    ):
        pass 
    @classmethod
    def run_scraper     (
        cls     ,
        path    ):
        file_name   = os.path.split(path)[-1]
        if      file_name.split('.')[-1]    == 'json'   :
            path_json   = path
            path_py     = None 
            scraper_name= file_name[:-5]
        elif    file_name.split('.')[-1]    == 'py'     :
            path_py     = path
            path_json   = None 
            scraper_name= file_name[:-3]
        settings    = sltm.g_config(os.path.join(
            os.path.dirname(path)   ,
            '__settings.json'     ))    
        cls.start_scraper(
            scraper_name    ,
            path_json       ,
            path_py         ,
            settings        )
    @classmethod
    def start_scraper   (
        cls                 ,
        scraper_name        ,
        path_json           ,
        path_py             ,
        settings    ={}     ,
        is_join     = True  ):
        def g_default_logger(
            scraper_name    ,
            settings        ):
            default_logger_dict = {
                'type'      : 'ConsoleLogger'   ,
                'kwargs'    : {}                }
            default_logger      = settings.get('default_logger', default_logger_dict)
            default_logger      = getattr(sltl, default_logger['type'])(**default_logger['kwargs'])
            default_logger.id_  = scraper_name
            return default_logger
        
        if      path_py   != None   :
            spec    = importlib.util.spec_from_file_location(scraper_name, path_py)
            module  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            scraper = module.g_scraper()
        elif    path_json != None   :
            json_dict   = sltm.g_config(path_json)
            scraper     = Scraper   (**json_dict['scraper'  ])
            if      json_dict.get('logger') :
                logger_dict     = json_dict['logger']
                scraper.logger  = getattr(sltl, logger['type'])(**logger['kwargs'])
        else                        :
            return 
        
        if      scraper.logger        == None   :
            scraper.logger  = g_default_logger(scraper_name, settings)
        if      scraper.data_exporter == None   :
            scraper.data_exporter   = slsx.Exporter(**settings['data_exporter'])

        sltl.set_main_logger(scraper.logger)
        scraper.logger.start()
        scraper.start()

        if      is_join:
            scraper.join_exit()
   
    def _on_init        (
        self    ):
        if      not os.path.isdir(self.root_dir):
            os.makedirs(self.root_dir)
        self.id_        = os.path.dirname(self.root_dir)
        self.scrapers   = self._load_scrapers()
        #self.schedules  = self._load_schedules()
        self.settings   = sltm.g_config(os.path.join(self.root_dir, '__settings.json'))
    def _load_scrapers  (
        self    ):
        py_files    = g_filders(
            self.root_dir   ,
            '\w+\.py'       ,
            True            ,
            True            ,
            False           ,
            False           )
        json_files  = g_filders(
            self.root_dir   ,
            '\w+\.json'     ,
            True            ,
            True            ,
            False           ,
            False           )
        
        py_files    = {
            os.path.basename(x)[:-3]    : x for x in py_files}
        json_files  = {
            os.path.basename(x)[:-5]    : x for x in json_files if '__settings.json' not in x} 
        all_scrapers= sltm.RecDefaultDict() 

        for json_name, json_file in json_files.items() :
            all_scrapers[json_name]['path_json']    = json_file
            all_scrapers[json_name]['scraper_name'] = json_name
        for py_name, py_file in py_files.items() :
            all_scrapers[py_name]['path_py']        = py_file
            all_scrapers[py_name]['scraper_name']   = py_name
        
        return all_scrapers


    
