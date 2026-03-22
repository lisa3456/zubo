import os
import re
import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning

# 禁用不安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ====================== 配置区 ======================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
IP_DIR = "Hotel/ip"
if not os.path.exists(IP_DIR):
    os.makedirs(IP_DIR)

# 仅保留【央视频道+卫视频道】
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17",
    ],
    "卫视频道": [
        "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "山西卫视", "陕西卫视",
    ],
}

SPECIAL_SYMBOLS = ["HD", "LT", "XF", "-", "_", " ", ".", "·", "高清", "标清", "超清", "H265", "4K", "FHD", "HDTV"]
def remove_special_symbols(text):
    for symbol in SPECIAL_SYMBOLS:
        text = text.replace(symbol, "")
    text = re.sub(r'\s+', '', text)
    return text.strip()

CHANNEL_MAPPING = {
    "CCTV1": ["CCTV1", "CCTV-1", "CCTV1综合", "CCTV1高清", "CCTV1HD", "cctv1","中央1台","CCTV01"],
    "CCTV2": ["CCTV2", "CCTV-2", "CCTV2财经", "CCTV2高清", "CCTV2HD", "cctv2","中央2台","CCTV02"],
    "CCTV3": ["CCTV3", "CCTV-3", "CCTV3综艺", "CCTV3高清", "CCTV3HD", "cctv3","中央3台","CCTV03"],
    "CCTV4": ["CCTV4", "CCTV-4", "CCTV4中文国际", "CCTV4高清", "CCTV4HD", "cctv4","中央4台","CCTV04"],
    "CCTV5": ["CCTV5", "CCTV-5", "CCTV5体育", "CCTV5高清", "CCTV5HD", "cctv5","中央5台","CCTV05"],
    "CCTV5+": ["CCTV5+", "CCTV-5+", "CCTV5+体育赛事", "CCTV5+高清", "CCTV5+HD", "cctv5+", "CCTV5plus"],
    "CCTV6": ["CCTV6", "CCTV-6", "CCTV6电影", "CCTV6高清", "CCTV6HD", "cctv6","中央6台","CCTV06"],
    "CCTV7": ["CCTV7", "CCTV-7", "CCTV7军事", "CCTV7高清", "CCTV7HD", "cctv7","中央7台","CCTV07"],
    "CCTV8": ["CCTV8", "CCTV-8", "CCTV8电视剧", "CCTV8高清", "CCTV8HD", "cctv8","中央8台","CCTV08"],
    "CCTV9": ["CCTV9", "CCTV-9", "CCTV9纪录", "CCTV9高清", "CCTV9HD", "cctv9","中央9台","CCTV09"],
    "CCTV10": ["CCTV10", "CCTV-10", "CCTV10科教", "CCTV10高清", "CCTV10HD", "cctv10","中央10台"],
    "CCTV11": ["CCTV11", "CCTV-11", "CCTV11戏曲", "CCTV11高清", "CCTV11HD", "cctv11", "中央11台"],
    "CCTV12": ["CCTV12", "CCTV-12", "CCTV12社会与法", "CCTV12高清", "CCTV12HD", "cctv12","中央12台"],
    "CCTV13": ["CCTV13", "CCTV-13", "CCTV13新闻", "CCTV13高清", "CCTV13HD", "cctv13","中央13台","CCTV-新闻"],
    "CCTV14": ["CCTV14", "CCTV-14", "CCTV14少儿", "CCTV14高清", "CCTV14HD", "cctv14","中央14台","CCTV-少儿"],
    "CCTV15": ["CCTV15", "CCTV-15", "CCTV15音乐", "CCTV15高清", "CCTV15HD", "cctv15","中央15台","CCTV-音乐"],
    "CCTV16": ["CCTV16", "CCTV-16", "CCTV16奥林匹克", "CCTV16高清", "CCTV16HD", "cctv16","中央16台"],
    "CCTV17": ["CCTV17", "CCTV-17", "CCTV17农业农村", "CCTV17高清", "CCTV17HD", "cctv17","中央17台"],
    "湖南卫视": ["湖南卫视", "湖南电视","湖南卫视高清"],
    "浙江卫视": ["浙江卫视高清"],
    "江苏卫视": ["江苏卫视HD","江苏卫视高清"],
    "东方卫视": ["上海卫视", "东方卫视"],
    "深圳卫视": ["深圳卫视高清", "深圳卫视"],
    "北京卫视": ["北京卫视HD","北京卫视高清"],
    "广东卫视": ["广东卫视","广东卫视高清"],
    "广西卫视": ["广西卫视","广西卫视高清"],
    "东南卫视": ["福建东南", "东南卫视"],
    "河北卫视": ["河北卫视","河北卫视高清"],
    "河南卫视": ["河南卫视","河南卫视高清"],
    "湖北卫视": ["湖北卫视","湖北卫视高清"],
    "四川卫视": ["四川卫视","四川卫视高清"],
    "重庆卫视": ["重庆卫视","重庆卫视高清"],
    "贵州卫视": ["贵州卫视","贵州卫视高清"],
    "云南卫视": ["云南卫视","云南卫视高清"],
    "天津卫视": ["天津卫视","天津卫视高清"],
    "安徽卫视": ["安徽卫视高清"],
    "山东卫视": ["山东卫视","山东卫视高清","山东卫视HD"],
    "辽宁卫视": ["辽宁卫视HD","辽宁卫视 高清"],
    "黑龙江卫视": ["黑龙江卫视高清"],
    "吉林卫视": ["吉林卫视","吉林卫视高清"],
    "内蒙古卫视": ["内蒙古卫视高清", "内蒙古"],
    "山西卫视": ["山西卫视高清"],
    "陕西卫视": ["陕西卫视"],
}

