# 暴风资源站实现
import sys
sys.path.append('..')
import json
import time
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    """
    暴风资源站爬虫实现
    API接口: https://bfzyapi.com/api.php/provide/vod/
    """

    def __init__(self):
        super().__init__()
        self.API_URL = "https://bfzyapi.com/api.php/provide/vod/"
        self.IMAGE_BASE_URL = "https://img.picbf.com"  # 暴风图床地址
        self.EXCLUDE_CATEGORIES = {29, 73}  # 过滤掉理论片和福利分类
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        self.DEFAULT_HEADERS = {
            "User-Agent": self.USER_AGENT
        }
        self.YEAR_OPTIONS = None
        self.CATEGORY_CACHE = None
        self.SPIDER_NAME = "暴风资源站"

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
                response = self.fetch(self.API_URL, params=params, headers=self.DEFAULT_HEADERS, timeout=timeout)
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
        # 处理相对路径的图片地址
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
        return self.SPIDER_NAME

    def init(self, extend=""):
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

            if type_pid == 0:
                primary_categories.append({
                    "type_id": str(type_id),
                    "type_name": cat["type_name"]
                })
            else:
                pid_str = str(type_pid)
                if pid_str not in sub_categories_map:
                    sub_categories_map[pid_str] = []
                sub_categories_map[pid_str].append({"n": cat["type_name"], "v": str(type_id)})
        
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

        # 电影片筛选 (主分类ID为20，子分类包括动作片、喜剧片等)
        if "21" in sub_categories or "22" in sub_categories or "23" in sub_categories or "24" in sub_categories or "25" in sub_categories or "26" in sub_categories or "27" in sub_categories or "28" in sub_categories:
            movie_filters = []
            all_movie_subcats = []
            for cat_id in ["21", "22", "23", "24", "25", "26", "27", "28", "50"]:
                if cat_id in sub_categories:
                    all_movie_subcats.extend(sub_categories[cat_id])
            if all_movie_subcats:
                movie_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_movie_subcats
                ]})
            movie_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["20"] = movie_filters

        # 连续剧筛选 (主分类ID为30，子分类包括国产剧、欧美剧等)
        if "31" in sub_categories or "32" in sub_categories or "33" in sub_categories or "34" in sub_categories or "35" in sub_categories or "36" in sub_categories or "37" in sub_categories or "38" in sub_categories:
            tv_filters = []
            all_tv_subcats = []
            for cat_id in ["31", "32", "33", "34", "35", "36", "37", "38"]:
                if cat_id in sub_categories:
                    all_tv_subcats.extend(sub_categories[cat_id])
            if all_tv_subcats:
                tv_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_tv_subcats
                ]})
            tv_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["30"] = tv_filters

        # 动漫片筛选 (主分类ID为39，子分类包括国产动漫、日韩动漫等)
        if "40" in sub_categories or "41" in sub_categories or "42" in sub_categories or "43" in sub_categories or "44" in sub_categories:
            cartoon_filters = []
            all_cartoon_subcats = []
            for cat_id in ["40", "41", "42", "43", "44"]:
                if cat_id in sub_categories:
                    all_cartoon_subcats.extend(sub_categories[cat_id])
            if all_cartoon_subcats:
                cartoon_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_cartoon_subcats
                ]})
            cartoon_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["39"] = cartoon_filters

        # 综艺片筛选 (主分类ID为45，子分类包括大陆综艺、港台综艺等)
        if "46" in sub_categories or "47" in sub_categories or "48" in sub_categories or "49" in sub_categories:
            variety_filters = []
            all_variety_subcats = []
            for cat_id in ["46", "47", "48", "49"]:
                if cat_id in sub_categories:
                    all_variety_subcats.extend(sub_categories[cat_id])
            if all_variety_subcats:
                variety_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_variety_subcats
                ]})
            variety_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["45"] = variety_filters

        # 体育赛事筛选 (主分类ID为53，子分类包括足球、篮球等)
        if "54" in sub_categories or "55" in sub_categories or "56" in sub_categories or "57" in sub_categories:
            sport_filters = []
            all_sport_subcats = []
            for cat_id in ["54", "55", "56", "57"]:
                if cat_id in sub_categories:
                    all_sport_subcats.extend(sub_categories[cat_id])
            if all_sport_subcats:
                sport_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_sport_subcats
                ]})
            sport_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["53"] = sport_filters

        # 短剧大全筛选 (主分类ID为58，子分类包括各种短剧类型)
        if "65" in sub_categories or "66" in sub_categories or "67" in sub_categories or "68" in sub_categories or "69" in sub_categories or "70" in sub_categories or "71" in sub_categories or "72" in sub_categories:
            short_filters = []
            all_short_subcats = []
            for cat_id in ["65", "66", "67", "68", "69", "70", "71", "72"]:
                if cat_id in sub_categories:
                    all_short_subcats.extend(sub_categories[cat_id])
            if all_short_subcats:
                short_filters.append({"key": "class", "name": "类型", "value": [
                    {"n": "全部", "v": ""},
                    *all_short_subcats
                ]})
            short_filters.append({"key": "year", "name": "年份", "value": self.YEAR_OPTIONS})
            filters["58"] = short_filters

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
                futures = [executor.submit(fetch_subcategory_videos, sub_cat) for sub_cat in sub_categories]
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
            data = self._request_data({"ac": "detail", "wd": key, "pg": pg})
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