#!/usr/bin/python3
# -*- coding: utf-8 -*-
# @Author  : dxyc0922
# @Time    : 2025/12/30
# @file    : 最大.py

# 导入必要的库
import threading
import requests as requests_lib  # HTTP请求库，用于发送网络请求
import sys                      # 系统相关功能
import base64 as base64_lib     # base64编码解码库
from base.spider import Spider as BaseSpider  # 导入基础爬虫类
from urllib import parse as urlparse_lib      # URL解析库

# 添加上级目录到系统路径
sys.path.append('..')


class Spider(BaseSpider):
    """
    最大资源爬虫类
    继承自BaseSpider，实现视频资源的爬取功能
    """

    def __init__(self):
        """
        初始化方法
        """
        super().__init__()  # 调用父类初始化方法
        self.name = ''      # 爬虫名称
        self.home_url = ''  # 网站主页URL
        self.api_url = ''  # API接口URL
        self.headers = {}   # HTTP请求头
        # 定义需要过滤的类型ID
        self.filted_type_ids = {55, 56, 57, 58, 59, 60, 61, 73, 74}  # 过滤类型ID

    def getName(self):
        """
        获取爬虫名称

        Returns:
            str: 爬虫名称
        """
        return self.name

    def init(self, extend=''):
        """
        初始化爬虫

        Args:
            extend (str): 扩展参数，默认为空字符串
        """
        self.name = '最大资源'  # 爬虫名称
        self.home_url = 'https://www.zuidazy.com'  # 网站主页URL
        self.api_url = 'https://api.zuidapi.com/api.php/provide/vod/'  # 获取视频数据API
        # 设置请求头，模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0',
            'Referer': self.home_url,  # 添加Referer头，可能对图片防盗链有帮助
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'}

    def getDependence(self):
        """
        获取依赖项

        Returns:
            list: 依赖项列表，此爬虫无依赖项
        """
        return []

    def isVideoFormat(self, url):
        """
        判断是否为视频格式

        Args:
            url (str): URL地址

        Returns:
            bool: 总是返回False，表示不进行视频格式判断
        """
        return False

    def manualVideoCheck(self):
        """
        手动视频检查

        Returns:
            bool: 总是返回False，表示不需要手动视频检查
        """
        return False

    def should_filter_video(self, video_info):
        """
        判断是否应该过滤视频（伦理片）

        Args:
            video_info (dict): 视频信息字典

        Returns:
            bool: 如果需要过滤返回True，否则返回False
        """
        type_id = int(video_info.get('type_id', 0))
        return type_id in self.filted_type_ids

    def homeContent(self, filter):
        """
        获取首页内容，包括分类和筛选条件

        Args:
            filter: 过滤条件

        Returns:
            dict: 包含分类信息和筛选条件的字典
        """
        # 返回分类信息
        # 同时返回各分类下的子分类
        return {
            'class': [
                {'type_id': '53', 'type_name': '影视解说'},  # 影视解说
                {'type_id': '1', 'type_name': '电影片'},    # 电影片分类
                {'type_id': '2', 'type_name': '连续剧'},    # 连续剧分类
                {'type_id': '4', 'type_name': '动漫片'},    # 动漫片分类
                {'type_id': '3', 'type_name': '综艺片'},    # 综艺片分类
                {'type_id': '47', 'type_name': '音乐'},     # 音乐分类
                {'type_id': '48', 'type_name': '体育'},     # 体育分类
                {'type_id': '54', 'type_name': '短剧'}       # 短剧分类
            ],
            'filters': {
                # 电影分类下的子分类
                '1': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '动作片', 'v': '6'},    # 动作片
                    {'n': '喜剧片', 'v': '7'},    # 喜剧片
                    {'n': '爱情片', 'v': '8'},    # 爱情片
                    {'n': '科幻片', 'v': '9'},    # 科幻片
                    {'n': '恐怖片', 'v': '10'},    # 恐怖片
                    {'n': '剧情片', 'v': '11'},    # 剧情片
                    {'n': '战争片', 'v': '12'},    # 战争片
                    {'n': '纪录片', 'v': '20'},    # 纪录片
                    {'n': '4K电影', 'v': '62'},    # 4K电影
                    {'n': '邵氏电影', 'v': '70'},    # 邵氏电影
                    {'n': 'Netflix电影', 'v': '71'}    # Netflix电影
                ]},
                # 连续剧分类下的子分类
                '2': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '国产剧', 'v': '13'},    # 国产剧
                    {'n': '香港剧', 'v': '17'},    # 香港剧
                    {'n': '韩国剧', 'v': '15'},    # 韩国剧
                    {'n': '欧美剧', 'v': '14'},    # 欧美剧
                    {'n': '台湾剧', 'v': '18'},    # 台湾剧
                    {'n': '日本剧', 'v': '16'},    # 日本剧
                    {'n': '海外剧', 'v': '23'},    # 海外剧
                    {'n': '泰国剧', 'v': '19'},     # 泰国剧
                    {'n': 'Netflix自制剧', 'v': '72'}     # Netflix自制剧
                ]},
                # 综艺分类下的子分类
                '3': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '大陆综艺', 'v': '25'},  # 大陆综艺
                    {'n': '港台综艺', 'v': '27'},  # 港台综艺
                    {'n': '日韩综艺', 'v': '26'},  # 日韩综艺
                    {'n': '欧美综艺', 'v': '28'}   # 欧美综艺
                ]},
                # 动漫分类下的子分类
                '4': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '国产动漫', 'v': '29'},  # 国产动漫
                    {'n': '日韩动漫', 'v': '30'},  # 日韩动漫
                    {'n': '欧美动漫', 'v': '31'},  # 欧美动漫
                    {'n': '港台动漫', 'v': '44'},  # 港台动漫
                    {'n': '海外动漫', 'v': '45'},  # 海外动漫
                    {'n': '动漫电影', 'v': '39'}   # 动漫电影
                ]},
                # 体育分类下的子分类
                '48': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '篮球', 'v': '49'},  # 篮球
                    {'n': '足球', 'v': '50'},  # 足球
                    {'n': '斯诺克', 'v': '52'}  # 斯诺克
                ]},
                # 短剧分类下的子分类
                '54': {'key': 'cid', 'name': '分类', 'value': [
                    {'n': '有声动漫', 'v': '63'},  # 有声动漫
                    {'n': '女频恋爱', 'v': '64'},  # 女频恋爱
                    {'n': '反转爽剧', 'v': '65'},  # 反转爽剧
                    {'n': '古装仙侠', 'v': '66'},  # 古装仙侠
                    {'n': '年代穿越', 'v': '67'},  # 年代穿越
                    {'n': '脑洞悬疑', 'v': '68'},  # 脑洞悬疑
                    {'n': '现代都市', 'v': '69'},  # 现代都市
                ]}
            }
        }

    def homeVideoContent(self):
        """
        获取首页视频内容

        Returns:
            dict: 包含视频列表和分页信息的字典
        """
        videos = []  # 存储视频信息的列表
        try:
            # 获取首页推荐视频数据
            response = requests_lib.get(f"{self.home_url}/index.php/ajax/data?mid=1",
                                        headers=self.headers)
            video_list = response.json()['list']  # 解析返回的JSON数据
            # 提取视频信息并添加到列表中，过滤掉伦理片
            for video_info in video_list:
                # 过滤掉伦理片
                if not self.should_filter_video(video_info):
                    videos.append({
                        'vod_id': video_info['vod_id'],  # 视频ID
                        'vod_name': video_info['vod_name'],  # 视频名称
                        'vod_pic': video_info['vod_pic'],  # 视频图片
                        'vod_remarks': video_info['vod_remarks']   # 视频备注
                    })
        except requests_lib.RequestException as e:
            # 请求失败时返回空列表
            return {'list': [], 'page': 0, 'pagecount': 0, 'limit': 0, 'total': 0}
        # 返回视频列表
        return {'list': videos, 'page': 1, 'pagecount': 1, 'limit': len(videos), 'total': len(videos)}

    def _perform_category_request(self, tid, pg, filter, ext):
        """
        执行分类内容请求的内部方法
        """
        # 获取分类ID，如果有扩展参数则使用扩展参数
        category_id = tid
        if ext and 'cid' in ext:
            category_id = ext['cid']
        # 构建请求URL，使用正确的参数名
        url = f"{self.home_url}/index.php/ajax/data?mid=1&tid={category_id}&page={pg}&limit=10"
        videos = []  # 存储分类视频信息的列表
        try:
            # 发送请求并解析返回数据
            response = requests_lib.get(url, headers=self.headers)
            video_list = response.json()['list']
            # 提取视频信息并添加到列表中，过滤掉伦理片
            for video_info in video_list:
                # 过滤掉伦理片
                if not self.should_filter_video(video_info):
                    videos.append({
                        'vod_id': video_info['vod_id'],  # 视频ID
                        'vod_name': video_info['vod_name'],  # 视频名称
                        'vod_pic': video_info['vod_pic'],  # 视频图片
                        'vod_remarks': video_info['vod_remarks']   # 视频备注
                    })
        except requests_lib.RequestException as e:
            # 请求失败时返回错误信息
            return {'list': [], 'msg': str(e), 'page': 0, 'pagecount': 0, 'limit': 0, 'total': 0}
        # 返回视频列表
        return {'list': videos, 'page': int(pg), 'pagecount': 999, 'limit': 10, 'total': 999}

    def categoryContent(self, tid, pg, filter, ext, callback=None):
        """
        获取分类内容

        Args:
            tid (str): 分类ID
            pg (str): 页码
            filter: 过滤条件
            ext (dict): 扩展参数
            callback: 回调函数，用于返回结果

        Returns:
            dict: 包含分类视频列表和分页信息的字典
        """
        return self._perform_category_request(tid, pg, filter, ext)

    def detailContent(self, did):
        """
        获取视频详情内容

        Args:
            did (list): 视频ID列表

        Returns:
            dict: 包含视频详情和分页信息的字典
        """
        video_id = did[0]  # 获取第一个视频ID
        videos = []  # 存储视频详情的列表
        try:
            # 获取视频详细信息
            response = requests_lib.get(
                f"{self.api_url}?ac=detail&ids={video_id}",
                headers=self.headers)
            video_detail = response.json()['list'][0]
            # 检查视频是否为伦理片，如果是则跳过
            if not self.should_filter_video(video_detail):
                videos.append({
                    'type_name': video_detail['type_name'],  # 类型名称
                    'vod_id': video_detail['vod_id'],  # 视频ID
                    'vod_name': video_detail['vod_name'],  # 视频名称
                    'vod_remarks': video_detail['vod_remarks'],  # 视频备注
                    'vod_year': video_detail['vod_year'],  # 年份
                    'vod_area': video_detail['vod_area'],  # 地区
                    'vod_actor': video_detail['vod_actor'],  # 演员
                    'vod_director': video_detail['vod_director'],  # 导演
                    'vod_content': video_detail['vod_content'],  # 简介
                    # 播放来源
                    'vod_play_from': video_detail['vod_play_from'],
                    # 播放地址
                    'vod_play_url': video_detail['vod_play_url'],
                    # 视频图片
                    'vod_pic': video_detail['vod_pic']
                })
        except requests_lib.RequestException as e:
            # 请求失败时返回错误信息
            return {'list': [], 'msg': str(e), 'page': 0, 'pagecount': 0, 'limit': 0, 'total': 0}
        # 返回视频详情
        return {'list': videos, 'page': 1, 'pagecount': 1, 'limit': 1, 'total': 1}

    def searchContent(self, key, quick, pg='1'):
        """
        搜索视频内容

        Args:
            key (str): 搜索关键词
            quick (bool): 是否快速搜索
            pg (str): 页码，默认为'1'

        Returns:
            dict: 包含搜索结果和分页信息的字典
        """
        search_key = key  # 搜索关键词
        results = []   # 存储搜索结果的列表
        try:
            # 发送搜索请求
            response = requests_lib.get(
                f"{self.api_url}?ac=detail&wd={search_key}",
                headers=self.headers)
            video_list = response.json()['list']  # 解析返回数据
            # 提取搜索结果并添加到列表中，过滤掉伦理片
            for video_info in video_list:
                # 过滤掉伦理片
                if not self.should_filter_video(video_info):
                    results.append({
                        'vod_id': video_info['vod_id'],  # 视频ID
                        'vod_name': video_info['vod_name'],  # 视频名称
                        'vod_pic': video_info['vod_pic'],  # 视频图片
                        'vod_remarks': video_info['vod_remarks']   # 视频备注
                    })
        except requests_lib.RequestException as e:
            # 请求失败时返回错误信息
            return {'list': [], 'msg': str(e), 'page': 0, 'pagecount': 0, 'limit': 0, 'total': 0}
        # 返回搜索结果
        return {'list': results, 'page': int(pg), 'pagecount': 1, 'limit': len(results), 'total': len(results)}

    def playerContent(self, flag, id, vipFlags):
        """
        获取播放内容

        Args:
            flag (str): 播放标志
            id (str): 视频ID
            vipFlags: VIP标志

        Returns:
            dict: 包含播放URL和播放信息的字典
        """
        # 构建播放URL（使用base64编码）
        # play_url = self.getProxyUrl() + f"&url={self.b64encode(id)}"
        # 返回播放信息
        return {'url': id, 'header': self.headers, 'parse': 0, 'jx': 0}

    def localProxy(self, params):
        """
        本地代理方法，用于处理广告

        Args:
            params (dict): 代理参数

        Returns:
            list: 包含状态码、内容类型和处理后内容的列表
        """
        # 解码URL并删除广告
        decoded_url = self.b64decode(params['url'])
        cleaned_content = self.del_ads(decoded_url)
        return [200, 'application/vnd.apple.mpegurl', cleaned_content]

    def destroy(self):
        """
        销毁方法

        Returns:
            str: 销毁状态信息
        """
        return '正在Destroy'

    def b64encode(self, data):
        """
        base64编码方法

        Args:
            data (str): 需要编码的数据

        Returns:
            str: base64编码后的字符串
        """
        return base64_lib.b64encode(data.encode('utf-8')).decode('utf-8')

    def b64decode(self, data):
        """
        base64解码方法

        Args:
            data (str): 需要解码的数据

        Returns:
            str: base64解码后的字符串
        """
        return base64_lib.b64decode(data.encode('utf-8')).decode('utf-8')

    def del_ads(self, url):
        """
        删除广告的方法

        Args:
            url (str): 视频播放URL

        Returns:
            str: 去除广告后的内容
        """
        # 定义协议和路径分隔符
        protocol = 'http'
        full_url = url
        path_separator = '/'
        # 发送请求获取内容
        response = requests_lib.get(url=full_url, headers=self.headers)

        if response.status_code != 200:
            return ''

        # 分割返回的内容为行
        content_lines = response.text.splitlines()

        # 检查是否为M3U8格式并处理混合内容
        if content_lines and content_lines[0] == '#EXTM3U' and len(content_lines) > 2 and 'mixed.m3u8' in content_lines[2]:
            redirect_url = content_lines[2]
            if redirect_url.startswith(protocol):
                pass  # 已是完整URL
            elif redirect_url.startswith(path_separator):
                redirect_url = self._build_base_url(full_url) + redirect_url
            else:
                redirect_url = full_url.rsplit(path_separator, maxsplit=1)[
                    0] + path_separator + redirect_url
            # 递归处理广告
            return self.del_ads(redirect_url)
        else:
            return self._process_m3u8_content(content_lines, full_url)

    def _build_base_url(self, full_url):
        """
        构建基础URL

        Args:
            full_url (str): 完整URL

        Returns:
            str: 基础URL
        """
        parsed_url = urlparse_lib.urlparse(full_url)
        return urlparse_lib.urlunparse([parsed_url.scheme, parsed_url.netloc, '', '', '', ''])

    def _process_m3u8_content(self, content_lines, original_url):
        """
        处理M3U8内容，移除广告

        Args:
            content_lines (list): M3U8内容行列表
            original_url (str): 原始URL

        Returns:
            str: 处理后的内容
        """
        # 构建基础URL
        base_url = original_url.rsplit('/', maxsplit=1)[0] + '/'
        base_url_full = self._build_base_url(original_url)

        processed_lines = []  # 存储处理后的行
        discontinuity_indices = []  # 存储不连续性标记的索引

        # 处理每一行内容
        for index, line in enumerate(content_lines):
            if '.ts' in line:
                # 处理.ts文件路径
                if line.startswith('http'):
                    processed_lines.append(line)
                elif line.startswith('/'):
                    processed_lines.append(base_url_full + line.lstrip('/'))
                else:
                    processed_lines.append(base_url + line)
            elif line == '#EXT-X-DISCONTINUITY':
                # 记录不连续性标记的位置
                processed_lines.append(line)
                discontinuity_indices.append(index)
            else:
                processed_lines.append(line)

        removal_ranges = []  # 要删除的区间
        # 根据不连续性标记确定要删除的区间
        if len(discontinuity_indices) >= 1:
            removal_ranges.append(
                (discontinuity_indices[0], discontinuity_indices[0]))
        if len(discontinuity_indices) >= 3:
            removal_ranges.append(
                (discontinuity_indices[1], discontinuity_indices[2]))
        if len(discontinuity_indices) >= 5:
            removal_ranges.append(
                (discontinuity_indices[3], discontinuity_indices[4]))

        # 过滤掉不需要的行
        filtered_lines = [line for index, line in enumerate(processed_lines)
                          if not any(start <= index <= end for start, end in removal_ranges)]

        return '\n'.join(filtered_lines)


# 主程序入口
if __name__ == '__main__':
    # pass
    Spider = Spider()
    Spider.init()
    print(Spider.homeVideoContent())
    # print(Spider._perform_category_request('1', '1', '', ''))
    # print(Spider.detailContent(['116658']))
