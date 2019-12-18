import  saltools.misc   as      sltm

from    os.path         import  join 

def set_param   (
    param   ,
    value   ):
    globals()[param]    = value
def set_params  (
    root    = './'  ):
    settings_dict   = sltm.g_config(join(root, '__settings.json'))
    _params_list    = {
            'EXTRACTORS_SEPARATOR'  : '-->'     ,
            'KWARGS_SEPARATOR'      : '<->'     ,
            'ESC_OPEN'              : '<('      ,
            'ESC_CLOSE'             : ')>'      ,
            'LIST_SEPARATOR'        : '!!'      ,
            'COLLECTIONS_SEPARATOR' : '|=|'     ,
        }

    for param, def_value in _params_list.items()    :
        set_param(param, settings_dict.get('parameters',{}).get(param, def_value))
    
    set_param('RESOURCE_FOLDER', join(root, 'resources'))

set_params()