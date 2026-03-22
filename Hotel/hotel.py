import os
import re
import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
# ====================== 完全保留你的频道配置 + 复刻别人的提取逻辑 ======================
# 配置区
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
IP_DIR = "Hotel/ip"
if not os.path.exists(IP_DIR):
    os.makedirs(IP_DIR)
# 频道分类定义（完整保留你的原版）
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视", "厦门卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘剧场", "淘娱乐",
        "IPTV热播剧场","IPTV谍战剧场", "IPTV戏曲","IPTV经典电影", "IPTV喜剧影院", "IPTV动作影院", "精品剧场","IPTV抗战剧场", 
    ],
}
# 特殊符号映射（完整保留）
SPECIAL_SYMBOLS = ["HD", "LT", "XF", "-", "_", " ", ".", "·", "高清", "标清", "超清", "H265", "4K", "FHD", "HDTV"]
# 移除特殊符号的函数（完整保留）
def remove_special_symbols(text):
    for symbol in SPECIAL_SYMBOLS:
        text = text.replace(symbol, "")
    text = re.sub(r'\s+', '', text)
    return text.strip()
# 频道名称映射（完整保留你的超全匹配规则）
CHANNEL_MAPPING = {
    "CCTV1": ["CCTV1", "CCTV-1", "CCTV1综合", "CCTV1高清", "CCTV1HD", "cctv1","中央1台","sCCTV1-综合","CCTV01"],
    "CCTV2": ["CCTV2", "CCTV-2", "CCTV2财经", "CCTV2高清", "CCTV2HD", "cctv2","中央2台","aCCTV2","sCCTV2-财经","CCTV02"],
    "CCTV3": ["CCTV3", "CCTV-3", "CCTV3综艺", "CCTV3高清", "CCTV3HD", "cctv3","中央3台","acctv3","sCCTV3-综艺","CCTV03"],
    "CCTV4": ["CCTV4", "CCTV-4", "CCTV4中文国际", "CCTV4高清", "CCTV4HD", "cctv4","中央4台","aCCTV4","sCCTV4-国际","CCTV04"],
    "CCTV5": ["CCTV5", "CCTV-5", "CCTV5体育", "CCTV5高清", "CCTV5HD", "cctv5","中央5台","sCCTV5-体育","CCTV05"],
    "CCTV5+": ["CCTV5+", "CCTV-5+", "CCTV5+体育赛事", "CCTV5+高清", "CCTV5+HD", "cctv5+", "CCTV5plus","CCTV5+体育赛事高清",],
    "CCTV6": ["CCTV6", "CCTV-6", "CCTV6电影", "CCTV6高清", "CCTV6HD", "cctv6","中央6台","sCCTV6-电影","CCTV06"],
    "CCTV7": ["CCTV7", "CCTV-7", "CCTV7军事", "CCTV7高清", "CCTV7HD", "cctv7","中央7台","CCTV07"],
    "CCTV8": ["CCTV8", "CCTV-8", "CCTV8电视剧", "CCTV8高清", "CCTV8HD", "cctv8","中央8台","sCCTV8-电视剧","CCTV08"],
    "CCTV9": ["CCTV9", "CCTV-9", "CCTV9纪录", "CCTV9高清", "CCTV9HD", "cctv9","中央9台","sCCTV9-纪录","CCTV09"],
    "CCTV10": ["CCTV10", "CCTV-10", "CCTV10科教", "CCTV10高清", "CCTV10HD", "cctv10","中央10台","sCCTV10-科教"],
    "CCTV11": ["CCTV11", "CCTV-11", "CCTV11戏曲", "CCTV11高清", "CCTV11HD", "cctv11", "中央11台","sCCTV11-戏曲"],
    "CCTV12": ["CCTV12", "CCTV-12", "CCTV12社会与法", "CCTV12高清", "CCTV12HD", "cctv12","中央12台","sCCTV12-社会与法"],
    "CCTV13": ["CCTV13", "CCTV-13", "CCTV13新闻", "CCTV13高清", "CCTV13HD", "cctv13","中央13台","sCCTV13-新闻","CCTV-新闻","CCTV13-新闻",],
    "CCTV14": ["CCTV14", "CCTV-14", "CCTV14少儿", "CCTV14高清", "CCTV14HD", "cctv14","中央14台","sCCTV14-少儿","CCTV-少儿高清","CCTV-少儿"],
    "CCTV15": ["CCTV15", "CCTV-15", "CCTV15音乐", "CCTV15高清", "CCTV15HD", "cctv15","中央15台","sCCTV15-音乐","CCTV-音乐"],
    "CCTV16": ["CCTV16", "CCTV-16", "CCTV16奥林匹克", "CCTV16高清", "CCTV16HD", "cctv16","中央16台"],
    "CCTV17": ["CCTV17", "CCTV-17", "CCTV17农业农村", "CCTV17高清", "CCTV17HD", "cctv17","中央17台"],
    "CCTV4欧洲": ["CCTV4欧洲", "CCTV-4欧洲", "CCTV4欧洲高清", "CCTV4欧洲HD"],
    "CCTV4美洲": ["CCTV4美洲", "CCTV-4美洲", "CCTV4美洲高清", "CCTV4美洲HD"],
    "兵器科技": ["兵器科技", "CCTV兵器科技", "兵器科技频道","兵器科技HD",],
    "风云音乐": ["风云音乐", "CCTV风云音乐"],
    "第一剧场": ["第一剧场", "CCTV第一剧场","第一剧场HD",],
    "风云足球": ["风云足球", "CCTV风云足球","风云足球HD",],
    "风云剧场": ["风云剧场", "CCTV风云剧场","风云剧场HD",],
    "怀旧剧场": ["怀旧剧场", "CCTV怀旧剧场","怀旧剧场HD",],
    "女性时尚": ["女性时尚", "CCTV女性时尚"],
    "世界地理": ["地理世界", "CCTV世界地理","世界地理高清"],
    "央视台球": ["央视台球", "CCTV央视台球","央视台球HD",],
    "高尔夫网球": ["高尔夫网球", "央视高网", "CCTV高尔夫网球", "高尔夫","高尔夫·网球HD",],
    "安徽卫视": ["安徽卫视高清"],
    "北京卫视": ["北京卫视HD","北京卫视高清"],
    "东南卫视": ["福建东南", "东南卫视"],
    "东方卫视": ["上海卫视", "东方卫视","SBN"],
    "农林卫视": ["陕西农林卫视", "农林卫视"],
    "江苏卫视": ["江苏卫视HD","江苏卫视高清"],
    "江西卫视": ["江西卫视高清"],
    "黑龙江卫视": ["黑龙江卫视高清"],
    "吉林卫视": ["吉林卫视","吉林卫视高清"],
    "辽宁卫视": ["辽宁卫视HD","辽宁卫视 高清"],
    "甘肃卫视": ["甘肃卫视","甘肃卫视高清"],
    "湖南卫视": ["湖南卫视", "湖南电视","湖南卫视高清"],
    "河南卫视": ["河南卫视","河南卫视高清"],
    "河北卫视": ["河北卫视","河北卫视高清"],
    "湖北卫视": ["湖北卫视","湖北卫视高清"],
    "海南卫视": ["旅游卫视", "海南卫视HD","海南高清卫视"],
    "厦门卫视": ["厦门卫视","厦门卫视高清"],
    "重庆卫视": ["重庆卫视","重庆卫视高清"],
    "深圳卫视": ["深圳卫视高清", "深圳卫视"],
    "广东卫视": ["广东卫视","广东卫视高清"],
    "广西卫视": ["广西卫视","广西卫视高清"],
    "天津卫视": ["天津卫视","天津卫视高清"],
    "山东卫视": ["山东卫视","山东高清","山东卫视高清","山东卫视HD"],
    "山西卫视": ["山西卫视高清"],
    "星空卫视": ["星空卫视", "星空衛視", "XF星空卫视"],
    "四川卫视": ["四川卫视","四川卫视高清"],
    "浙江卫视": ["浙江卫视高清"],
    "贵州卫视": ["贵州卫视","贵州卫视高清"],
    "内蒙古卫视": ["内蒙古卫视高清", "内蒙古", "内蒙卫视"],
    "康巴卫视": ["康巴卫视"],
    "山东教育卫视": ["山东教育","山东教育卫视"],
    "大湾区卫视": ["南方卫视高清","南方卫视","南方卫视高清"],
    "新疆卫视": ["新疆卫视", "新疆1"],
    "兵团卫视": ["兵团卫", "兵团卫视高清"],
    "西藏卫视": ["XZTV2","西藏卫视高清"],
    "CETV1": ["中国教育1台", "中国教育一台", "中国教育一套高清", "教育一套" ,"CETV-1高清","中国教育"],
    "CETV2": ["中国教育2台", "中国教育二台", "中国教育二套高清"],
    "CETV3": ["中国教育3台", "中国教育三台", "中国教育三套高清"],
    "CETV4": ["中国教育4台", "中国教育四台", "中国教育四套高清"],
    "CGTN英语": ["CGTN 英语高清"],
    "CHC动作电影": ["动作电影","CHC 动作电影",],
    "CHC家庭影院": ["家庭影院","CHC 家庭影院",],
    "CHC影迷电影": ["高清电影","CHC 高清电影",],
    "淘电影": ["淘电影", "IPTV淘电影"],
    "淘精彩": ["淘精彩", "IPTV淘精彩"],
    "淘剧场": ["淘剧场", "IPTV淘剧场"],
    "淘4K": ["淘4K", "IPTV淘4K"],
    "淘娱乐": ["淘娱乐", "IPTV淘娱乐"],
    "淘BABY": ["淘BABY", "IPTV淘BABY", "淘baby"],
    "淘萌宠": ["淘萌宠", "IPTV淘萌宠"],
    "IPTV戏曲": ["相声小品",],
    "IPTV热播剧场": ["IPTV-热播剧场","热播剧场"],
    "IPTV谍战剧场": ["IPTV-谍战剧场","谍战剧场"],
    "IPTV少儿动画": ["IPTV-少儿动画"],
    "": [""],
    "IPTV经典电影": ["经典电影", "IPTV-经典电影"],
    "IPTV喜剧影院": ["喜剧影院", "IPTV-喜剧影院"],
    "IPTV动作影院": ["动作影院", "IPTV-动作影院"],
    "IPTV抗战剧场": ["测试频道15","抗战剧场","IPTV-抗战剧场"],
}
RESULTS_PER_CHANNEL = 20
# 精确频道名称匹配函数（完整保留）
def exact_channel_match(channel_name, pattern_name):
    clean_name = remove_special_symbols(channel_name.strip().lower())
    clean_pattern = remove_special_symbols(pattern_name.strip().lower())
    if clean_name == clean_pattern:
        return True
    cctv_match = re.match(r'^cctv[-_\s]?(\d+[a-z]?)$', clean_name)
    pattern_match = re.match(r'^cctv[-_\s]?(\d+[a-z]?)$', clean_pattern)
    if cctv_match and pattern_match:
        cctv_num1 = cctv_match.group(1)
        cctv_num2 = pattern_match.group(1)
        if cctv_num1 != cctv_num2:
            return False
        else:
            return clean_name == clean_pattern
    if "+" in clean_name and "+" in clean_pattern:
        if "cctv5+" in clean_name and "cctv5+" in clean_pattern:
            return True
    if clean_pattern in clean_name:
        if clean_pattern.endswith(('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')):
            pattern_len = len(clean_pattern)
            if len(clean_name) > pattern_len:
                next_char = clean_name[pattern_len]
                if next_char.isdigit():
                    return False
        return True
    return False
