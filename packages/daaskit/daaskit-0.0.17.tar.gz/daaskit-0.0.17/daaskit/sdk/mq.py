import json
from nats.aio.client import Client as NATS
from daaskit.sdk import util

_defaultnatsusername = util.get_env("ENV_NATS_USERNAME", "wing")
_defaultnatspassword = util.get_env('ENV_NATS_PASSWORD', 'bar')
_defaultnatsserver = 'nats://%s:4222' % (util.get_host_with_ns('nats-server'))
_globalnatsserver = util.get_env('ENV_NATS_HOST', _defaultnatsserver)


class MQ:
   def __init__(self, natsserver=None, username=None, password=None):
      if natsserver == None:
         natsserver = _globalnatsserver
      if username == None:
         username = _defaultnatsusername
      if password == None:
         password = _defaultnatspassword

      self.natsserver = natsserver
      self.username = username
      self.password = password
      self.nc = NATS()
      self.status = 'idel'

   async def connect(self):
      async def disconnected_cb():
         print("Got disconnected...")

      async def reconnected_cb():
         print("Got reconnected...")

      await self.nc.connect(self.natsserver,
         user=self.username,
         password=self.password,
         reconnected_cb=reconnected_cb,
         disconnected_cb=disconnected_cb,
         max_reconnect_attempts=-1)
      self.status = 'connected'

   async def close(self):
      if self.status == 'connected':
         await self.nc.close()

   def isclosed(self):
       if self.status == 'connected':
         return self.nc.is_closed
       else:
          return False

   # 订阅设备数据
   # handler：处理函数
   # deviceids：指定设备id列表，空则不过滤
   async def subdev(self, handler, deviceids=None):
      async def msg_handler(msg):
         data = msg.data.decode()
         obj = json.loads(data)
         if deviceids == None or len(deviceids) == 0:
             await handler(msg, data)
             return

         if obj['device_id'] in deviceids:
            await handler(msg, data)

      subject = 'qqs.device.data.report.inner'
      await self.nc.subscribe(subject, cb=msg_handler)

   # 订阅指定主题
   # handler：处理函数
   # subject：主题名称
   async def subtopic(self, handler, subject='test_topic'):
      async def msg_handler(msg):
         data = msg.data.decode()
         await handler(data)

      await self.nc.subscribe(subject, cb=msg_handler)

   # 发布消息
   # subject：主题名称
   # data：消息数据
   async def pubmsg(self, subject, data):
      await self.nc.publish(subject, data.encode())
