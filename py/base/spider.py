"""
猫vod爬虫基类
提供基础的爬虫功能，包括网络请求、HTML解析、缓存管理等
"""
import re
# import os
import json
# import time
import requests
from lxml import etree
# from com.github.catvod import Proxy
# from com.chaquo.python import Python
from abc import abstractmethod, ABCMeta
# from importlib.machinery import SourceFileLoader


class Spider(metaclass=ABCMeta):
    """
    爬虫基类，实现单例模式
    定义了爬虫需要实现的抽象方法和通用工具方法
    """
    _instance = None

    def __init__(self):
        """
        初始化方法
        """
        self.extend = ''

    def __new__(cls, *args, **kwargs):
        """
        单例模式实现
        确保整个应用中只有一个Spider实例
        """
        if cls._instance:
            return cls._instance
        else:
            cls._instance = super().__new__(cls)
            return cls._instance

    @abstractmethod
    def init(self, extend=""):
        """
        初始化方法，子类必须实现
        用于初始化爬虫相关配置
        :param extend: 扩展参数
        """
        pass

    def homeContent(self, filter):
        """
        首页内容，子类必须实现
        获取首页推荐内容
        :param filter: 过滤条件
        """
        pass

    def homeVideoContent(self):
        """
        首页视频内容，子类必须实现
        获取首页视频列表
        """
        pass

    def categoryContent(self, tid, pg, filter, extend):
        """
        分类内容，子类必须实现
        获取指定分类下的视频列表
        :param tid: 分类ID
        :param pg: 页码
        :param filter: 过滤条件
        :param extend: 扩展参数
        """
        pass

    def detailContent(self, ids):
        """
        详情内容，子类必须实现
        获取视频详情信息
        :param ids: 视频ID列表
        """
        pass

    def searchContent(self, key, quick, pg="1"):
        """
        搜索内容，子类必须实现
        根据关键词搜索视频
        :param key: 搜索关键词
        :param quick: 是否快速搜索
        :param pg: 页码
        """
        pass

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容，子类必须实现
        获取视频播放地址
        :param flag: 播放源标识
        :param id: 视频ID
        :param vipFlags: VIP标识列表
        """
        pass

    def liveContent(self, url):
        """
        直播内容，子类必须实现
        获取直播内容
        :param url: 直播地址
        """
        pass

    def localProxy(self, param):
        """
        本地代理，子类必须实现
        用于处理本地代理请求
        :param param: 代理参数
        """
        pass

    def isVideoFormat(self, url):
        """
        判断是否为视频格式，子类必须实现
        :param url: URL地址
        """
        pass

    def manualVideoCheck(self):
        """
        手动视频检测，子类必须实现
        """
        pass

    def action(self, action):
        """
        执行操作，子类必须实现
        :param action: 操作类型
        """
        pass

    def destroy(self):
        """
        销毁方法，子类必须实现
        用于清理资源
        """
        pass

    def getName(self):
        """
        获取爬虫名称，子类必须实现
        :return: 爬虫名称
        """
        pass

    def getDependence(self):
        """
        获取依赖，返回依赖的爬虫名称列表
        :return: 依赖列表
        """
        return []

    def loadSpider(self, name):
        """
        加载其他爬虫实例
        :param name: 爬虫名称
        :return: 爬虫实例
        """
        return self.loadModule(name).Spider()

    # def loadModule(self, name):
    #     """
    #     加载模块
    #     :param name: 模块名称
    #     :return: 模块对象
    #     """
    #     cache_dir = Python.getPlatform().getApplication().getCacheDir().getAbsolutePath()
    #     path = os.path.join(os.path.join(cache_dir, 'py'),  f'{name}.py')
    #     return SourceFileLoader(name, path).load_module()

    def regStr(self, reg, src, group=1):
        """
        正则表达式提取字符串
        :param reg: 正则表达式
        :param src: 源字符串
        :param group: 匹配组，默认为1
        :return: 提取的字符串
        """
        m = re.search(reg, src)
        src = ''
        if m:
            src = m.group(group)
        return src

    def removeHtmlTags(self, src):
        """
        移除HTML标签
        :param src: 包含HTML标签的字符串
        :return: 去除HTML标签后的字符串
        """
        clean = re.compile('<.*?>')
        return re.sub(clean, '', src)

    def cleanText(self, src):
        """
        清理文本，移除表情符号等特殊字符
        :param src: 源文本
        :return: 清理后的文本
        """
        clean = re.sub('[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', src)
        return clean

    def fetch(self, url, params=None, cookies=None, headers=None, timeout=5, verify=True, stream=False, allow_redirects = True):
        """
        发送GET请求
        :param url: 请求URL
        :param params: URL参数
        :param cookies: Cookie信息
        :param headers: 请求头
        :param timeout: 超时时间
        :param verify: 是否验证SSL证书
        :param stream: 是否使用流式请求
        :param allow_redirects: 是否允许重定向
        :return: Response对象
        """
        rsp = requests.get(url, params=params, cookies=cookies, headers=headers, timeout=timeout, verify=verify, stream=stream, allow_redirects=allow_redirects)
        rsp.encoding = 'utf-8'
        return rsp

    def post(self, url, params=None, data=None, json=None, cookies=None, headers=None, timeout=5, verify=True, stream=False, allow_redirects = True):
        """
        发送POST请求
        :param url: 请求URL
        :param params: URL参数
        :param data: 表单数据
        :param json: JSON数据
        :param cookies: Cookie信息
        :param headers: 请求头
        :param timeout: 超时时间
        :param verify: 是否验证SSL证书
        :param stream: 是否使用流式请求
        :param allow_redirects: 是否允许重定向
        :return: Response对象
        """
        rsp = requests.post(url, params=params, data=data, json=json, cookies=cookies, headers=headers, timeout=timeout, verify=verify, stream=stream, allow_redirects=allow_redirects)
        rsp.encoding = 'utf-8'
        return rsp

    def html(self, content):
        """
        解析HTML内容
        :param content: HTML字符串
        :return: etree对象
        """
        return etree.HTML(content)

    def str2json(self, str):
        """
        字符串转JSON
        :param str: JSON字符串
        :return: JSON对象
        """
        return json.loads(str)

    def json2str(self, str):
        """
        JSON转字符串
        :param str: JSON对象
        :return: JSON字符串
        """
        return json.dumps(str, ensure_ascii=False)
    
    # def getProxyUrl(self, local=True):
    #     """
    #     获取代理URL
    #     :param local: 是否使用本地代理
    #     :return: 代理URL
    #     """
    #     return f'{Proxy.getUrl(local)}?do=py'

    def log(self, msg):
        """
        打印日志
        :param msg: 日志消息
        """
        if isinstance(msg, dict) or isinstance(msg, list):
            print(json.dumps(msg, ensure_ascii=False))
        else:
            print(f'{msg}')

    # def getCache(self, key):
    #     """
    #     获取缓存
    #     :param key: 缓存键
    #     :return: 缓存值，如果不存在或过期则返回None
    #     """
    #     value = self.fetch(f'http://127.0.0.1:{Proxy.getPort()}/cache?do=get&key={key}', timeout=5).text
    #     if len(value) > 0:
    #         if value.startswith('{') and value.endswith('}') or value.startswith('[') and value.endswith(']'):
    #             value = json.loads(value)
    #             if type(value) == dict:
    #                 if not 'expiresAt' in value or value['expiresAt'] >= int(time.time()):
    #                     return value
    #                 else:
    #                     self.delCache(key)
    #                     return None
    #         return value
    #     else:
    #         return None

    # def setCache(self, key, value):
    #     """
    #     设置缓存
    #     :param key: 缓存键
    #     :param value: 缓存值
    #     :return: 操作结果
    #     """
    #     if type(value) in [int, float]:
    #         value = str(value)
    #     if len(value) > 0:
    #         if type(value) == dict or type(value) == list:
    #             value = json.dumps(value, ensure_ascii=False)
    #     r = self.post(f'http://127.0.0.1:{Proxy.getPort()}/cache?do=set&key={key}', data={"value": value}, timeout=5)
    #     return 'succeed' if r.status_code == 200 else 'failed'

    # def delCache(self, key):
    #     """
    #     删除缓存
    #     :param key: 缓存键
    #     :return: 操作结果
    #     """
    #     r = self.fetch(f'http://127.0.0.1:{Proxy.getPort()}/cache?do=del&key={key}', timeout=5)
    #     return 'succeed' if r.status_code == 200 else 'failed'