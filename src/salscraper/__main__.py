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
    return vars(parser.parse_args())

def main        (
    ):
    args_dict   = parse_args()
    path        = args_dict['path']
    url         = args_dict.get('url')
    if      os.path.isfile(path)   :
        slsp.Project.run_scraper(path, url)
    elif    os.path.isdir(path)    :
        p   = slsp.Project(
            n_workers   = 5     ,
            root_dir    = path  )
        p.start()
        p.join_exit()

main()