from    pprint              import  pprint
from    sqlalchemy.schema   import  Table       , MetaData
from    enum                import  Enum
from    collections         import  OrderedDict

import  saltools.parallel   as      sltp
import  saltools.misc       as      sltm
import  saltools.common     as      sltc
import  saltools.logging    as      sltl

import  csv
import  os

class ExporterType(Enum):
    SQLALCHEMY  = 0
    PPRINT      = 1
    CSV         = 2

class Exporter(sltc.EasyObj):
    EasyObj_PARAMS  = OrderedDict((
        ('type'             , {
            'type'      : ExporterType          ,
            'default'   : ExporterType.PPRINT   },),
        ('engine_builder'   , {
            'type'      : sltm.SQLAlchemyEBuilder   ,
            'default'   : None                      },),
        ('path'             , {
            'default'   : None  ,
            'type'      : str   },),))
    
    @classmethod
    @sltl.handle_exception  (
        is_log_start= True  ,
        params_start= None  )
    def export_sqlalchemy   (
        cls             ,
        data            ,
        engine          ,
        path    = None  ):
        engine  = engine.engine
        def insert_row(
            row                 , 
            table               ,
            meta                , 
            referrer    = None  ,
            referrer_id = None  ):
            columns     = [x for x in row if not isinstance(row[x], list)]
            relations   = [x for x in row if     isinstance(row[x], list)]

            values  = {column: row[column] for column in columns}
            if      referrer != None    :
                values['{}_id'.format(referrer)] = referrer_id
            
            id_     = table.insert().values(**values).execute().lastrowid
            for relation_table_name in relations   :
                relation_table   = Table(relation_table_name, meta, autoload=True)
                for relation_row in row[relation_table_name]   :
                    insert_row(
                        relation_row    ,
                        relation_table  ,
                        meta            ,
                        table.name      ,
                        id_             )

        meta    = MetaData(engine)
        for table_name in data.keys()    :
            table   = Table(table_name, meta, autoload=True)
            for row in data[table_name] :  
                insert_row(row, table, meta)

    @classmethod
    @sltl.handle_exception  (
        is_log_start= True  ,
        params_start= None  )
    def export_pprint       (
        cls             ,
        data            ,
        engine  = None  , 
        path    = None  ):
        pprint(data)
    
    @classmethod
    @sltl.handle_exception  (
        is_log_start= True  ,
        params_start= None  )
    def export_csv          (
        cls             ,
        data            ,
        engine  = None  , 
        path    = None  ):
        for key, value in data.items():
            if      path == None        :
                path    = f'{key}.csv'
            elif    os.path.isdir(path) :
                path    = os.path.join(path, f'{key}.csv')

            w_headers   = not os.path.isfile(path)
            headers     = value[0].keys()
            with open(path, 'a', newline= '\n') as f :  
                writer  = csv.DictWriter(f, fieldnames=headers)
                if      w_headers   :
                    writer.writeheader()
                writer.writerows(value)
    
    def export  (
        self    ,
        data    ):
        export_fn   = getattr(type(self), 'export_'+ self.type.name.lower())
        export_fn(
            data                ,
            self.engine_builder ,
            self.path           )
        



