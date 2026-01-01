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
        self.SPIDER_NAME = "最大资源"
        # API接口地址:http://api.ffzyapi.com/api.php/provide/vod/
        self.API_URL = "https://api.zuidapi.com/api.php/provide/vod/"
        # 图片基础URL，用于处理相对路径的图片链接:https://img.picbf.com
        self.IMAGE_BASE_URL = ""
        # 需要排除的分类ID集合:{34}
        self.EXCLUDE_CATEGORIES = {51, 55, 56, 57, 58, 59, 60, 61, 73, 74}
        # 需要过滤的播放源关键词列表:feifan
        self.FILTER_KEYWORDS = []
        # 默认请求头:"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        self.DEFAULT_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 4.4; TV Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Safari/537.36 TV Safari/4.0"}
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
                if cat.get("type_id") in self.EXCLUDE_CATEGORIES:
                    continue

                type_id = cat.get("type_id")
                type_pid = cat.get("type_pid", 0)

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
                if str(item.get("type_id")) not in {str(cat_id) for cat_id in self.EXCLUDE_CATEGORIES}
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
                if str(item.get("type_id")) not in {str(cat_id) for cat_id in self.EXCLUDE_CATEGORIES}
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
                        if str(item.get("type_id")) not in {str(cat_id) for cat_id in self.EXCLUDE_CATEGORIES}
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
                if str(item.get("type_id")) not in {str(cat_id) for cat_id in self.EXCLUDE_CATEGORIES}
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
        # 检查是否是m3u8链接，如果是则过滤广告
        if 'm3u8' in id or 'm3u' in id:
            filtered_url = self._filter_m3u8_ads(id)
            return {'url': filtered_url, 'header': self.DEFAULT_HEADERS, 'parse': 0, 'jx': 0}

        # 检查是否是广告链接或需要过滤的链接
        if self._is_ad_link(id):
            # 尝试通过API获取纯净的播放链接
            clean_url = self._get_clean_url(id)
            if clean_url:
                if 'm3u8' in clean_url or 'm3u' in clean_url:
                    clean_url = self._filter_m3u8_ads(clean_url)
                return {'url': clean_url, 'header': self.DEFAULT_HEADERS, 'parse': 1, 'jx': 0}

        # 检查是否需要解析
        if self._need_parse(id):
            return {'url': id, 'header': self.DEFAULT_HEADERS, 'parse': 1, 'jx': 0}
        else:
            return {'url': id, 'header': self.DEFAULT_HEADERS, 'parse': 0, 'jx': 0}

    def _filter_m3u8_ads(self, m3u8_url):
        """
        通过分析域名分布来过滤m3u8文件中的广告片段

        Args:
            m3u8_url (str): 原始m3u8播放列表URL

        Returns:
            str: 过滤广告后的m3u8 URL 或原始URL
        """
        try:
            import requests
            import tempfile
            import os
            from urllib.parse import urljoin, urlparse
            from collections import Counter

            # 获取m3u8内容
            response = requests.get(m3u8_url, headers=self.DEFAULT_HEADERS)
            if response.status_code != 200:
                return m3u8_url

            m3u8_content = response.text
            lines = m3u8_content.split('\n')

            # 提取所有媒体URL（非注释行）
            media_urls = []
            extinf_lines = []  # 保存EXTINF行及其对应的URL索引

            i = 0
            while i < len(lines):
                line = lines[i]
                if line.startswith('#EXTINF'):
                    # 记录EXTINF行，下一行是URL
                    # (EXTINF行, 对应URL在media_urls中的索引)
                    extinf_lines.append((line, len(media_urls)))
                elif line.strip() and not line.startswith('#'):
                    # 这是一个媒体URL
                    if line.startswith('http'):
                        url = line
                    else:
                        # 相对URL转换为绝对URL
                        url = urljoin(m3u8_url, line)
                    media_urls.append(url)
                i += 1

            # 分析域名分布，找出主要域名（正常视频片段）
            domains = []
            for url in media_urls:
                try:
                    parsed = urlparse(url)
                    domain = f"{parsed.scheme}://{parsed.netloc}"  # 包含协议的域名
                    domains.append(domain)
                except:
                    continue

            if not domains:
                return m3u8_url  # 如果无法解析任何域名，返回原URL

            # 统计域名出现次数
            domain_counts = Counter(domains)

            # 找出出现次数最多的域名（认为是正常视频域名）
            if not domain_counts:
                return m3u8_url

            # 获取出现次数最多的域名
            main_domain, _ = domain_counts.most_common(1)[0]

            # 过滤：只保留与主域名相同的URL
            filtered_lines = []
            url_index = 0

            for line in lines:
                if line.startswith('#EXTINF'):
                    # 保留EXTINF行
                    filtered_lines.append(line)
                elif line.strip() and not line.startswith('#'):
                    # 这是一个URL行，需要判断是否保留
                    if url_index < len(media_urls):
                        current_url = media_urls[url_index]
                        try:
                            parsed = urlparse(current_url)
                            current_domain = f"{parsed.scheme}://{parsed.netloc}"

                            # 如果域名与主域名相同，则保留
                            if current_domain == main_domain:
                                filtered_lines.append(line)  # 保留原始行（相对或绝对路径）
                        except:
                            # 解析失败，不保留
                            pass
                        url_index += 1
                else:
                    # 保留所有注释行（除了可能的广告相关注释）
                    filtered_lines.append(line)

            # 如果过滤后内容过少，返回原URL
            original_media_count = len([l for l in lines if l.strip(
            ) and not l.startswith('#') and not l.startswith('#EXT')])
            filtered_media_count = len([l for l in filtered_lines if l.strip(
            ) and not l.startswith('#') and not l.startswith('#EXT')])

            if original_media_count > 0 and filtered_media_count / original_media_count < 0.5:
                return m3u8_url

            # 创建临时m3u8文件
            filtered_content = '\n'.join(filtered_lines)

            # 将过滤后的内容保存到临时文件
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.m3u8') as f:
                f.write(filtered_content)
                temp_path = f.name

            # 返回临时文件的file URL
            return f"file://{temp_path}"

        except Exception as e:
            # 出错时返回原URL
            return m3u8_url

    def _is_ad_m3u8_line(self, line, base_url):
        """
        检查m3u8文件中的行是否是广告片段（使用域名分析方法）

        Args:
            line (str): m3u8文件中的一行
            base_url (str): 基础URL，用于构建绝对路径

        Returns:
            bool: 如果是广告返回True，否则返回False
        """
        if not line or line.startswith('#'):
            return False

        # 绝对URL
        if line.startswith('http'):
            url = line
        else:
            # 相对URL，转换为绝对URL
            from urllib.parse import urljoin
            url = urljoin(base_url, line)

        # 这个方法在新算法中不再使用，因为我们使用域名分布分析
        # 保留是为了兼容其他可能的调用
        return False

    def _is_ad_link(self, url):
        """
        检查是否是广告链接

        Args:
            url (str): 播放地址

        Returns:
            bool: 如果是广告链接返回True，否则返回False
        """
        ad_indicators = [
            'ads.', 'ad.', 'advertisement', 'adserver',
            'analytics.', '.gif', '.html', 'popup', 'track'
        ]

        url_lower = url.lower()
        return any(indicator in url_lower for indicator in ad_indicators)

    def _need_parse(self, url):
        """
        检查URL是否需要解析（某些URL可能需要额外解析才能去除广告）

        Args:
            url (str): 播放地址

        Returns:
            bool: 如果需要解析返回True，否则返回False
        """
        parse_indicators = [
            'v.qq.com', 'youku.com', 'iqiyi.com', 'mgtv.com',
            'bilibili.com', 'touko', 'player.m3u8'
        ]

        url_lower = url.lower()
        return any(indicator in url_lower for indicator in parse_indicators)

    def _get_clean_url(self, original_url):
        """
        通过API或其他方式获取纯净的播放链接

        Args:
            original_url (str): 原始播放地址

        Returns:
            str: 纯净的播放链接，如果获取失败返回None
        """
        try:
            # 尝试通过API获取纯净播放链接
            # 这里可以根据具体资源站API进行定制
            import re

            # 提取真实视频链接（根据常见格式）
            # 通常广告会在视频链接前添加跳转或包装
            m3u8_pattern = r'(https?://[^\s]*\.(m3u8|mp4|flv|avi)[^\s]*)'
            match = re.search(m3u8_pattern, original_url)
            if match:
                clean_url = match.group(1)
                # 验证链接是否有效
                if self._validate_url(clean_url):
                    return clean_url

            # 如果正则提取失败，尝试移除常见的广告参数
            clean_url = self._remove_ad_params(original_url)
            if clean_url and clean_url != original_url and self._validate_url(clean_url):
                return clean_url

            return None
        except Exception as e:
            return None

    def _remove_ad_params(self, url):
        """
        移除URL中的广告参数

        Args:
            url (str): 原始URL

        Returns:
            str: 移除广告参数后的URL
        """
        import re
        from urllib.parse import urlparse, parse_qs, urlunparse

        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query, keep_blank_values=True)

            # 定义要移除的广告相关参数
            ad_params = {
                'ad', 'ads', 'advertisement', 'track', 'from_ad', 'utm_source',
                'utm_medium', 'utm_campaign', 'utm_term', 'ref', 'referer',
                'popup', 'preplay', 'splash'
            }

            # 过滤掉广告参数
            filtered_params = {k: v for k,
                               v in query_params.items() if k not in ad_params}

            # 重新构建查询字符串
            from urllib.parse import urlencode
            new_query = urlencode(filtered_params, doseq=True)

            # 重新构建URL
            new_parsed = parsed_url._replace(query=new_query)
            return urlunparse(new_parsed)
        except Exception as e:
            return url  # 如果处理失败，返回原URL

    def _validate_url(self, url):
        """
        验证URL是否有效（简单检查）

        Args:
            url (str): 要验证的URL

        Returns:
            bool: 如果URL有效返回True，否则返回False
        """
        import re
        # 简单的URL格式验证
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            # domain...
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return url_pattern.match(url) is not None

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