# 统一频道名称（完整保留）
def unify_channel_name(channels_list):
    new_channels_list = []
    for name, channel_url, speed in channels_list:
        original_name = name
        unified_name = None
        clean_name = remove_special_symbols(name.strip().lower())
        cctv_match = re.search(r'^cctv[-_\s]?(\d+[a-z]?)$', clean_name, re.IGNORECASE)
        if cctv_match:
            cctv_num = cctv_match.group(1)
            if cctv_num == "5+":
                standard_name = "CCTV5+"
            else:
                standard_name = f"CCTV{cctv_num}"
            if standard_name in CHANNEL_MAPPING:
                unified_name = standard_name
                print(f"数字匹配: '{original_name}' -> '{standard_name}'")
        if not unified_name:
            for standard_name, variants in CHANNEL_MAPPING.items():
                for variant in variants:
                    if exact_channel_match(name, variant):
                        unified_name = standard_name
                        break
                if unified_name:
                    break
        if not unified_name:
            for pattern in [r'cctv[-\s]?(\d+)高清?', r'cctv[-\s]?(\d+)hd', r'cctv[-\s]?(\d+).*']:
                match = re.search(pattern, clean_name, re.IGNORECASE)
                if match:
                    cctv_num = match.group(1)
                    if cctv_num == "5+":
                        standard_name = "CCTV5+"
                    else:
                        standard_name = f"CCTV{cctv_num}"
                    if standard_name in CHANNEL_MAPPING:
                        unified_name = standard_name
                        print(f"正则匹配: '{original_name}' -> '{standard_name}'")
                        break
        if not unified_name:
            unified_name = original_name
        new_channels_list.append(f"{unified_name},{channel_url},{speed}\n")
        if original_name != unified_name:
            print(f"频道名称统一: '{original_name}' -> '{unified_name}'")
    return new_channels_list
