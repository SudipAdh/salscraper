import  argparse
import  os 
from   .            import  project    as slsp

def parse_args  (
    ):
    parser  = argparse.ArgumentParser('salscraper')
    parser.add_argument(
        'path'                                                  , 
        type    = str                                           ,
        help    = 'Path to a project folder or a scraper file.' )
    parser.add_argument(
        '-u'                        ,
        '--url'                     ,
        type    = str               ,
        help    = 'Url to scrape.'  )
    parser.add_argument(
        '-s'                                                                                ,
        '--settings_path'                                                                   ,
        type    = str                                                                       ,
        help    = 'Path to an alter\',native settings file, default is __settings.json.'    )
    return vars(parser.parse_args())

def main        (
    ):
    args_dict       = parse_args()
    path            = args_dict['path']
    url             = args_dict.get('url')
    settings_path   = args_dict.get('settings_path')
    
    if      os.path.isfile(path)   :
        slsp.Project.run_scraper(path, url, settings_path)
    elif    os.path.isdir(path)    :
        p   = slsp.Project(
            n_workers       = 5             ,
            root_dir        = path          ,
            settings_path   = settings_path )
        p.start()
        p.join_exit()

main()