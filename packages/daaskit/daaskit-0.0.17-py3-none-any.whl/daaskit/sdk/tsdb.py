from daaskit.sdk import util
import influxdb_client                                      # influxdb2.*
from influxdb_client.client.write_api import SYNCHRONOUS    # influxdb2.*
from influxdb import InfluxDBClient


_globalorg = util.get_env('ENV_TSDB_ORG', "daasdev")
_globalusername = util.get_env('ENV_TSDB_USERNAME', "root") 
_globalpassword = util.get_env('ENV_TSDB_PASSWORD', "daasdev@#20222")
_globalurl = util.get_env('ENV_TSDB_URL', "http://" + util.get_host_with_ns('tdb') + ":8086") 

# idb 1.*
class DB1:
    # 初始化
    # domain：域
    # url：dburl，例如：http://localhost:8086
    def __init__(self, domain=None, url=None, username=None, password=None):
        if domain == None:
            domain = 'cvxa3663'
        if url == None:
            url = _globalurl
        if username == None:
            username = _globalusername
        if password == None:
            password = _globalpassword
        host, port = util.get_host_port_by_url(url)
        self.client = InfluxDBClient(host, port, username, password, domain)
        self.client.create_database(domain)
    
    def __del__(self):
        self.client.close()

    # 查询
    # query：查询语句，例如select value from cpu_load_short where host=$host
    # params：参数，例如：{'host': 'server01'}
    def query(self, query, params=None):
        if params == None:
            return self.client.query(query)
        else:
            return self.client.query(query, bind_params=params)
    
    # 插入一条记录
    # measurement：表名
    # tags：索引集合，例如{"host": "host1", "region": "region1"}
    # fields：值集合，例如{"count": 10, "data": 100}
    # time：时间
    def insert(self, measurement, tags, fields=None, time=None):
        row = {
            "measurement": measurement,
            "tags": tags
        }
        if fields != None:
            row['fields'] = fields
        if time != None:
            row['time'] = time
        self.client.write_points([row])
    
    # 插入多条记录
    # rows：记录列表，如：[
    #    {
    #       "measurement": "cpu_load_short",
    #        "tags": {
    #            "host": "server01",
    #            "region": "us-west"
    #        },
    #        "time": "2009-11-10T23:00:00Z",
    #        "fields": {
    #            "value": 0.64
    #        }
    #    }
    # ]
    def inserts(self, rows):
        self.client.write_points(rows)

# idb 2.*
class DB2:
    def __init__(self, domain='cvxa3663', url=None, org=None, username=None, password=None):
        if url == None:
            url = _globalurl
        if org == None:
            org = _globalorg
        if username == None:
            username = _globalusername
        if password == None:
            password = _globalpassword
            
        self.bucket = domain
        self.client = influxdb_client.InfluxDBClient(
            url=url,
            org=org,
            username=username,
            password=password
        )
        buckets_api = self.client.buckets_api()
        bucketobj = buckets_api.find_bucket_by_name(self.bucket)
        if bucketobj == None:
            buckets_api.create_bucket(bucket_name=self.bucket)

    def __del__(self):
        self.client.close()
        self.bucket = ''
        
    # 插入，
    # tags: 索引列表，如{"device_id":"dev1","field": "temp"}
    # fields: 值列表，如{"value": 25.5}
    def insert(self, measurement, tags, fields, time=None):
        if measurement.strip() == '':
            return
        
        # Write script
        write_api = self.client.write_api(write_options=SYNCHRONOUS)

        p = influxdb_client.Point(measurement) 
        for key in tags.keys():
            p = p.tag(key, tags[key])
        for key in fields.keys():
            p = p.field(key, fields[key])
        if time != None:
            p.time(time)

        write_api.write(bucket=self.bucket, record=p)

    def queryby(self, measurement, range, filter, limit = None, sortfields = None, groupfields = None, funcs = None):
        query = self._getfrom() + self._getrange(range) 
        query += self._getmeasurement(measurement) + self._getfilters(filter) + self._getsort(sortfields)
        query += self._getlimit(limit) + self._getgroup(groupfields)
        if funcs != None and len(funcs) > 0:
            for func in funcs:
                query += " |> " + func
        return self.query(query)

    def query(self, query):
        query_api = self.client.query_api()
        return query_api.query(query=query)

    def _getfrom(self):
        return 'from(bucket: "%s") ' % (self.bucket)
    
    def _getmeasurement(self, measurement):
        return '|> filter(fn:(r) => r._measurement == "%s") ' % (measurement)
    
    def _getrange(self, range):
        if range == None or (range.get('start') == None and range.get('stop') == None):
            return ' '
        startStopStr = ''
        if range.get('start') != None:
            startStopStr += 'start: %s' % range.get('start')
        if range.get('stop') != None:
            if startStopStr == '':
                startStopStr += 'stop: %s' % range.get('stop')
            else:
                startStopStr += ', stop: %s' % range.get('stop')
        return '|> range(%s) ' % startStopStr
    
    def _getfilters(self, filter):
        filterstr = ''
        if filter == None:
            return filterstr
        for key in filter.keys():
            filterstr += '|> filter(fn: (r) => r.%s == "%s") ' % (key, filter[key])
        return filterstr
    
    def _getgroup(self, groupfields):
        if groupfields == None or len(groupfields) == 0:
            return ' '
        return '|> group(columns: ["' + '","'.join(groupfields) + '"]) '
    
    def _getsort(self, sortfields):
        if sortfields == None or len(sortfields) == 0:
            return ' '
        return '|> sort(columns: ["' + '","'.join(sortfields) + '"]) '
    
    def _getlimit(self, count):
        if count == None:
            return ' '
        return '|> limit(n:%d) ' % (count)