# 按指定顺序排序频道（完整保留）
def sort_channels_by_specified_order(channels_list, category_channels):
    channel_order = {channel: index for index, channel in enumerate(category_channels)}
    def get_channel_sort_key(item):
        name, url, speed = item
        if name in channel_order:
            return (channel_order[name], -float(speed))
        else:
            return (float('inf'), name)
    return sorted(channels_list, key=get_channel_sort_key)
# 分类频道（完整保留，删除"其他频道"）
def classify_channels_by_category(channels_data):
    categorized_channels = {}
    for category in CHANNEL_CATEGORIES.keys():
        categorized_channels[category] = []
    for line in channels_data:
        try:
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue
            name = parts[0]
            url = parts[1]
            speed = parts[2] if len(parts) > 2 else "0.000"
            assigned = False
            for category, channel_list in CHANNEL_CATEGORIES.items():
                if name in channel_list:
                    categorized_channels[category].append((name, url, speed))
                    assigned = True
                    break
        except Exception as e:
            print(f"分类频道时出错: {e}, 行: {line}")
            continue
    return categorized_channels
# 分组并排序频道（完整保留）
def group_and_sort_channels_by_category(categorized_channels):
    processed_categories = {}
    for category, channels in categorized_channels.items():
        if not channels:
            continue
        if category in CHANNEL_CATEGORIES:
            category_order = CHANNEL_CATEGORIES[category]
            channel_groups = {}
            for name, url, speed in channels:
                if name not in channel_groups:
                    channel_groups[name] = []
                channel_groups[name].append((name, url, speed))
            grouped_channels = []
            for channel_name in category_order:
                if channel_name in channel_groups:
                    url_list = channel_groups[channel_name]
                    url_list.sort(key=lambda x: -float(x[2]))
                    url_list = url_list[:RESULTS_PER_CHANNEL]
                    grouped_channels.extend(url_list)
                    del channel_groups[channel_name]
            for channel_name, url_list in channel_groups.items():
                url_list.sort(key=lambda x: -float(x[2]))
                url_list = url_list[:RESULTS_PER_CHANNEL]
                grouped_channels.extend(url_list)
            grouped_channels = sort_channels_by_specified_order(grouped_channels, category_order)
            processed_categories[category] = grouped_channels
        else:
            channels.sort(key=lambda x: -float(x[2]))
            channel_groups = {}
            for name, url, speed in channels:
                if name not in channel_groups:
                    channel_groups[name] = []
                channel_groups[name].append((name, url, speed))
            grouped_channels = []
            for channel_name, url_list in channel_groups.items():
                url_list.sort(key=lambda x: -float(x[2]))
                url_list = url_list[:RESULTS_PER_CHANNEL]
                grouped_channels.extend(url_list)
            grouped_channels.sort(key=lambda x: x[0])
            processed_categories[category] = grouped_channels
    return processed_categories