RESULTS_PER_CHANNEL = 50

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

def unify_channel_name(channels_list):
    new_channels_list = []
    for name, channel_url in channels_list:
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
        new_channels_list.append(f"{unified_name},{channel_url}\n")
        if original_name != unified_name:
            print(f"频道名称统一: '{original_name}' -> '{unified_name}'")
    return new_channels_list

def sort_channels_by_specified_order(channels_list, category_channels):
    channel_order = {channel: index for index, channel in enumerate(category_channels)}
    def get_channel_sort_key(item):
        name, url = item
        if name in channel_order:
            return (channel_order[name], name)
        else:
            return (float('inf'), name)
    return sorted(channels_list, key=get_channel_sort_key)

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
            assigned = False
            if name.startswith("CCTV"):
                categorized_channels["央视频道"].append((name, url))
                assigned = True
            else:
                for category, channel_list in CHANNEL_CATEGORIES.items():
                    if name in channel_list:
                        categorized_channels[category].append((name, url))
                        assigned = True
                        break
        except Exception as e:
            print(f"分类频道时出错: {e}, 行: {line}")
            continue
    return categorized_channels

def group_and_sort_channels_by_category(categorized_channels):
    processed_categories = {}
    for category, channels in categorized_channels.items():
        if not channels:
            continue
        if category in CHANNEL_CATEGORIES:
            category_order = CHANNEL_CATEGORIES[category]
            channel_groups = {}
            for name, url in channels:
                if name not in channel_groups:
                    channel_groups[name] = []
                channel_groups[name].append((name, url))
            grouped_channels = []
            for channel_name in category_order:
                if channel_name in channel_groups:
                    url_list = channel_groups[channel_name]
                    url_list = url_list[:RESULTS_PER_CHANNEL]
                    grouped_channels.extend(url_list)
                    del channel_groups[channel_name]
            for channel_name, url_list in channel_groups.items():
                url_list = url_list[:RESULTS_PER_CHANNEL]
                grouped_channels.extend(url_list)
            grouped_channels = sort_channels_by_specified_order(grouped_channels, category_order)
            processed_categories[category] = grouped_channels
        else:
            channel_groups = {}
            for name, url in channels:
                if name not in channel_groups:
                    channel_groups[name] = []
                channel_groups[name].append((name, url))
            grouped_channels = []
            for channel_name, url_list in channel_groups.items():
                url_list = url_list[:RESULTS_PER_CHANNEL]
                grouped_channels.extend(url_list)
            grouped_channels.sort(key=lambda x: x[0])
            processed_categories[category] = grouped_channels
    return processed_categories

def check_single_ip(ip_port, url_end):
    try:
        url = f"http://{ip_port}{url_end}"
        resp = requests.get(url, timeout=3, headers=HEADERS, verify=False)
        resp.raise_for_status()
        if "tsfile" in resp.text or "hls" in resp.text or "m3u8" in resp.text:
            print(f"{url} 访问成功")
            return url
    except:
        return None

def extract_channels(url):
    hotel_channels = []
    try:
        urls = url.split('/', 3)
        url_x = f"{urls[0]}//{urls[2]}"
        current_ip_port = urls[2]
        
        if "ZHGXTV" in url:
            response = requests.get(url, timeout=2, headers=HEADERS, verify=False)
            json_data = response.content.decode('utf-8')
            data_lines = json_data.split('\n')
            for line in data_lines:
                line = line.strip()
                if not line:
                    continue
                if "," in line and ("hls" in line or "m3u8" in line):
                    if line.count(',') >= 1:
                        name, channel_url = line.split(',', 1)
                        channel_url = re.sub(r'(\d+\.\d+\.\d+\.\d+)(:\d+)?/', f'{current_ip_port}/', channel_url)
                        hotel_channels.append((name, channel_url))
                elif len(line.split(',')) == 2 and ("hls" in line or "m3u8" in line):
                    name, channel_url = line.strip().split(',')
                    parts = channel_url.split('/', 3)
                    if len(parts) >= 4:
                        urld = f"{url_x}/{parts[3]}"
                        hotel_channels.append((name, urld))
        elif "iptv" in url:
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
        return hotel_channels
    except Exception as e:
        print(f"解析频道错误 {url}: {str(e)[:30]}")
        return []

