# coding=utf-8
"""
通用爬虫资源站实现
该模板适用于实现基于通用API接口的资源站爬虫
"""
from base.spider import Spider as BaseSpider
import time
import json
import sys
sys.path.append('..')


class Spider(BaseSpider):
    """
    通用爬虫资源站实现
    该类提供了一个通用的爬虫模板，适用于具有标准API接口的视频资源站
    """

    def __init__(self):
        super().__init__()
        # 爬虫名称:非凡资源
        self.SPIDER_NAME = "优质资源"
        # API接口地址:http://api.ffzyapi.com/api.php/provide/vod/
        self.API_URL = "https://api.yzzy-api.com/inc/apijson.php"
        # 需要排除的分类ID集合:{34}
        self.EXCLUDE_CATEGORIES = {19, 61, 92, 93}
        # 需要过滤的播放源关键词列表:feifan
        self.FILTER_KEYWORDS = []
        # 默认请求头:"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        self.DEFAULT_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
        # 年份选项列表，用于筛选:初始化
        self.YEAR_OPTIONS = None
        # 分类缓存，避免重复请求:初始化
        self.CATEGORY_CACHE = None
        # 一级分类关键字，用于识别主分类
        self.PRIMARY_CATEGORIES_KEYWORDS = [
            '影视解说', '电影', '电视剧', '连续剧', '综艺', '动漫', '纪录片', '演唱会', '音乐', '体育赛事', '体育', '爽文短剧', '短剧大全']
        # 二级分类映射，定义了主分类下的子分类关键字
        self.SECONDARY_CATEGORIES_MAP = {
            '电影': ['动作片', '喜剧片', '爱情片', '科幻片', '恐怖片', '剧情片', '战争片', '动画片', '4K电影', '邵氏电影', 'Netflix电影'],
            '电视剧': ['国产剧', '台剧', '台湾剧', '韩剧', '韩国剧', '欧美剧', '港剧', '香港剧', '泰剧', '泰国剧', '日剧', '日本剧', '海外剧', 'Netflix自制剧'],
            '连续剧': ['国产剧', '台剧', '台湾剧', '韩剧', '韩国剧', '欧美剧', '港剧', '香港剧', '泰剧', '泰国剧', '日剧', '日本剧', '海外剧', 'Netflix自制剧'],
            '综艺': ['大陆综艺', '港台综艺', '日韩综艺', '欧美综艺'],
            '动漫': ['国产动漫', '日韩动漫', '欧美动漫', '港台动漫', '海外动漫'],
            '体育赛事': ['篮球', '足球', '斯诺克'],
            '爽文短剧': ['有声动漫', '女频恋爱', '反转爽剧', '古装仙侠', '年代穿越', '脑洞悬疑', '现代都市']
        }

    def _generate_year_options(self):
        """
        生成年份筛选选项
        从当前年份到2001年，逐年递减生成筛选选项

        Returns:
            list: 包含年份选项的列表，格式为[{"n": "显示名称", "v": "实际值"}]
        """
        current_year = int(time.strftime("%Y"))
        year_range = range(current_year, 2000 - 1, -1)
        year_options = [{"n": "全部", "v": ""}]
        for year in year_range:
            year_options.append({"n": str(year), "v": str(year)})
        return year_options

    def _request_data(self, params, timeout=10, retries=3):
        """
        发送API请求并处理响应数据

        Args:
            params (dict): 请求参数
            timeout (int): 请求超时时间（秒）
            retries (int): 重试次数

        Returns:
            dict or None: 成功时返回解析后的数据，失败时返回None
        """
        import time
        for attempt in range(retries):
            try:
                response = self.fetch(
                    self.API_URL, params=params, headers=self.DEFAULT_HEADERS, timeout=timeout)
                if response.status_code == 200:
                    data = json.loads(response.text)
                    if data is not None:
                        if "code" in data and data["code"] in (0, 1):
                            return data
                        elif "list" in data:
                            return data
                else:
                    pass
            except json.JSONDecodeError:
                pass
            except Exception as e:
                pass

            if attempt < retries - 1:
                time.sleep(0.5)

        return None

    def _build_video_object(self, item):
        """
        构建视频对象，处理视频信息

        Args:
            item (dict): 原始视频信息字典

        Returns:
            dict: 标准格式的视频信息字典
        """
        vod_pic = item.get("vod_pic", "")
        if vod_pic and not vod_pic.startswith(('http://', 'https://')):
            vod_pic = self.IMAGE_BASE_URL + "/" + vod_pic.lstrip('/')

        return {
            "vod_id": str(item["vod_id"]),
            "vod_name": item["vod_name"],
            "vod_pic": vod_pic,
            "vod_remarks": item.get("vod_remarks", ""),
            "vod_time": item.get("vod_time", ""),
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

        Returns:
            str: 爬虫名称
        """
        return self.SPIDER_NAME

    def init(self, extend=""):
        """
        初始化方法，需要在继承类中设置以下参数：
        - self.API_URL
        - self.IMAGE_BASE_URL
        - self.EXCLUDE_CATEGORIES
        - self.DEFAULT_HEADERS
        - self.SPIDER_NAME
        """
        pass

    def _categorize_without_pid(self, all_categories):
        """
        处理没有type_pid字段的分类数据，根据分类名称进行分类

        Args:
            all_categories (list): 原始分类数据列表

        Returns:
            tuple: (primary_categories, sub_categories_map)
                - primary_categories: 主分类列表
                - sub_categories_map: 子分类映射表，以主分类ID为键
        """
        primary_categories = []
        sub_categories_map = {}

        # 首先识别主分类
        for cat in all_categories:
            type_id = cat.get("type_id")
            type_name = cat.get("type_name", "")

            # 精准匹配主分类关键词
            is_primary = type_name in self.PRIMARY_CATEGORIES_KEYWORDS

            # 精准匹配二级分类映射中的键
            is_primary_by_map = type_name in self.SECONDARY_CATEGORIES_MAP.keys()

            if is_primary or is_primary_by_map:
                primary_categories.append({
                    "type_id": str(type_id),
                    "type_name": type_name
                })

        # 然后建立子分类映射
        for primary_cat in primary_categories:
            primary_name = primary_cat["type_name"]
            primary_id = primary_cat["type_id"]

            # 检查该主分类下是否有子分类映射
            if primary_name in self.SECONDARY_CATEGORIES_MAP:
                sub_keywords = self.SECONDARY_CATEGORIES_MAP[primary_name]

                # 查找该主分类下的子分类
                sub_categories = []
                for cat in all_categories:
                    type_id = cat.get("type_id")
                    type_name = cat.get("type_name", "")

                    # 精准匹配子分类关键字
                    if type_name in sub_keywords and str(type_id) != primary_id:
                        sub_categories.append({
                            "n": type_name,
                            "v": str(type_id)
                        })

                if sub_categories:
                    sub_categories_map[primary_id] = sub_categories

        return primary_categories, sub_categories_map

    def _fetch_categories(self):
        """
        获取分类信息，包括主分类和子分类，并缓存结果
        如果原始数据没有type_pid字段，则根据分类名称进行智能分类

        Returns:
            tuple: (primary_categories, sub_categories_map)
                - primary_categories: 主分类列表
                - sub_categories_map: 子分类映射表，以主分类ID为键
        """
        if self.CATEGORY_CACHE:
            return self.CATEGORY_CACHE

        params = {"ac": "list", "pg": "1"}
        data = self._request_data(params)
        if not data or "class" not in data:
            return [], {}

        all_categories = data["class"]

        # 检查是否有type_pid字段，如果没有则使用智能分类
        has_type_pid = any("type_pid" in cat for cat in all_categories)

        if has_type_pid:
            # 有type_pid字段的处理方式
            primary_categories = []
            sub_categories_map = {}

            for cat in all_categories:
                type_id = cat.get("type_id")
                type_pid = cat.get("type_pid", 0)

                if type_id in self.EXCLUDE_CATEGORIES:
                    continue

                if type_pid == 0:
                    primary_categories.append({
                        "type_id": str(type_id),
                        "type_name": cat["type_name"]
                    })
                else:
                    pid_str = str(type_pid)
                    if pid_str not in sub_categories_map:
                        sub_categories_map[pid_str] = []
                    sub_categories_map[pid_str].append(
                        {"n": cat["type_name"], "v": str(type_id)})

            self.CATEGORY_CACHE = (primary_categories, sub_categories_map)
            return primary_categories, sub_categories_map
        else:
            # 没有type_pid字段的处理方式，使用智能分类
            primary_categories, sub_categories_map = self._categorize_without_pid(
                all_categories)
            self.CATEGORY_CACHE = (primary_categories, sub_categories_map)
            return primary_categories, sub_categories_map

    def homeContent(self, filter):
        """
        获取首页内容，包括分类和筛选条件

        Args:
            filter (bool): 是否启用筛选条件

        Returns:
            dict: 包含分类和筛选条件的字典
        """
        try:
            primary_categories, sub_categories_map = self._fetch_categories()

            filters = {}
            if filter:
                filters = self._build_filter_options(sub_categories_map)

            result = {
                "class": primary_categories,
                "filters": filters
            }
            return result
        except Exception as e:
            return {"class": [], "filters": {}}

    def _build_filter_options(self, sub_categories):
        """
        构建筛选选项，为每个子分类生成筛选条件

        Args:
            sub_categories (dict): 子分类映射表

        Returns:
            dict: 筛选选项配置
        """
        if self.YEAR_OPTIONS is None:
            self.YEAR_OPTIONS = self._generate_year_options()

        filters = {}

        for cat_id, sub_cats in sub_categories.items():
            filter_options = [
                {"key": "type_id", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *sub_cats
                ]},
                {"key": "year", "name": "年份", "value": self.YEAR_OPTIONS}
            ]

            filters[cat_id] = filter_options

        return filters

    def homeVideoContent(self):
        """
        获取首页推荐视频内容

        Returns:
            dict: 包含推荐视频列表的字典
        """
        try:
            params = {
                "ac": "detail",
                "pg": "1"
            }
            data = self._request_data(params)
            if not data:
                return {"list": []}

            if "list" not in data or not data["list"]:
                return {"list": []}

            videos = [
                self._build_video_object(item)
                for item in data.get("list", [])
                if item.get("type_id") not in self.EXCLUDE_CATEGORIES
            ]

            result = {"list": videos}
            return result
        except Exception as e:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        """
        获取分类内容

        Args:
            tid (str): 分类ID
            pg (str): 页码
            filter (bool): 是否启用筛选
            extend (dict): 扩展参数

        Returns:
            dict: 包含分类视频列表和分页信息的字典
        """
        try:
            category_id = tid
            if extend and 'type_id' in extend and extend['type_id']:
                category_id = extend['type_id']

            params = {"ac": "detail", "t": category_id, "pg": pg}

            if extend:
                for key, value in extend.items():
                    if key != 't' and key != 'type_id' and value:
                        params[key] = value

            data = self._request_data(params)
            if not data:
                return self._get_subcategory_data(tid, pg, extend)

            if "list" not in data or not data["list"]:
                return self._get_subcategory_data(tid, pg, extend)

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
            return result
        except Exception as e:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def _get_subcategory_data(self, tid, pg, extend):
        """
        获取子分类数据，当主分类下有子分类时使用此方法

        Args:
            tid (str): 主分类ID
            pg (str): 页码
            extend (dict): 扩展参数

        Returns:
            dict: 包含子分类视频列表和分页信息的字典
        """
        try:
            _, sub_categories_map = self._fetch_categories()

            if tid not in sub_categories_map:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            sub_categories = sub_categories_map[tid]
            all_videos = []

            import concurrent.futures

            def fetch_subcategory_videos(sub_cat):
                """
                获取单个子分类的视频数据

                Args:
                    sub_cat (dict): 子分类信息

                Returns:
                    list: 视频列表
                """
                sub_tid = sub_cat['v']
                params = {"ac": "detail", "t": sub_tid, "pg": pg}
                if extend:
                    for key, value in extend.items():
                        if key != 't' and key != 'type_id' and value:
                            params[key] = value

                sub_data = self._request_data(params)
                if sub_data and "list" in sub_data and sub_data["list"]:
                    return [
                        self._build_video_object(item)
                        for item in sub_data.get("list", [])
                        if item.get("type_id") not in self.EXCLUDE_CATEGORIES
                    ]
                return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(
                    fetch_subcategory_videos, sub_cat) for sub_cat in sub_categories]
                for future in concurrent.futures.as_completed(futures):
                    sub_videos = future.result()
                    all_videos.extend(sub_videos)

            all_videos.sort(key=lambda x: x.get('vod_time', ''), reverse=True)

            total = len(all_videos)
            limit = 20
            pagecount = (total + limit - 1) // limit

            start_idx = (int(pg) - 1) * limit
            end_idx = start_idx + limit
            paged_videos = all_videos[start_idx:end_idx]

            result = {
                "list": paged_videos,
                "page": int(pg),
                "pagecount": pagecount,
                "limit": limit,
                "total": total
            }

            return result
        except Exception as e:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def detailContent(self, ids):
        """
        获取视频详情

        Args:
            ids (list): 视频ID列表

        Returns:
            dict: 包含视频详细信息的字典
        """
        try:
            if not ids:
                return {"list": []}

            data = self._request_data({"ac": "detail", "ids": ','.join(ids)})
            if not data or "list" not in data:
                return {"list": []}

            if not data["list"]:
                return {"list": []}

            details = []
            for item in data["list"]:
                if item.get("type_id") in self.EXCLUDE_CATEGORIES:
                    continue

                detail = self._build_video_object(item)

                play_from = item.get("vod_play_from", "")
                play_url = item.get("vod_play_url", "")

                filtered_play_from, filtered_play_url = self._filter_play_sources(
                    play_from, play_url)

                detail.update({
                    "vod_play_from": filtered_play_from,
                    "vod_play_url": filtered_play_url
                })
                details.append(detail)

            result = {"list": details}
            return result
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        """
        搜索视频内容

        Args:
            key (str): 搜索关键词
            quick (bool): 是否快速搜索
            pg (str): 页码，默认为"1"

        Returns:
            dict: 包含搜索结果和分页信息的字典
        """
        try:
            params = {"ac": "detail", "wd": key, "pg": pg}
            data = self._request_data(params)
            if not data:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            if "list" not in data or not data["list"]:
                return {
                    "list": [],
                    "page": int(data.get("page", pg)),
                    "pagecount": int(data.get("pagecount", 0)),
                    "limit": int(data.get("limit", 20)),
                    "total": int(data.get("total", 0))
                }

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
            return result
        except Exception as e:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def playerContent(self, flag, id, vipFlags):
        """
        获取播放地址

        Args:
            flag (str): 播放来源标识
            id (str): 视频ID
            vipFlags (list): VIP标识列表

        Returns:
            dict: 包含播放地址和相关参数的字典
        """
        return {'url': id, 'header': self.DEFAULT_HEADERS, 'parse': 0, 'jx': 0}

    def destroy(self):
        """
        销毁爬虫实例，释放资源
        """
        pass

    def _filter_play_sources(self, play_from, play_url):
        """
        过滤播放源，移除不需要的播放源

        Args:
            play_from (str): 播放源字符串，使用"$$$"分隔
            play_url (str): 播放地址字符串，使用"$$$"分隔

        Returns:
            tuple: (filtered_play_from, filtered_play_url) 过滤后的播放源和播放地址
        """
        if not play_from or not play_url:
            return play_from, play_url

        from_list = play_from.split("$$$")
        url_list = play_url.split("$$$")

        filtered_pairs = [
            (source, url_list[i])
            for i, source in enumerate(from_list)
            if i < len(url_list) and not any(keyword in source.lower() for keyword in self.FILTER_KEYWORDS)
        ]

        if not filtered_pairs:
            return play_from, play_url

        filtered_from_list, filtered_url_list = zip(
            *filtered_pairs) if filtered_pairs else ([], [])
        return "$$$".join(filtered_from_list), "$$$".join(filtered_url_list)