# ====================== 复刻别人的核心提取逻辑（修改适配+移除测速） ======================
# 1. 读取IP配置（复刻网段扫描逻辑，完整保留）
def read_config(ip_port):
    """解析IP:Port为网段配置，复刻别人的网段扫描逻辑"""
    ip_configs = []
    try:
        if ':' in ip_port:
            ip_part, port = ip_port.split(':', 1)
            parts = ip_part.split('.')
            if len(parts) == 4:
                a, b, c, d = parts
                # 关键：复刻别人的逻辑，将IP第四段改为1，扫描整个网段
                ip = f"{a}.{b}.{c}.1"
                ip_configs.append((ip, port))
        return ip_configs
    except Exception as e:
        print(f"读取IP配置错误: {e}")
        return []
# 2. 检测单个IP:Port的URL可用性（复刻别人的检测逻辑，完整保留）
def check_ip_port(ip_port, url_end):
    try:
        url = f"http://{ip_port}{url_end}"
        resp = requests.get(url, timeout=3, headers=HEADERS, verify=False)
        resp.raise_for_status()
        if "tsfile" in resp.text or "hls" in resp.text or "m3u8" in resp.text:
            print(f"{url} 访问成功")
            return url
    except:
        return None
# 3. 多线程扫描整个网段（复刻别人的网段扫描，完整保留）
def scan_ip_port(ip, port, url_end):
    """扫描IP所在网段的所有主机（1-255）"""
    valid_urls = []
    a, b, c, d = map(int, ip.split('.'))
    ip_ports = [f"{a}.{b}.{c}.{x}:{port}" for x in range(1, 256)]  # 扫描1-255段
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = {executor.submit(check_ip_port, ip_port, url_end): ip_port for ip_port in ip_ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_urls.append(result)
    return valid_urls
# 4. 提取频道（核心修改：适配110.241.188.75:808纯文本格式）
def extract_channels(url):
    hotel_channels = []
    try:
        urls = url.split('/', 3)
        url_x = f"{urls[0]}//{urls[2]}"
        current_ip_port = urls[2]
        
        if "iptv" in url:
            response = requests.get(url, timeout=3, headers=HEADERS, verify=False)
            json_data = response.json()
            for item in json_data.get('data', []):
                if isinstance(item, dict):
                    name = item.get('name')
                    urlx = item.get('url')
                    if urlx and ("tsfile" in urlx or "m3u8" in urlx):
                        if not urlx.startswith('/'):
                            urlx = '/' + urlx
                        urld = f"{url_x}{urlx}"
                        hotel_channels.append((name, urld))
        elif "ZHGXTV" in url:
            response = requests.get(url, timeout=2, headers=HEADERS, verify=False)
            json_data = response.content.decode('utf-8')
            data_lines = json_data.split('\n')
            for line in data_lines:
                line = line.strip()
                if not line:
                    continue
                # 适配纯文本逗号分隔格式（110.241.188.75:808）
                if "," in line and ("hls" in line or "m3u8" in line):
                    # 兼容多逗号情况，只按第一个逗号拆分
                    if line.count(',') >= 1:
                        name, channel_url = line.split(',', 1)
                        # 替换频道URL中的内网IP为当前访问的公网IP:Port
                        channel_url = re.sub(r'(\d+\.\d+\.\d+\.\d+)(:\d+)?/', f'{current_ip_port}/', channel_url)
                        hotel_channels.append((name, channel_url))
                # 兼容原有ZHGXTV格式
                elif len(line.split(',')) == 2 and ("hls" in line or "m3u8" in line):
                    name, channel_url = line.strip().split(',')
                    parts = channel_url.split('/', 3)
                    if len(parts) >= 4:
                        urld = f"{url_x}/{parts[3]}"
                        hotel_channels.append((name, urld))
        return hotel_channels
    except Exception as e:
        print(f"解析频道错误 {url}: {str(e)[:30]}")
        return []
# ====================== 核心流程（整合复刻逻辑，移除测速过滤） ======================
def hotel_iptv():
    try:
        # 1. 读取YML输出的IP文件
        ip_file = os.path.join(IP_DIR, "hotel_ip.txt")
        if not os.path.exists(ip_file):
            print(f"错误：未找到 YML 生成的 {ip_file}")
            return
        with open(ip_file, 'r', encoding='utf-8') as f:
            ip_ports = [line.strip() for line in f if line.strip()]
        if not ip_ports:
            print("警告：IP 文件为空")
            return
        print(f"✅ 读取到 {len(ip_ports)} 个有效 IP，开始扫描网段")
        # 2. 复刻别人的完整流程：IP配置 → 网段扫描 → 提取频道（移除测速）
        valid_urls = []
        url_ends = ["/iptv/live/1000.json?key=txiptv", "/ZHGXTV/Public/json/live_interface.txt"]
        configs = []
        
        # 解析每个IP为网段配置
        for ip_port in ip_ports:
            ip_config = read_config(ip_port)
            configs.extend([(ip, port, url_end) for ip, port in ip_config for url_end in url_ends])
        
        # 多线程扫描网段
        for ip, port, url_end in configs:
            valid_urls.extend(scan_ip_port(ip, port, url_end))
        
        if not valid_urls:
            print("⚠️ 未扫描到有效频道URL")
            return
        print(f"✅ 共扫描到 {len(valid_urls)} 个有效URL")
        # 提取频道
        all_channels = []
        for url in valid_urls:
            all_channels.extend(extract_channels(url))
        
        if not all_channels:
            print("⚠️ 未提取到任何频道")
            return
        print(f"✅ 共提取到 {len(all_channels)} 个频道（已移除测速过滤）")
        
        # 构造无测速的频道列表（speed固定为0.000，兼容后续逻辑）
        no_speed_channels = [(name, url, "0.000") for name, url in all_channels]
        
        # 3. 你的原有流程：名称统一 + 分类 + 排序
        unified_channels = unify_channel_name(no_speed_channels)
        categorized_channels = classify_channels_by_category(unified_channels)
        processed_channels = group_and_sort_channels_by_category(categorized_channels)
        # 4. 写入分类临时文件
        file_paths = []
        for category, channels in processed_channels.items():
            if channels:
                filename = f"{category.replace('频道', '')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"{category},#genre#\n")
                    for name, url, speed in channels:
                        f.write(f"{name},{url}\n")
                file_paths.append(filename)
                print(f"已保存 {len(channels)} 个频道到 {filename}")
        # 5. 合并为最终 hotel.txt
        output_dir = "Hotel"
        os.makedirs(output_dir, exist_ok=True)
        final_output = os.path.join(output_dir, "hotel.txt")
        # 写入头部和固定链接
        beijing_time = datetime.datetime.now()
        current_time = beijing_time.strftime("%Y/%m/%d %H:%M")
        with open(final_output, "w", encoding='utf-8') as f_out:
            f_out.write(f"{current_time}更新,#genre#\n")
            f_out.write("浙江卫视,http://ali-m-l.cztv.com/channels/lantian/channel001/1080p.m3u8\n")
            # 合并分类文件
            for fp in file_paths:
                if os.path.exists(fp):
                    with open(fp, "r", encoding='utf-8') as f_in:
                        f_out.write(f"\n{f_in.read()}")
                    os.remove(fp)
        # 原始顺序去重
        with open(final_output, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        unique_lines = []
        seen_lines = set()
        for line in lines:
            if line not in seen_lines:
                unique_lines.append(line)
                seen_lines.add(line)
        with open(final_output, 'w', encoding='utf-8') as f:
            f.writelines(unique_lines)
        print(f"\n🎉 处理完成！最终文件已保存到: {final_output}")
        print(f"📊 统计：共 {len(unique_lines)-2} 个有效频道（已去重，无测速）")
    except Exception as e:
        print(f"❌ 整体处理失败: {str(e)}")
# ====================== 主函数 ======================
def main():
    start_time = datetime.datetime.now()
    print(f"脚本开始运行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    
    # 执行核心流程
    hotel_iptv()
    
    # 输出运行信息
    end_time = datetime.datetime.now()
    print(f"\n脚本结束运行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    run_time = end_time - start_time
    hours, remainder = divmod(run_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"总运行时间: {hours}小时{minutes}分{seconds}秒")
    print("📌 重要：YML 生成的 IP 文件已完整保留，未做任何修改/删除 | 已移除测速过滤")
if __name__ == "__main__":
    main()
