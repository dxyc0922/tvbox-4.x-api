# 通用爬虫资源站实现
from base.spider import Spider as BaseSpider
import time
import json
import sys
sys.path.append('..')


class Spider(BaseSpider):
    """
    通用爬虫资源站实现
    通过初始化参数配置不同资源站的API信息
    """

    def __init__(self):
        super().__init__()
        # 以下参数将在init方法中设置
        self.API_URL = "http://api.ffzyapi.com/api.php/provide/vod/"  # API地址
        self.HAS_IMAGE_PROCESSING = False  # 是否有图床地址
        self.IMAGE_BASE_URL = "" # 图床地址
        self.EXCLUDE_CATEGORIES = {34}  # 排除的分类ID
        self.DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}  # 请求头
        self.YEAR_OPTIONS = None  # 年份选项
        self.CATEGORY_CACHE = None  # 分类缓存
        self.SPIDER_NAME = "非凡资源站"  # 爬虫名称

    def _generate_year_options(self):
        current_year = int(time.strftime("%Y"))
        year_range = range(current_year, 2000 - 1, -1)
        year_options = [{"n": "全部", "v": ""}]
        for year in year_range:
            year_options.append({"n": str(year), "v": str(year)})
        return year_options

    def _request_data(self, params, timeout=10, retries=3):
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
        # 如果需要处理图片路径
        vod_pic = item.get("vod_pic", "")
        if self.HAS_IMAGE_PROCESSING and vod_pic and not vod_pic.startswith(('http://', 'https://')):
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
        return self.SPIDER_NAME

    def init(self, extend=""):
        """
        初始化方法，需要在继承类中设置以下参数：
        - self.API_URL
        - self.IMAGE_BASE_URL (如果需要图片处理)
        - self.EXCLUDE_CATEGORIES
        - self.DEFAULT_HEADERS
        - self.SPIDER_NAME
        - self.HAS_IMAGE_PROCESSING
        """
        pass

    def _fetch_categories(self):
        if self.CATEGORY_CACHE:
            return self.CATEGORY_CACHE

        params = {"ac": "list", "pg": "1"}
        data = self._request_data(params)
        if not data or "class" not in data:
            return [], {}

        all_categories = data["class"]
        primary_categories = []
        sub_categories_map = {}

        for cat in all_categories:
            type_id = cat.get("type_id")
            type_pid = cat.get("type_pid", 0)

            if type_id in self.EXCLUDE_CATEGORIES:
                continue

            if type_pid == 0:  # 一级分类
                primary_categories.append({
                    "type_id": str(type_id),
                    "type_name": cat["type_name"]
                })
            else:  # 子分类
                pid_str = str(type_pid)
                if pid_str not in sub_categories_map:
                    sub_categories_map[pid_str] = []
                sub_categories_map[pid_str].append(
                    {"n": cat["type_name"], "v": str(type_id)})

        self.CATEGORY_CACHE = (primary_categories, sub_categories_map)
        return primary_categories, sub_categories_map

    def homeContent(self, filter):
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
        if self.YEAR_OPTIONS is None:
            self.YEAR_OPTIONS = self._generate_year_options()

        filters = {}

        # 为所有主分类动态构建筛选选项，仅包含类型和年份筛选
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
        try:
            _, sub_categories_map = self._fetch_categories()

            if tid not in sub_categories_map:
                return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

            sub_categories = sub_categories_map[tid]
            all_videos = []

            import concurrent.futures

            def fetch_subcategory_videos(sub_cat):
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

                detail.update({
                    "vod_play_from": play_from,
                    "vod_play_url": play_url
                })
                details.append(detail)

            result = {"list": details}
            return result
        except Exception as e:
            return {"list": []}

    def searchContent(self, key, quick, pg="1"):
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
        return {'url': id, 'header': self.DEFAULT_HEADERS, 'parse': 0, 'jx': 0}

    def destroy(self):
        pass