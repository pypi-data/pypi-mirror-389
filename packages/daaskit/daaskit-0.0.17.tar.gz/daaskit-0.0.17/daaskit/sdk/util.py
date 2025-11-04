import os
from dbutils.pooled_db import PooledDB
import pymysql

def get_env_ns(ns=None):
    if ns is None:
        ns = os.getenv('ENV_DAASDEV_NS')
        if ns is None:
            ns='daasdev'
    return ns

def get_env(key, default=None):
    val = os.getenv(key)
    if val is None:
        return default
    else:
        return val

def get_host_with_ns(host):
    ns = get_env('ENV_DAASDEV_NS', '')
    if host == "rdb" or host == "influxdb" or host == "nats-server":
       if ns != "":
           return host + "." + ns
    
    return host

def create_pooleddb(dbhost, dbport, dbuser, dbpwd, dbname):
   return PooledDB(
      creator=pymysql,  # 使用链接数据库的模块
      maxconnections=20,  # 连接池允许的最大连接数，0和None表示不限制连接数
      mincached=2,  # 初始化时，链接池中至少创建的空闲的链接，0表示不创建
      maxcached=5,  # 链接池中最多闲置的链接，0和None不限制
      #maxshared=3,  # 链接池中最多共享的链接数量，0和None表示全部共享。PS: 无用，因为pymysql和MySQLdb等模块的 threadsafety都为1，所有值无论设置为多少，_maxcached永远为0，所以永远是所有链接都共享。
      blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待然后报错
      maxusage=None,  # 一个链接最多被重复使用的次数，None表示无限制
      setsession=[],  # 开始会话前执行的命令列表。如：["set datestyle to ...", "set time zone ..."]
      ping=0,
      # ping MySQL服务端，检查是否服务可用。# 如：0 = None = never, 1 = default = whenever it is requested, 2 = when a cursor is created, 4 = when a query is executed, 7 = always
      host=dbhost,
      port=dbport,
      user=dbuser,
      passwd=dbpwd,
      db=dbname,
      charset='utf8'
   )

def create_pooleddb_by(datasource):
    # 获取 root:daasdev@#20222@tcp(rdb:3306)/oadb_cvxa3663
    part = datasource.split('?')[0] 
    items = part.split('@tcp')

    # 从 root:daasdev@#20222 获取用户名和密码
    i = items[0].index(':')
    dbuser = items[0][0:i]
    dbpwd = items[0][i + 1:]
    # dbpwd = 'daasdev@#20222'

    # 从 (rdb:3306)/oadb_cvxa3663 获取端口，host和数据库名
    i = items[1].index('/')
    dbname = items[1][i + 1:]

    i = items[1].index(')')
    hostport = items[1][1:i]
    items = hostport.split(':')
    host = get_host_with_ns(items[0])
    port = int(items[1])
    
    return create_pooleddb(host, port, dbuser, dbpwd, dbname)

def get_host_port_by_url(url):
    items = url.split(":")
    if len(items) == 2:
        # 如localhost:8086
        return items[0], int(items[1])
    if len(items) == 3:
        # 如http://localhost:8086
        return items[1].strip('/'), int(items[2])
    return url, 80

# Utility to check if a method exists in a class
def class_method_exist(cls, method_name):
    try:
        method = getattr(cls, method_name)
        if callable(method):
            return True
        return False
    except AttributeError:
        return False