import re
import os
import json
import time
import requests
from lxml import etree
from com.github.catvod import Proxy  # type: ignore
from com.chaquo.python import Python  # type: ignore
from abc import abstractmethod, ABCMeta
from importlib.machinery import SourceFileLoader
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import parse as urlparse_lib      # URL解析库


class Spider:
    """
    非凡资源站爬虫实现
    API接口: hhttp://api.ffzyapi.com/api.php/provide/vod/
    支持首页、分类、搜索、详情和播放功能
    """

    # 常量定义
    API_URL = "http://api.ffzyapi.com/api.php/provide/vod/"
    SITE_URL = "https://ffzy.tv"
    SPIDER_NAME = "非凡资源站"
    EXCLUDE_CATEGORIES = {34}  # 伦理片分类ID
    MAIN_CATEGORIES = {"1", "2", "3", "4"}  # 一级分类ID
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def __init__(self):
        self.extend = ""

    def getName(self):
        """
        获取爬虫名称
        :return: 爬虫名称
        """
        return self.SPIDER_NAME

    def getDependence(self):
        """
        获取依赖库
        :return: 依赖库列表
        """
        return ["requests", "lxml"]

    def init(self, extend=""):
        """
        初始化爬虫
        :param extend: 扩展参数
        """
        self.extend = extend
        print(f"非凡资源站爬虫初始化完成，扩展参数: {extend}")

    def homeContent(self, filter):
        """
        获取首页内容 - 实际是获取分类信息
        :param filter: 过滤条件
        :return: 分类信息和筛选条件
        """
        try:
            # 获取分类数据
            params = {
                "ac": "list",  # 使用list获取分类信息
                "pg": "1"
            }
            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取分类数据失败，状态码: {response.status_code}")
                return {"class": [], "filters": {}}

            data = json.loads(response.text)

            # 提取分类信息 - 只获取一级分类（type_pid为0），过滤掉伦理片分类
            categories = []
            if "class" in data and data["class"]:
                for cat in data["class"]:
                    # 只添加一级分类（type_pid为0），并过滤掉伦理片分类
                    if cat.get("type_pid", 0) == 0 and cat.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        category = {
                            "type_id": str(cat["type_id"]),
                            "type_name": cat["type_name"]
                        }
                        categories.append(category)

            # 根据API返回的分类数据动态构建筛选条件，过滤掉伦理片
            sub_categories = {}
            if "class" in data and data["class"]:
                for cat in data["class"]:
                    type_pid = cat.get("type_pid", 0)
                    # 过滤掉伦理片分类
                    if type_pid in [1, 2, 3, 4] and cat.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        if str(type_pid) not in sub_categories:
                            sub_categories[str(type_pid)] = []
                        sub_categories[str(type_pid)].append({
                            "n": cat["type_name"],
                            "v": str(cat["type_id"])
                        })

            # 定义筛选条件 - 根据一级分类构建二级分类筛选，并从API数据中提取年份等信息
            filters = {}

            # 动态生成年份筛选选项（从API返回的数据中提取年份信息）
            current_year = int(time.strftime("%Y"))
            year_range = range(current_year, 2000 - 1, -1)  # 从当前年份到2000年
            year_options = [{"n": "全部", "v": ""}]
            for year in year_range:
                year_options.append({"n": str(year), "v": str(year)})

            # 电影片筛选
            if "1" in sub_categories:
                filters["1"] = [
                    {"key": "class", "name": "类型", "value": [
                        {"n": "全部", "v": ""},
                        *sub_categories["1"]  # 电影片的二级分类
                    ]},
                    {"key": "area", "name": "地区", "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "大陆"},
                        {"n": "香港", "v": "香港"},
                        {"n": "台湾", "v": "台湾"},
                        {"n": "美国", "v": "美国"},
                        {"n": "韩国", "v": "韩国"},
                        {"n": "日本", "v": "日本"},
                        {"n": "泰国", "v": "泰国"}
                    ]},
                    {"key": "year", "name": "年份", "value": year_options}
                ]

            # 连续剧筛选
            if "2" in sub_categories:
                filters["2"] = [
                    {"key": "class", "name": "类型", "value": [
                        {"n": "全部", "v": ""},
                        *sub_categories["2"]  # 连续剧的二级分类
                    ]},
                    {"key": "year", "name": "年份", "value": year_options}
                ]

            # 综艺片筛选
            if "3" in sub_categories:
                filters["3"] = [
                    {"key": "class", "name": "类型", "value": [
                        {"n": "全部", "v": ""},
                        *sub_categories["3"]  # 综艺片的二级分类
                    ]},
                    {"key": "year", "name": "年份", "value": year_options}
                ]

            # 动漫片筛选
            if "4" in sub_categories:
                filters["4"] = [
                    {"key": "class", "name": "类型", "value": [
                        {"n": "全部", "v": ""},
                        *sub_categories["4"]  # 动漫片的二级分类
                    ]},
                    {"key": "year", "name": "年份", "value": year_options}
                ]

            result = {
                "class": categories,
                "filters": filters if filter else {}  # 只有当filter为True时才返回筛选条件
            }
            print(f"分类信息获取成功: {len(categories)} 个分类")
            return result
        except Exception as e:
            print(f"获取分类信息失败: {str(e)}")
            return {"class": [], "filters": {}}

    def homeVideoContent(self):
        """
        获取首页视频内容 - 最新更新的视频列表
        :return: 首页视频内容数据
        """
        try:
            # 获取首页最新内容 - 使用ac=detail参数以获取完整信息
            params = {
                "ac": "detail",  # 使用detail参数获取完整信息，包括图片
                "pg": "1",
                "h": "24"  # 获取24小时内更新的内容
            }
            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取首页视频数据失败，状态码: {response.status_code}")
                return {"list": []}

            data = json.loads(response.text)
            videos = []

            if "list" in data and data["list"]:
                for item in data["list"]:
                    # 过滤掉伦理片分类的视频
                    if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        video = {
                            "vod_id": str(item["vod_id"]),
                            "vod_name": item["vod_name"],
                            # 现在可以从detail接口获取图片
                            "vod_pic": item.get("vod_pic", ""),
                            "vod_remarks": item.get("vod_remarks", ""),
                            "vod_year": item.get("vod_year", ""),
                            "vod_area": item.get("vod_area", ""),
                            "vod_lang": item.get("vod_lang", ""),
                            "vod_actor": item.get("vod_actor", ""),
                            "vod_director": item.get("vod_director", ""),
                            "vod_content": self.removeHtmlTags(item.get("vod_content", "")),
                            "type_name": item.get("type_name", "")
                        }
                        videos.append(video)

            result = {"list": videos}
            print(f"首页视频内容获取成功: {len(videos)} 个视频")
            return result
        except Exception as e:
            print(f"获取首页视频内容失败: {str(e)}")
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """
        获取分类内容
        :param tid: 分类ID
        :param pg: 页码
        :param filter: 过滤条件
        :param extend: 扩展参数
        :return: 分类内容数据
        """
        try:
            print(f"正在获取分类 {tid} 第 {pg} 页内容...")

            # 如果是一级分类（tid为1,2,3,4），则并发获取其子分类数据
            if tid in self.MAIN_CATEGORIES:
                return self._getMergedCategoryContent(tid, pg, extend)
            else:
                # 使用ac=detail参数以获取完整信息
                params = {
                    "ac": "detail",  # 使用detail参数获取完整信息，包括图片
                    "t": tid,        # 分类ID
                    "pg": pg         # 页码
                }

                # 添加其他筛选参数（除了class，因为class已经被用作分类ID）
                if extend:
                    for key, value in extend.items():
                        if key != "class" and value:  # 避免重复添加class参数，只添加非空的筛选参数
                            params[key] = value

                response = self.fetch(self.API_URL, params=params, headers={
                                      "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
                if response.status_code != 200:
                    print(f"获取分类数据失败，状态码: {response.status_code}")
                    return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

                data = json.loads(response.text)
                videos = []

                if "list" in data and data["list"]:
                    for item in data["list"]:
                        # 过滤掉伦理片分类的视频
                        if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                            video = {
                                "vod_id": str(item["vod_id"]),
                                "vod_name": item["vod_name"],
                                # 现在可以从detail接口获取图片
                                "vod_pic": item.get("vod_pic", ""),
                                "vod_remarks": item.get("vod_remarks", ""),
                                "vod_year": item.get("vod_year", ""),
                                "vod_area": item.get("vod_area", ""),
                                "vod_lang": item.get("vod_lang", ""),
                                "vod_actor": item.get("vod_actor", ""),
                                "vod_director": item.get("vod_director", ""),
                                "vod_content": self.removeHtmlTags(item.get("vod_content", "")),
                                "type_name": item.get("type_name", "")
                            }
                            videos.append(video)

                result = {
                    "list": videos,
                    "page": int(data.get("page", 1)),
                    "pagecount": int(data.get("pagecount", 1)),
                    "limit": int(data.get("limit", 20)),
                    "total": int(data.get("total", 0))
                }
                print(f"分类内容获取成功: {len(videos)} 个视频, 总计 {result['total']} 个")
                return result
        except Exception as e:
            print(f"获取分类内容失败: {str(e)}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def _getMergedCategoryContent(self, tid, pg, extend):
        """
        获取合并的一级分类内容（并发获取子分类数据）
        :param tid: 一级分类ID
        :param pg: 页码
        :param extend: 扩展参数
        :return: 合并后的分类内容数据
        """
        try:
            # 获取分类数据以确定子分类
            params = {
                "ac": "list",  # 使用list获取分类信息
                "pg": "1"
            }
            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取分类数据失败，状态码: {response.status_code}")
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            data = json.loads(response.text)

            # 获取该一级分类下的所有子分类
            sub_categories = []
            if "class" in data and data["class"]:
                for cat in data["class"]:
                    if str(cat.get("type_pid", 0)) == tid and cat.get("type_id") not in self.EXCLUDE_CATEGORIES:  # 过滤掉伦理片
                        sub_categories.append(str(cat["type_id"]))

            # 并发获取所有子分类的视频数据
            all_videos = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                # 提交所有子分类的请求
                future_to_cat = {
                    executor.submit(self._getSubCategoryVideos, cat_id, 1, extend): cat_id
                    for cat_id in sub_categories
                }

                # 收集结果
                for future in as_completed(future_to_cat):
                    cat_videos = future.result()
                    all_videos.extend(cat_videos)

            # 按更新时间排序（取最新的视频在前）
            all_videos.sort(key=lambda x: x.get("vod_time", ""), reverse=True)

            # 模拟分页
            start_idx = (int(pg) - 1) * 20
            end_idx = start_idx + 20
            paged_videos = all_videos[start_idx:end_idx]

            result = {
                "list": paged_videos,
                "page": int(pg),
                "pagecount": (len(all_videos) + 19) // 20,  # 计算总页数
                "limit": 20,
                "total": len(all_videos)
            }
            print(
                f"合并分类内容获取成功: {len(paged_videos)} 个视频, 总计 {result['total']} 个")
            return result
        except Exception as e:
            print(f"获取合并分类内容失败: {str(e)}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def _getSubCategoryVideos(self, cat_id, pg, extend):
        """
        获取子分类的视频数据
        :param cat_id: 子分类ID
        :param pg: 页码
        :param extend: 扩展参数
        :return: 视频列表
        """
        try:
            params = {
                "ac": "detail",
                "t": cat_id,
                "pg": pg
            }

            # 添加其他筛选参数
            if extend:
                for key, value in extend.items():
                    if key != "class" and value:  # 避免重复添加class参数，只添加非空的筛选参数
                        params[key] = value

            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取子分类数据失败，状态码: {response.status_code}")
                return []

            data = json.loads(response.text)
            videos = []

            if "list" in data and data["list"]:
                for item in data["list"]:
                    # 过滤掉伦理片分类的视频
                    if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        video = {
                            "vod_id": str(item["vod_id"]),
                            "vod_name": item["vod_name"],
                            "vod_pic": item.get("vod_pic", ""),
                            "vod_remarks": item.get("vod_remarks", ""),
                            "vod_year": item.get("vod_year", ""),
                            "vod_area": item.get("vod_area", ""),
                            "vod_lang": item.get("vod_lang", ""),
                            "vod_actor": item.get("vod_actor", ""),
                            "vod_director": item.get("vod_director", ""),
                            "vod_content": self.removeHtmlTags(item.get("vod_content", "")),
                            "type_name": item.get("type_name", ""),
                            "vod_time": item.get("vod_time", "")  # 用于排序
                        }
                        videos.append(video)

            return videos
        except Exception as e:
            print(f"获取子分类视频失败: {str(e)}")
            return []

    def detailContent(self, ids):
        """
        获取详情内容
        :param ids: 内容ID列表
        :return: 详情内容数据
        """
        try:
            print(f"正在获取详情内容，ID: {ids}")

            if not ids:
                return {"list": []}

            # 获取详情信息 - 支持批量获取
            ids_str = ','.join(ids)
            params = {
                "ac": "detail",
                "ids": ids_str
            }

            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取详情数据失败，状态码: {response.status_code}")
                return {"list": []}

            data = json.loads(response.text)
            details = []

            if "list" in data and data["list"]:
                for item in data["list"]:
                    # 过滤掉伦理片分类的视频
                    if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        detail = {
                            "vod_id": str(item["vod_id"]),
                            "vod_name": item["vod_name"],
                            "vod_pic": item.get("vod_pic", ""),  # 详情接口通常有图片
                            "type_name": item.get("type_name", ""),
                            "vod_year": item.get("vod_year", ""),
                            "vod_area": item.get("vod_area", ""),
                            "vod_remarks": item.get("vod_remarks", ""),
                            "vod_actor": item.get("vod_actor", ""),
                            "vod_director": item.get("vod_director", ""),
                            "vod_content": self.removeHtmlTags(item.get("vod_content", "")),
                            "vod_play_from": item.et("vod_play_from", ""),
                            "vod_play_url": item.get("vod_play_url", ""),
                            "vod_lang": item.get("vod_lang", ""),
                            "vod_class": item.get("vod_class", ""),
                            "vod_pubdate": item.get("vod_pubdate", "")
                        }
                        details.append(detail)

            result = {"list": details}
            print(f"详情内容获取成功: {len(details)} 个详情")
            return result
        except Exception as e:
            print(f"获取详情内容失败: {str(e)}")
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        """
        搜索内容
        :param key: 搜索关键词
        :param quick: 是否快速搜索
        :param pg: 页码
        :return: 搜索结果数据
        """
        try:
            print(f"正在搜索: {key}, 页码: {pg}")

            # 搜索接口使用 ac=detail 参数
            params = {
                "ac": "detail",
                "wd": key,
                "pg": pg
            }

            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"搜索数据失败，状态码: {response.status_code}")
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            data = json.loads(response.text)
            videos = []

            if "list" in data and data["list"]:
                for item in data["list"]:
                    # 过滤掉伦理片分类的视频
                    if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                        video = {
                            "vod_id": str(item["vod_id"]),
                            "vod_name": item["vod_name"],
                            "vod_pic": item.get("vod_pic", ""),  # 搜索接口通常有图片
                            "vod_remarks": item.get("vod_remarks", ""),
                            "vod_year": item.get("vod_year", ""),
                            "vod_area": item.get("vod_area", ""),
                            "vod_lang": item.get("vod_lang", ""),
                            "vod_actor": item.get("vod_actor", ""),
                            "vod_director": item.get("vod_director", ""),
                            "vod_content": self.removeHtmlTags(item.get("vod_content", "")),
                            "type_name": item.get("type_name", "")
                        }
                        videos.append(video)

            result = {
                "list": videos,
                "page": int(data.get("page", 1)),
                "pagecount": int(data.get("pagecount", 1)),
                "limit": int(data.get("limit", 20)),
                "total": int(data.get("total", 0))
            }
            print(f"搜索完成: 找到 {len(videos)} 个结果")
            return result
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        """
        获取播放内容
        :param flag: 播放标识
        :param id: 内容ID
        :param vipFlags: VIP标识列表
        :return: 包含播放URL和播放信息的字典
        """
        return {'url': id, 'header': {"User-Agent": self.USER_AGENT}, 'parse': 0, 'jx': 0}

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
        销毁爬虫实例，释放资源
        """
        print("非凡资源站爬虫已销毁")

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

    def fetch(self, url, params=None, cookies=None, headers=None, timeout=10, verify=True, stream=False, allow_redirects=True):
        """
        发送GET请求获取数据
        :param url: 请求URL
        :param params: 请求参数
        :param cookies: 请求Cookie
        :param headers: 请求头
        :param timeout: 超时时间
        :param verify: 是否验证SSL证书
        :param stream: 是否使用流式请求
        :param allow_redirects: 是否允许重定向
        :return: 响应对象
        """
        try:
            rsp = requests.get(url, params=params, cookies=cookies, headers=headers,
                               timeout=timeout, verify=verify, stream=stream, allow_redirects=allow_redirects)
            rsp.encoding = 'utf-8'
            return rsp
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return None

    def removeHtmlTags(self, src):
        """
        移除HTML标签
        :param src: 包含HTML标签的字符串
        :return: 移除HTML标签后的字符串
        """
        if not src:
            return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', src).strip()
