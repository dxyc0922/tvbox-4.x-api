# 非凡资源站实现
import sys
sys.path.append('..')
import json
import time
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    """
    非凡资源站爬虫实现
    API接口: http://api.ffzyapi.com/api.php/provide/vod/
    支持首页、分类、搜索、详情和播放功能
    """

    def __init__(self):
        super().__init__()
        # 常量定义
        self.API_URL = "http://api.ffzyapi.com/api.php/provide/vod/"
        self.EXCLUDE_CATEGORIES = {34}  # 伦理片分类ID
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        self.DEFAULT_HEADERS = {
            "User-Agent": self.USER_AGENT
        }
        self.YEAR_OPTIONS = None  # 延迟到实际需要时再生成
        self.CATEGORY_CACHE = None  # 分类缓存
        self.SPIDER_NAME = "非凡资源站"  # 爬虫名称常量

    def _generate_year_options(self):
        """生成年份筛选选项"""
        current_year = int(time.strftime("%Y"))
        year_range = range(current_year, 2000 - 1, -1)  # 从当前年份到2000年
        year_options = [{"n": "全部", "v": ""}]
        for year in year_range:
            year_options.append({"n": str(year), "v": str(year)})
        return year_options

    def _request_data(self, params, timeout=10, retries=3):
        """统一的数据请求方法，增加超时控制和重试机制"""
        import time  # 在方法开始时导入一次time模块
        for attempt in range(retries):
            try:
                response = self.fetch(self.API_URL, params=params, headers=self.DEFAULT_HEADERS, timeout=timeout)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    # 检查返回的数据是否为有效格式
                    if data is not None:
                        # 检查API返回的code字段，通常1表示成功
                        if "code" in data and data["code"] in (0, 1):  # 有些API 0表示成功，有些1表示成功
                            return data
                        elif "list" in data:  # 即使没有code字段，只要有list也可以认为是有效数据
                            return data
                        else:
                            self.log(f"API返回错误码: {data.get('code', 'N/A')}, params: {params}")
                    else:
                        self.log(f"请求返回数据无效: {params}")
                else:
                    self.log(f"请求失败，状态码: {response.status_code}, params: {params}")
            except json.JSONDecodeError:
                self.log(f"响应不是有效的JSON格式: {params}")
            except Exception as e:
                self.log(f"请求异常: {str(e)}, params: {params}")
            
            # 如果不是最后一次尝试，等待一段时间再重试
            if attempt < retries - 1:
                time.sleep(0.5)  # 等待0.5秒再重试
        
        return None

    def _build_video_object(self, item):
        """构建视频对象的公共方法"""
        return {
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
            "type_name": item.get("type_name", "")
        }

    def getName(self):
        """
        获取爬虫名称
        :return: 爬虫名称
        """
        return self.SPIDER_NAME

    def init(self, extend=""):
        """
        初始化爬虫
        :param extend: 扩展参数
        """
        self.log(f"非凡资源站爬虫初始化完成，扩展参数: {extend}")

    def _fetch_categories(self):
        """统一获取分类数据的方法，带缓存机制"""
        if self.CATEGORY_CACHE:
            return self.CATEGORY_CACHE

        params = {"ac": "list", "pg": "1"}
        data = self._request_data(params)
        if not data or "class" not in data:
            return [], {}

        all_categories = data["class"]
        primary_categories = []  # 一级分类
        sub_categories_map = {}  # 子分类映射

        for cat in all_categories:
            type_id = cat.get("type_id")
            type_pid = cat.get("type_pid", 0)

            # 过滤伦理片
            if type_id in self.EXCLUDE_CATEGORIES:
                continue

            # 收集一级分类
            if type_pid == 0:
                primary_categories.append({
                    "type_id": str(type_id),
                    "type_name": cat["type_name"]
                })
            # 收集子分类
            elif type_pid in (1, 2, 3, 4):
                pid_str = str(type_pid)
                if pid_str not in sub_categories_map:
                    sub_categories_map[pid_str] = []
                sub_categories_map[pid_str].append({"n": cat["type_name"], "v": str(type_id)})

        # 缓存结果
        self.CATEGORY_CACHE = (primary_categories, sub_categories_map)
        return primary_categories, sub_categories_map

    def homeContent(self, filter):
        """
        获取首页内容 - 实际是获取分类信息
        :param filter: 过滤条件
        :return: 分类信息和筛选条件
        """
        try:
            primary_categories, sub_categories_map = self._fetch_categories()
            
            # 仅在需要时定义筛选条件
            filters = {}
            if filter:
                filters = self._build_filter_options(sub_categories_map)

            result = {
                "class": primary_categories,
                "filters": filters  # 只有当filter为True时才返回筛选条件
            }
            self.log(f"分类信息获取成功: {len(primary_categories)} 个分类")
            return result
        except Exception as e:
            self.log(f"获取分类信息失败: {str(e)}")
            return {"class": [], "filters": {}}

    def _build_filter_options(self, sub_categories):
        """
        构建筛选选项
        :param sub_categories: 二级分类数据
        :return: 筛选选项
        """
        # 确保年份选项已生成
        if self.YEAR_OPTIONS is None:
            self.YEAR_OPTIONS = self._generate_year_options()
            
        filters = {}

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
                {"key": "year", "name": "年份", "value": self.YEAR_OPTIONS}
            ]

        # 为连续剧、综艺和动漫单独构建筛选项
        for cat_id in ["2", "3", "4"]:
            if cat_id in sub_categories:
                filters[cat_id] = [
                    {"key": "class", "name": "类型", "value": [
                        {"n": "全部", "v": ""},
                        *sub_categories[cat_id]  # 使用各自分类的二级分类
                    ]},
                    {"key": "year", "name": "年份", "value": self.YEAR_OPTIONS}
                ]

        return filters

    def homeVideoContent(self):
        """
        获取首页视频内容 - 最新更新的视频列表
        :return: 首页视频内容数据
        """
        try:
            # 获取首页最新内容 - 使用ac=detail参数以获取完整信息
            params = {
                "ac": "detail",  # 使用detail参数获取完整信息，包括图片
                "pg": "1"
            }
            data = self._request_data(params)
            if not data:
                return {"list": []}

            # 检查API是否返回错误或空数据
            if "list" not in data or not data["list"]:
                self.log("首页无数据返回")
                return {"list": []}

            # 使用列表推导式构建视频列表
            videos = [
                self._build_video_object(item)
                for item in data.get("list", [])
                if item.get("type_id") not in self.EXCLUDE_CATEGORIES
            ]

            result = {"list": videos}
            self.log(f"首页视频内容获取成功: {len(videos)} 个视频")
            return result
        except Exception as e:
            self.log(f"获取首页视频内容失败: {str(e)}")
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
            self.log(f"正在获取分类 {tid} 第 {pg} 页内容...")

            # 构建请求参数
            params = {"ac": "detail", "t": tid, "pg": pg}
            if extend:
                for key, value in extend.items():
                    if key != "class" and value:
                        params[key] = value

            data = self._request_data(params)
            if not data:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            # 检查API是否返回错误或空数据
            if "list" not in data or not data["list"]:
                self.log(f"分类 {tid} 第 {pg} 页无数据返回")
                return {
                    "list": [],
                    "page": int(data.get("page", pg)),
                    "pagecount": int(data.get("pagecount", 0)),
                    "limit": int(data.get("limit", 20)),
                    "total": int(data.get("total", 0))
                }

            # 构建视频列表
            videos = [
                self._build_video_object(item)
                for item in data.get("list", [])
                if item.get("type_id") not in self.EXCLUDE_CATEGORIES
            ]

            result = {
                "list": videos,
                "page": int(data.get("page", pg)),
                "pagecount": int(data.get("pagecount", 1)),
                "limit": int(data.get("limit", 20)),
                "total": int(data.get("total", 0))
            }
            self.log(f"分类内容获取成功: {len(videos)} 个视频, 总计 {result['total']} 个")
            return result
        except Exception as e:
            self.log(f"获取分类内容失败: {str(e)}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}


    def _filter_play_sources(self, play_from, play_url):
        """
        过滤播放源，移除包含'feifan'的播放源
        :param play_from: 播放源字符串
        :param play_url: 播放地址字符串
        :return: 过滤后的(播放源, 播放地址)元组
        """
        if not play_from or not play_url:
            return play_from, play_url

        # 分割播放源和播放地址
        from_list = play_from.split("$$$")
        url_list = play_url.split("$$$")

        # 过滤掉feifan播放源并使用列表推导式提高效率
        filtered_pairs = [
            (source, url_list[i]) 
            for i, source in enumerate(from_list) 
            if i < len(url_list) and 'feifan' not in source.lower()
        ]

        if not filtered_pairs:
            return play_from, play_url  # 如果过滤后为空，返回原始值

        filtered_from_list, filtered_url_list = zip(*filtered_pairs) if filtered_pairs else ([], [])
        return "$$$".join(filtered_from_list), "$$$".join(filtered_url_list)

    def detailContent(self, ids):
        """
        获取详情内容
        :param ids: 内容ID列表
        :return: 详情内容数据
        """
        try:
            self.log(f"正在获取详情内容，ID: {ids}")
            if not ids:
                return {"list": []}

            # 获取详情信息 - 支持批量获取
            data = self._request_data({"ac": "detail", "ids": ','.join(ids)})
            if not data or "list" not in data:
                return {"list": []}

            # 检查API是否返回错误或空数据
            if not data["list"]:
                self.log(f"ID {ids} 的详情内容为空")
                return {"list": []}

            details = []
            for item in data["list"]:
                # 跳过伦理片分类的视频
                if item.get("type_id") in self.EXCLUDE_CATEGORIES:
                    continue

                # 构建基础视频对象并应用播放源过滤
                detail = self._build_video_object(item)
                play_from, play_url = item.get("vod_play_from", ""), item.get("vod_play_url", "")
                filtered_from, filtered_url = self._filter_play_sources(play_from, play_url)

                # 更新详情页特有字段
                detail.update({
                    "vod_play_from": filtered_from,
                    "vod_play_url": filtered_url
                })
                details.append(detail)

            result = {"list": details}
            self.log(f"详情内容获取成功: {len(details)} 个详情")
            return result
        except Exception as e:
            self.log(f"获取详情内容失败: {str(e)}")
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
            self.log(f"正在搜索: {key}, 页码: {pg}")

            # 搜索接口使用 ac=detail 参数
            data = self._request_data({"ac": "detail", "wd": key, "pg": pg})
            if not data:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            # 检查API是否返回错误或空数据
            if "list" not in data or not data["list"]:
                self.log(f"搜索关键词 '{key}' 无结果")
                return {
                    "list": [],
                    "page": int(data.get("page", pg)),
                    "pagecount": int(data.get("pagecount", 0)),
                    "limit": int(data.get("limit", 20)),
                    "total": int(data.get("total", 0))
                }

            # 使用列表推导式构建视频列表
            videos = [
                self._build_video_object(item)
                for item in data.get("list", [])
                if item.get("type_id") not in self.EXCLUDE_CATEGORIES
            ]

            result = {
                "list": videos,
                "page": int(data.get("page", pg)),
                "pagecount": int(data.get("pagecount", 1)),
                "limit": int(data.get("limit", 20)),
                "total": int(data.get("total", 0))
            }
            self.log(f"搜索完成: 找到 {len(videos)} 个结果")
            return result
        except Exception as e:
            self.log(f"搜索失败: {str(e)}")
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        """
        获取播放内容
        :param flag: 播放标识
        :param id: 内容ID
        :param vipFlags: VIP标识列表
        :return: 包含播放URL和播放信息的字典
        """
        return {'url': id, 'header': self.DEFAULT_HEADERS, 'parse': 0, 'jx': 0}

    def destroy(self):
        """
        销毁爬虫实例，释放资源
        """
        self.log("非凡资源站爬虫已销毁")