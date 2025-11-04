#!/usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
from daaskit.sdk import apis
from daaskit.sdk.util import get_env_ns
from daaskit.sdk.log import logger

def get_db(ns=None):
    ns = get_env_ns(ns)
    db = pymysql.connect(host='rdb.%s.svc.cluster.local' % ns, port=3306, user='root', passwd='daasdev@#20222', db='oadb_cvxa3663')
    return db

class DB:
   def __init__(self, domain: str = 'cvxa3663', backend: bool = False, **kwargs):
      self.domain = domain
      self.backend = backend
      self.request = apis.get(org_domain=domain, **kwargs)
      self.pooleddb = self

   def exec(self, sql, *args):
      _args = args
      if len(args) == 1 and isinstance(args[0], (list, tuple)):
         _args = args[0]
      result = self.request.exts.db.execute({
         'sql': sql,
         'args': _args,
         'backend': self.backend
      })
      data, err = result.data()
      if err:
         logger.error(f'DB.exec error: err=({err}), sql=({sql}), args=({_args})')
         raise Exception(f'DB.exec error: {err}')
      return data
   
   def fetch_one(self, sql, *args):
      rows = self.exec(sql, *args)
      if rows and len(rows) > 0:
         return rows[0]
      return None
   def fetch_all(self, sql, *args):
      rows = self.exec(sql, *args)
      return list(rows)
   def insert(self, sql, *args):
      affected = self.exec(sql, *args)
      if affected is None or isinstance(affected, int) == False:
         affected = 0
      return affected
   def update(self, sql, *args):
      affected = self.exec(sql, *args)
      if affected is None or isinstance(affected, int) == False:
         affected = 0
      return affected
   def delete(self, sql, *args):
      affected = self.exec(sql, *args)
      if affected is None or isinstance(affected, int) == False:
         affected = 0
      return affected