def hotel_iptv():
    try:
        ip_file = os.path.join(IP_DIR, "hotel_ip.txt")
        if not os.path.exists(ip_file):
            print(f"错误：未找到 {ip_file}")
            return
        with open(ip_file, 'r', encoding='utf-8') as f:
            ip_ports = [line.strip() for line in f if line.strip()]
        if not ip_ports:
            print("警告：IP 文件为空")
            return
        print(f"✅ 读取到 {len(ip_ports)} 个有效 IP，开始访问单个IP")
        
        valid_urls = []
        url_ends = ["/iptv/live/1000.json?key=txiptv", "/ZHGXTV/Public/json/live_interface.txt"]
        
        for ip_port in ip_ports:
            for url_end in url_ends:
                url = check_single_ip(ip_port, url_end)
                if url:
                    valid_urls.append(url)
        
        if not valid_urls:
            print("⚠️ 未扫描到有效频道URL")
            return
        print(f"✅ 共扫描到 {len(valid_urls)} 个有效URL")
        
        all_channels = []
        for url in valid_urls:
            all_channels.extend(extract_channels(url))
        
        if not all_channels:
            print("⚠️ 未提取到任何频道")
            return
        print(f"✅ 共提取到 {len(all_channels)} 个频道（已移除测速过滤）")
        
        unified_channels = unify_channel_name(all_channels)
        categorized_channels = classify_channels_by_category(unified_channels)
        processed_channels = group_and_sort_channels_by_category(categorized_channels)
        
        file_paths = []
        for category, channels in processed_channels.items():
            if channels:
                filename = f"{category.replace('频道', '')}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"{category},#genre#\n")
                    for name, url in channels:
                        f.write(f"{name},{url}\n")
                file_paths.append(filename)
                print(f"已保存 {len(channels)} 个频道到 {filename}")
        
        output_dir = "Hotel"
        os.makedirs(output_dir, exist_ok=True)
        final_output = os.path.join(output_dir, "hotel.txt")
        beijing_time = datetime.datetime.now()
        current_time = beijing_time.strftime("%Y/%m/%d %H:%M")
        
        # ✅ 关键修复：严格按「央视→卫视」顺序写入，保证结构正确
        with open(final_output, "w", encoding='utf-8') as f_out:
            f_out.write(f"{current_time}更新,#genre#\n")
            
            # 先写入央视频道
            for fp in file_paths:
                if "央视" in fp:
                    if os.path.exists(fp):
                        with open(fp, "r", encoding='utf-8') as f_in:
                            f_out.write(f"\n{f_in.read()}\n")
                        os.remove(fp)
                    break
            
            # 再写入卫视频道
            for fp in file_paths:
                if "卫视" in fp:
                    if os.path.exists(fp):
                        with open(fp, "r", encoding='utf-8') as f_in:
                            f_out.write(f"\n{f_in.read()}\n")
                        os.remove(fp)
                    break
        
        # 去重逻辑保持不变
        with open(final_output, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        unique_lines = []
        seen = set()
        genre_lines = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if "#genre#" in line_stripped:
                genre_lines.append(line)
                continue
            name, url = line_stripped.split(",", 1)
            ip_port = url.split("//")[1].split("/")[0]
            key = (name, ip_port)
            if key not in seen:
                seen.add(key)
                unique_lines.append(line)
        
        final_lines = genre_lines + unique_lines
        with open(final_output, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        
        print(f"\n🎉 处理完成！最终文件已保存到: {final_output}")
        print(f"📊 统计：共 {len(final_lines)-2} 个有效频道（已去重，无测速）")
    except Exception as e:
        print(f"❌ 整体处理失败: {str(e)}")

def main():
    start_time = datetime.datetime.now()
    print(f"脚本开始运行时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    hotel_iptv()
    end_time = datetime.datetime.now()
    print(f"\n脚本结束运行时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    run_time = end_time - start_time
    hours, remainder = divmod(run_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"总运行时间: {hours}小时{minutes}分{seconds}秒")
    print("📌 已移除测速+网段扫描 | 仅保留央视频道+卫视频道 | 输出hotel.txt | CCTV正确归类")

if __name__ == "__main__":
    main()
