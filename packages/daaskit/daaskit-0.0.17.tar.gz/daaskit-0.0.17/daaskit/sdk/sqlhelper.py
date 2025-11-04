#!/usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
from daaskit.sdk import util, sql as sdk_sql
from daaskit.sdk.log import logger

def connect(pooledDB):
   # 创建连接
   # conn = pymysql.connect(host='192.168.11.38', port=3306, user='root', passwd='apNXgF6RDitFtDQx', db='m2day03db')
   conn = pooledDB.connection()
   # 创建游标
   cursor = conn.cursor(pymysql.cursors.DictCursor)
   return conn,cursor
def close(conn,cursor):
   # 关闭游标
   cursor.close()
   # 关闭连接
   conn.close()
def fetch_one(pooledDB, sql, args=[]):
   if util.class_method_exist(pooledDB, "fetch_one"):
      return pooledDB.fetch_one(sql, args)
   conn,cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   effect_row = cursor.execute(sql,args)
   result = cursor.fetchone()
   close(conn,cursor)
   return result
def fetch_all(pooledDB, sql, args=[]):
   if util.class_method_exist(pooledDB, "fetch_all"):
      return pooledDB.fetch_all(sql, args)
   conn, cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   cursor.execute(sql,args)
   result = cursor.fetchall()
   close(conn, cursor)
   return result
def insert(pooledDB, sql, args):
   """
   创建数据
   :param sql: 含有占位符的SQL
   :return:
   """
   if util.class_method_exist(pooledDB, "insert"):
      return pooledDB.insert(sql, args)
   conn, cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   effect_row = cursor.execute(sql,args)
   conn.commit()
   close(conn, cursor)
def delete(pooledDB, sql, args=[]):
   """
   创建数据
   :param sql: 含有占位符的SQL
   :return:
   """
   if util.class_method_exist(pooledDB, "delete"):
      return pooledDB.delete(sql, args)
   conn, cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   effect_row = cursor.execute(sql,args)
   conn.commit()
   close(conn, cursor)
   return effect_row
def update(pooledDB, sql, args):
   if util.class_method_exist(pooledDB, "update"):
      return pooledDB.update(sql, args)
   conn, cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   effect_row = cursor.execute(sql, args)
   conn.commit()
   close(conn, cursor)
   return effect_row
def exec(pooledDB, sql, args=[]):
   if util.class_method_exist(pooledDB, "exec"):
      return pooledDB.exec(sql, args)
   conn, cursor = connect(pooledDB)
   # 执行SQL，并返回收影响行数
   effect_row = cursor.execute(sql, args)
   conn.commit()
   close(conn, cursor)
   return effect_row

pooledDBDict = {}

try:
   # 初始化
   pooledDBDict["backend"] = sdk_sql.DB(backend=True)
   domains = fetch_all(pooledDBDict["backend"], "select * from sys_domain where del_flag = 0")
   for domain in domains:
      domainstr = domain["domain"]
      pooledDB = pooledDBDict.get(domainstr)
      if pooledDB != None:
         continue
      pooledDBDict[domainstr] = sdk_sql.DB(domain=domainstr)
except Exception as e:
   logger.error(f"init sqlhelper failed: {e}")