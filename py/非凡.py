import re
import os
import json
import time
import requests
# from lxml import etree
# from com.github.catvod import Proxy  # type: ignore
# from com.chaquo.python import Python  # type: ignore
# from abc import abstractmethod, ABCMeta
# from importlib.machinery import SourceFileLoader
from concurrent.futures import ThreadPoolExecutor, as_completed


class Spider:
    """
    非凡资源站爬虫实现
    API接口: https://ffzy.tv/api.php/provide/vod/
    支持首页、分类、搜索、详情和播放功能
    """

    # 常量定义
    API_URL = "https://ffzy.tv/api.php/provide/vod/"
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
                        # 过滤掉feifan播放源
                        vod_play_from = self._filter_play_from(
                            item.get("vod_play_from", ""))
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
                            "vod_play_from": vod_play_from,  # 使用过滤后的播放源
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

    def _filter_play_from(self, play_from):
        """
        过滤播放源，移除包含feifan的播放源
        :param play_from: 原始播放源字符串
        :return: 过滤后的播放源字符串
        """
        if not play_from:
            return play_from

        # 分割播放源
        sources = play_from.split("$$$")
        # 过滤掉包含feifan的播放源（不区分大小写）
        filtered_sources = [
            source for source in sources if 'feifan' not in source.lower()]
        # 重新组合，如果过滤后为空则返回原值
        return "$$$".join(filtered_sources) if filtered_sources else play_from

    def playerContent(self, flag, id, vipFlags):
        """
        获取播放内容
        :param flag: 播放标识
        :param id: 内容ID
        :param vipFlags: VIP标识列表
        :return: 播放内容数据
        """
        try:
            print(f"正在获取播放内容，标识: {flag}, ID: {id}")

            # 获取视频详情以获取播放地址
            params = {
                "ac": "detail",
                "ids": id
            }

            response = self.fetch(self.API_URL, params=params, headers={
                                  "User-Agent": self.USER_AGENT, "Referer": self.SITE_URL})
            if response.status_code != 200:
                print(f"获取播放详情失败，状态码: {response.status_code}")
                return {"parse": 0, "playUrl": "", "url": "", "header": {}}

            data = json.loads(response.text)

            if "list" in data and data["list"]:
                item = data["list"][0]
                # 过滤掉伦理片分类的视频
                if item.get("type_id") not in self.EXCLUDE_CATEGORIES:
                    play_from = item.get("vod_play_from", "")  # 直接使用已经过滤的播放源
                    play_url = item.get("vod_play_url", "")

                    # 解析播放源
                    from_list = play_from.split("$$$")
                    url_list = play_url.split("$$$")

                    # 找到对应的播放源
                    play_url_str = ""
                    for i, source in enumerate(from_list):
                        if source == flag and i < len(url_list):
                            play_url_str = url_list[i]
                            break

                    # 解析播放地址
                    if play_url_str:
                        # 解析播放地址列表，格式为 "第1集$地址#第2集$地址"
                        episodes = play_url_str.split("#")
                        # 获取第一个播放地址作为默认播放地址
                        for episode in episodes:
                            parts = episode.split("$")
                            if len(parts) >= 2:
                                video_url = parts[1]
                                if video_url.startswith("http"):
                                    result = {
                                        "parse": 0,  # 0表示直接播放
                                        "playUrl": "",
                                        "url": video_url,
                                        "header": {
                                            "User-Agent": self.USER_AGENT,
                                            "Referer": self.SITE_URL
                                        }
                                    }
                                    print(f"播放内容获取成功: {video_url}")
                                    return result

            return {"parse": 0, "playUrl": "", "url": "", "header": {}}
        except Exception as e:
            print(f"获取播放内容失败: {str(e)}")
            return {"parse": 0, "playUrl": "", "url": "", "header": {}}

    def localProxy(self, param):
        """
        本地代理方法
        :param param: 代理参数
        :return: 代理结果
        """
        pass

    def destroy(self):
        """
        销毁爬虫实例，释放资源
        """
        print("非凡资源站爬虫已销毁")

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


if __name__ == "__main__":
    spider = Spider()
    spider.init()
    print(spider.detailContent(['51818']))
