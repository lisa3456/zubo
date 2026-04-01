import os
import re
import json
import subprocess
import concurrent.futures
from datetime import datetime, timezone, timedelta

# ================= 基础配置 =================
IP_DIR = "ip"
RTP_DIR = "rtp"
ZUBO_FILE = "zubo.txt"
IPTV_FILE = "IPTV.txt"
FAILED_COUNT_FILE = "失效IP计数.json"
MAX_FAILED_TIMES = 3  # 连续失败≥3次直接删除
THREAD_MAX = 15       # 检测线程数，可根据服务器调整

# 全局IP-省份/运营商映射（绑定IP与归属文件）
ip_info = {}

# ================= 失败计数操作 =================
def load_failed_count():
    """加载IP连续失败计数，文件不存在则返回空字典"""
    if os.path.exists(FAILED_COUNT_FILE):
        try:
            with open(FAILED_COUNT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 加载失败计数文件出错，重置为空：{e}")
    return {}

def save_failed_count(failed_count):
    """保存IP连续失败计数到json文件"""
    try:
        with open(FAILED_COUNT_FILE, "w", encoding="utf-8") as f:
            json.dump(failed_count, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存失败计数文件失败：{e}")

# ================= 频道分类与映射配置 =================
CHANNEL_CATEGORIES = {
    "央视": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17"
    ],
    "卫视": [
        "北京卫视", "浙江卫视", "东方卫视", "湖南卫视", "江苏卫视", "深圳卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视"
    ],
    "数字": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘剧场", "淘娱乐", "东方影视", 
        "风云剧场", "怀旧剧场", "第一剧场", "都市剧场", "欢笑剧场", 
        "iHOT爱历史", "iHOT爱谍战", "iHOT爱悬疑", "iHOT爱旅行",
        "华数热播剧场", "华数军旅剧场", "华数谍战剧场", "华数城市剧场", "华数古装剧场", "华数魅力时尚",
        "兵器科技", "风云音乐", "风云足球", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
        "央视文化精品", "电视指南", "求索纪录", "求索科学", "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", 
        "睛彩青少", "睛彩竞技", "睛彩篮球", "文物宝库", "乐游", "生活时尚", "游戏风云", 
        "星空卫视", "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台"
    ],
}

CHANNEL_MAPPING = {
    "CCTV1": ["CCTV-1", "CCTV-1 HD", "CCTV1 HD", "CCTV-1综合"],
    "CCTV2": ["CCTV-2", "CCTV-2 HD", "CCTV2 HD", "CCTV-2财经"],
    "CCTV3": ["CCTV-3", "CCTV-3 HD", "CCTV3 HD", "CCTV-3综艺"],
    "CCTV4": ["CCTV-4", "CCTV-4 HD", "CCTV4 HD", "CCTV-4中文国际"],
    "CCTV4欧洲": ["CCTV-4欧洲", "CCTV-4欧洲", "CCTV4欧洲 HD", "CCTV-4 欧洲", "CCTV-4中文国际欧洲", "CCTV4中文欧洲"],
    "CCTV4美洲": ["CCTV-4美洲", "CCTV-4北美", "CCTV4美洲 HD", "CCTV-4 美洲", "CCTV-4中文国际美洲", "CCTV4中文美洲"],
    "CCTV5": ["CCTV-5", "CCTV-5 HD", "CCTV5 HD", "CCTV-5体育"],
    "CCTV5+": ["CCTV-5+", "CCTV-5+ HD", "CCTV5+ HD", "CCTV-5+体育赛事"],
    "CCTV6": ["CCTV-6", "CCTV-6 HD", "CCTV6 HD", "CCTV-6电影"],
    "CCTV7": ["CCTV-7", "CCTV-7 HD", "CCTV7 HD", "CCTV-7国防军事"],
    "CCTV8": ["CCTV-8", "CCTV-8 HD", "CCTV8 HD", "CCTV-8电视剧"],
    "CCTV9": ["CCTV-9", "CCTV-9 HD", "CCTV9 HD", "CCTV-9纪录"],
    "CCTV10": ["CCTV-10", "CCTV-10 HD", "CCTV10 HD", "CCTV-10科教"],
    "CCTV11": ["CCTV-11", "CCTV-11 HD", "CCTV11 HD", "CCTV-11戏曲"],
    "CCTV12": ["CCTV-12", "CCTV-12 HD", "CCTV12 HD", "CCTV-12社会与法"],
    "CCTV13": ["CCTV-13", "CCTV-13 HD", "CCTV13 HD", "CCTV-13新闻"],
    "CCTV14": ["CCTV-14", "CCTV-14 HD", "CCTV14 HD", "CCTV-14少儿"],
    "CCTV15": ["CCTV-15", "CCTV-15 HD", "CCTV15 HD", "CCTV-15音乐"],
    "CCTV16": ["CCTV-16", "CCTV-16 HD", "CCTV-16 4K", "CCTV-16奥林匹克", "CCTV16 4K", "CCTV-16奥林匹克4K"],
    "CCTV17": ["CCTV-17", "CCTV-17 HD", "CCTV17 HD", "CCTV-17农业农村"],
    "CCTV4K": ["CCTV4K超高清", "CCTV-4K超高清", "CCTV-4K 超高清", "CCTV 4K"],
    "CCTV8K": ["CCTV8K超高清", "CCTV-8K超高清", "CCTV-8K 超高清", "CCTV 8K"],
    "兵器科技": ["CCTV-兵器科技", "CCTV兵器科技"],
    "风云音乐": ["CCTV-风云音乐", "CCTV风云音乐"],
    "第一剧场": ["CCTV-第一剧场", "CCTV第一剧场"],
    "风云足球": ["CCTV-风云足球", "CCTV风云足球"],
    "风云剧场": ["CCTV-风云剧场", "CCTV风云剧场"],
    "怀旧剧场": ["CCTV-怀旧剧场", "CCTV怀旧剧场"],
    "女性时尚": ["CCTV-女性时尚", "CCTV女性时尚"],
    "世界地理": ["CCTV-世界地理", "CCTV世界地理"],
    "央视台球": ["CCTV-央视台球", "CCTV央视台球"],
    "高尔夫网球": ["CCTV-高尔夫网球", "CCTV高尔夫网球", "CCTV央视高网", "CCTV-高尔夫·网球", "央视高网"],
    "央视文化精品": ["CCTV-央视文化精品", "CCTV央视文化精品", "CCTV文化精品", "CCTV-文化精品", "文化精品"],
    "卫生健康": ["CCTV-卫生健康", "CCTV卫生健康"],
    "电视指南": ["CCTV-电视指南", "CCTV电视指南"],
    "农林卫视": ["陕西农林卫视"],
    "三沙卫视": ["海南三沙卫视"],
    "兵团卫视": ["新疆兵团卫视"],
    "延边卫视": ["吉林延边卫视"],
    "安多卫视": ["青海安多卫视"],
    "康巴卫视": ["四川康巴卫视"],
    "山东教育卫视": ["山东教育"],
    "中国教育1台": ["CETV1", "中国教育一台", "中国教育1", "CETV-1 综合教育", "CETV-1"],
    "中国教育2台": ["CETV2", "中国教育二台", "中国教育2", "CETV-2 空中课堂", "CETV-2"],
    "中国教育3台": ["CETV3", "中国教育三台", "中国教育3", "CETV-3 教育服务", "CETV-3"],
    "中国教育4台": ["CETV4", "中国教育四台", "中国教育4", "CETV-4 职业教育", "CETV-4"],
    "早期教育": ["中国教育5台", "中国教育五台", "CETV早期教育", "华电早期教育", "CETV 早期教育"],
    "CHC影迷电影": ["CHC高清电影", "CHC-影迷电影", "影迷电影", "chc高清电影"],
    "淘电影": ["IPTV淘电影", "北京IPTV淘电影", "北京淘电影"],
    "淘精彩": ["IPTV淘精彩", "北京IPTV淘精彩", "北京淘精彩"],
    "淘剧场": ["IPTV淘剧场", "北京IPTV淘剧场", "北京淘剧场"],
    "淘4K": ["IPTV淘4K", "北京IPTV4K超清", "北京淘4K", "淘4K", "淘 4K"],
    "淘娱乐": ["IPTV淘娱乐", "北京IPTV淘娱乐", "北京淘娱乐"],
    "淘BABY": ["IPTV淘BABY", "北京IPTV淘BABY", "北京淘BABY", "IPTV淘baby", "北京IPTV淘baby", "北京淘baby"],
    "淘萌宠": ["IPTV淘萌宠", "北京IPTV萌宠TV", "北京淘萌宠"],
    "魅力足球": ["上海魅力足球"],
    "睛彩青少": ["睛彩羽毛球"],
    "求索纪录": ["求索记录", "求索纪录4K", "求索记录4K", "求索纪录 4K", "求索记录 4K"],
    "金鹰纪实": ["湖南金鹰纪实", "金鹰记实"],
    "纪实科教": ["北京纪实科教", "BRTV纪实科教", "纪实科教8K"],
    "星空卫视": ["星空衛視", "星空衛视", "星空卫視"],
    "ChannelV": ["CHANNEL-V", "Channel[V]"],
    "凤凰卫视中文台": ["凤凰中文", "凤凰中文台", "凤凰卫视中文", "凤凰卫视"],
    "凤凰卫视香港台": ["凤凰香港台", "凤凰卫视香港", "凤凰香港"],
    "凤凰卫视资讯台": ["凤凰资讯", "凤凰资讯台", "凤凰咨询", "凤凰咨询台", "凤凰卫视咨询台", "凤凰卫视资讯", "凤凰卫视咨询"],
    "凤凰卫视电影台": ["凤凰电影", "凤凰电影台", "凤凰卫视电影", "鳳凰衛視電影台", " 凤凰电影"],
    "茶频道": ["湖南茶频道"],
    "快乐垂钓": ["湖南快乐垂钓"],
    "先锋乒羽": ["湖南先锋乒羽"],
    "天元围棋": ["天元围棋频道"],
    "汽摩": ["重庆汽摩", "汽摩频道", "重庆汽摩频道"],
    "梨园频道": ["河南梨园频道", "梨园", "河南梨园"],
    "文物宝库": ["河南文物宝库"],
    "武术世界": ["河南武术世界"],
    "乐游": ["乐游频道", "上海乐游频道", "乐游纪实", "SiTV乐游频道", "SiTV 乐游频道"],
    "欢笑剧场": ["上海欢笑剧场4K", "欢笑剧场 4K", "欢笑剧场4K", "上海欢笑剧场"],
    "东方影视": ["东方影视SD", "上海东方影视"],
    "生活时尚": ["生活时尚4K", "SiTV生活时尚", "上海生活时尚"],
    "都市剧场": ["都市剧场4K", "SiTV都市剧场", "上海都市剧场"],
    "游戏风云": ["游戏风云4K", "SiTV游戏风云", "上海游戏风云"],
    "金色学堂": ["金色学堂4K", "SiTV金色学堂", "上海金色学堂"],
    "动漫秀场": ["动漫秀场4K", "SiTV动漫秀场", "上海动漫秀场"],
    "卡酷少儿": ["北京KAKU少儿", "BRTV卡酷少儿", "北京卡酷少儿", "卡酷动画"],
    "哈哈炫动": ["炫动卡通", "上海哈哈炫动"],
    "优漫卡通": ["江苏优漫卡通", "优漫漫画"],
    "金鹰卡通": ["湖南金鹰卡通"],
    "中国交通": ["中国交通频道"],
    "中国天气": ["中国天气频道"],
    "iHOT爱历史": ["爱历史"],
    "iHOT爱谍战": ["爱谍战"], 
    "iHOT爱悬疑": ["爱悬疑"],
    "iHOT爱旅行": ["爱旅行"],
    "华数热播剧场": ["热播剧场", "IPTV热播剧场"],
    "华数谍战剧场": ["谍战剧场", "IPTV谍战剧场"],
    "华数军旅剧场": ["军旅剧场", "IPTV军旅剧场"],
    "华数古装剧场": ["古装剧场", "IPTV古装剧场"],
    "华数城市剧场": ["城市剧场", "IPTV城市剧场"],   
    "华数魅力时尚": ["魅力时尚", "IPTV魅力时尚"],
}

# ================= 第一阶段：生成zubo.txt组合链接 =================
def first_stage():
    print("🔔 【第一阶段】开始生成zubo.txt组合链接")
    if not os.path.exists(IP_DIR):
        print("⚠️ ip目录不存在，跳过第一阶段")
        return
    if not os.path.exists(RTP_DIR):
        print("⚠️ rtp目录不存在，跳过第一阶段")
        return
    
    combined_lines = []
    # 遍历ip目录下的所有txt文件，匹配对应rtp文件
    for ip_file in os.listdir(IP_DIR):
        if not ip_file.endswith(".txt"):
            continue
        ip_path = os.path.join(IP_DIR, ip_file)
        rtp_path = os.path.join(RTP_DIR, ip_file)
        if not os.path.exists(rtp_path):
            print(f"⚠️ 未找到{ip_file}对应的rtp文件，跳过")
            continue
        
        # 读取IP和RTP内容
        try:
            with open(ip_path, encoding="utf-8") as f1, open(rtp_path, encoding="utf-8") as f2:
                ip_lines = [x.strip() for x in f1 if x.strip()]
                rtp_lines = [x.strip() for x in f2 if x.strip() and "," in x]
        except Exception as e:
            print(f"⚠️ 读取{ip_file}失败：{e}，跳过")
            continue
        
        # 组合链接
        for ip_port in ip_lines:
            for rtp_line in rtp_lines:
                ch_name, rtp_url = rtp_line.split(",", 1)
                if "rtp://" in rtp_url:
                    part = rtp_url.split("rtp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/rtp/{part}")
                elif "udp://" in rtp_url:
                    part = rtp_url.split("udp://", 1)[1]
                    combined_lines.append(f"{ch_name},http://{ip_port}/udp/{part}")
    
    # 去重：按链接去重，保留唯一线路
    unique_lines = {}
    for line in combined_lines:
        url_part = line.split(",", 1)[1]
        if url_part not in unique_lines:
            unique_lines[url_part] = line
    
    # 写入zubo.txt
    try:
        with open(ZUBO_FILE, "w", encoding="utf-8") as f:
            for line in unique_lines.values():
                f.write(line + "\n")
        print(f"🎯 第一阶段完成，写入{len(unique_lines)}条唯一组合链接")
    except Exception as e:
        print(f"❌ 写入zubo.txt失败：{e}")

# ================= 第二阶段：多线程检测IP+更新失败计数+生成IPTV.txt =================
def second_stage():
    global ip_info
    print("\n🧩 【第二阶段】开始多线程检测IP+生成IPTV.txt")
    if not os.path.exists(ZUBO_FILE):
        print("⚠️ zubo.txt不存在，跳过第二阶段")
        return None, None
    
    # 检测流是否可播放的核心函数
    def check_stream(url, timeout=12):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-i", url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
            )
            return b"codec_type" in result.stdout
        except Exception:
            return False
    
    # 1. 重新加载IP-省份/运营商映射（每次运行都刷新，保证最新）
    ip_info.clear()
    all_ips = set()
    if os.path.exists(IP_DIR):
        for fname in os.listdir(IP_DIR):
            if not fname.endswith(".txt"):
                continue
            province_operator = fname.replace(".txt", "")
            try:
                with open(os.path.join(IP_DIR, fname), encoding="utf-8") as f:
                    for line in f:
                        ip_port = line.strip()
                        if ip_port and ip_port not in ip_info:
                            ip_info[ip_port] = province_operator
                            all_ips.add(ip_port)
            except Exception as e:
                print(f"⚠️ 读取{fname}失败：{e}，跳过")
    print(f"📥 加载到{len(ip_info)}个IP，分属{len(set(ip_info.values()))}个省份/运营商")
    
    # 2. 频道别名映射
    alias_map = {}
    for main_name, aliases in CHANNEL_MAPPING.items():
        for alias in aliases:
            alias_map[alias] = main_name
    
    # 3. 按IP分组频道链接
    ip_channel_groups = {}
    with open(ZUBO_FILE, encoding="utf-8") as f:
        for line in f:
            if "," not in line:
                continue
            ch_name, url = line.strip().split(",", 1)
            ch_main = alias_map.get(ch_name, ch_name)
            # 提取URL中的IP:port
            ip_match = re.match(r"http://([^/]+)/", url)
            if not ip_match:
                continue
            ip_port = ip_match.group(1)
            if ip_port not in ip_info:
                continue
            ip_channel_groups.setdefault(ip_port, []).append((ch_main, url))
    
    if not ip_channel_groups:
        print("⚠️ 无有效IP频道分组，跳过检测")
        return None, None
    
    # 4. 多线程检测IP是否可播放
    playable_ips = set()
    unplayable_ips = set()
    failed_count = load_failed_count()
    
    print(f"🚀 启动{THREAD_MAX}线程检测，共{len(ip_channel_groups)}个IP待检测...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_MAX) as executor:
        # 提交检测任务：每个IP取第一个频道链接检测（代表性）
        futures = {
            executor.submit(check_stream, entries[0][1]): ip_port
            for ip_port, entries in ip_channel_groups.items()
        }
        # 处理检测结果
        for future in concurrent.futures.as_completed(futures):
            ip_port = futures[future]
            try:
                if future.result():
                    playable_ips.add(ip_port)
                else:
                    unplayable_ips.add(ip_port)
            except Exception as e:
                unplayable_ips.add(ip_port)
                print(f"⚠️ 检测{ip_port}异常：{e}，标记为不可用")
    
    # 5. 更新IP连续失败计数（核心：检测成功重置为0，失败+1）
    for ip_port in all_ips:
        if ip_port in playable_ips:
            failed_count[ip_port] = 0  # 成功：重置计数
        elif ip_port in unplayable_ips:
            failed_count[ip_port] = failed_count.get(ip_port, 0) + 1  # 失败：计数+1
    save_failed_count(failed_count)
    
    # 打印检测结果日志
    print(f"\n✅ 检测完成：可播放IP{len(playable_ips)}个，不可用IP{len(unplayable_ips)}个")
    for ip_port in unplayable_ips:
        cnt = failed_count.get(ip_port, 0)
        print(f"❌ {ip_port}（{ip_info[ip_port]}）- 连续失败{cnt}次")
    
    # 6. 按优先级收集频道线路（域名>北京/上海/四川IP>普通IP，每个频道最多50条）
    channel_lines = {}
    priority_provinces = {"北京", "上海", "四川"}
    # 域名判断函数
    def is_domain(addr):
        ip_pattern = re.compile(r'^\d+\.\d+\.\d+\.\d+(:\d+)?$')
        if ip_pattern.match(addr):
            return False
        return '.' in addr and not addr.replace('.', '').isdigit()
    
    for ip_port in playable_ips:
        operator = ip_info.get(ip_port, "未知")
        is_domain_addr = is_domain(ip_port)
        is_priority_ip = any(prov in operator for prov in priority_provinces)
        # 遍历该IP下的所有频道
        for ch_main, url in ip_channel_groups.get(ip_port, []):
            line_key = f"{ch_main},{url}${operator}"
            if ch_main not in channel_lines:
                channel_lines[ch_main] = {"domain": [], "priority": [], "normal": []}
            # 按优先级分类
            if is_domain_addr:
                channel_lines[ch_main]["domain"].append(line_key)
            elif is_priority_ip:
                channel_lines[ch_main]["priority"].append(line_key)
            else:
                channel_lines[ch_main]["normal"].append(line_key)
    
    # 合并线路，每个频道最多保留50条
    valid_channel_lines = []
    for ch, line_dict in channel_lines.items():
        domain_lst = line_dict["domain"]
        priority_lst = line_dict["priority"]
        normal_lst = line_dict["normal"]
        # 计算各层级可取值数，总数≤50
        take_domain = min(len(domain_lst), 50)
        remain = 50 - take_domain
        take_priority = min(len(priority_lst), remain) if remain > 0 else 0
        remain = remain - take_priority
        take_normal = min(len(normal_lst), remain) if remain > 0 else 0
        # 合并线路
        selected_lines = domain_lst[:take_domain] + priority_lst[:take_priority] + normal_lst[:take_normal]
        valid_channel_lines.extend(selected_lines)
    
    # 7. 生成IPTV.txt
    beijing_now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    # 统计各类型可播放IP数
    domain_count = sum(1 for ip in playable_ips if is_domain(ip))
    bj_count = sum(1 for ip in playable_ips if "北京" in ip_info.get(ip, ""))
    sh_count = sum(1 for ip in playable_ips if "上海" in ip_info.get(ip, ""))
    sc_count = sum(1 for ip in playable_ips if "四川" in ip_info.get(ip, ""))
    
    try:
        with open(IPTV_FILE, "w", encoding="utf-8") as f:
            f.write(f"更新时间: {beijing_now}\n")
            f.write(f"可播放IP/域名共{len(playable_ips)}个（域名{domain_count}个、北京{bj_count}个、上海{sh_count}个、四川{sc_count}个）\n\n")
            # 按分类写入频道
            for category, ch_list in CHANNEL_CATEGORIES.items():
                f.write(f"{category},#genre#\n")
                for ch in ch_list:
                    for line in valid_channel_lines:
                        if line.startswith(f"{ch},"):
                            f.write(line + "\n")
                f.write("\n")
        print(f"🎯 IPTV.txt生成完成，共{len(valid_channel_lines)}条有效频道线路")
    except Exception as e:
        print(f"❌ 写入IPTV.txt失败：{e}")
    
    # 返回省份-IP映射和可播放IP，供第三阶段使用
    operator_ip_map = {}
    for ip, operator in ip_info.items():
        operator_ip_map.setdefault(operator, set()).add(ip)
    return operator_ip_map, playable_ips

# ================= 第三阶段：删除≥3次失败的IP =================
def third_stage(operator_ip_map, playable_ips):
    global ip_info
    if not operator_ip_map or not ip_info:
        print("⚠️ 无IP数据，跳过第三阶段")
        return

    print(f"\n📤 【第三阶段】开始清理IP池（连续失败≥{MAX_FAILED_TIMES}次直接删除）")
    
    failed_count = load_failed_count()
    province_map = {}
    deleted_ips = []
    
    for ip, operator in ip_info.items():
        cnt = failed_count.get(ip, 0)
        if ip in playable_ips or cnt < MAX_FAILED_TIMES:
            province_map.setdefault(operator, []).append(ip)
        else:
            deleted_ips.append((ip, operator, cnt))
    
    # 打印删除日志
    if deleted_ips:
        for ip, op, cnt in deleted_ips:
            print(f"🔴 彻底删除 IP {ip}（{op}）- 连续失败{cnt}次")
    else:
        print("✅ 暂无达到删除阈值的IP")

    # 2. 强制写入空文件占位
    for operator, ip_list in province_map.items():
        safe_fn = operator.replace("/", "_").replace("\\", "_").replace(":", "_") + ".txt"
        path = os.path.join(IP_DIR, safe_fn)
        
        try:
            # 直接覆盖写入！不管有没有IP，都强制重写文件
            with open(path, "w", encoding="utf-8") as f:
                if ip_list:
                    # 有IP：正常写入
                    for ip in sorted(set(ip_list)):
                        f.write(ip + "\n")
                else:
                    # 🔥 如果没IP，写占位符
                    f.write("# 暂无有效IP\n") 
            
            # 根据是否有IP，调整日志显示
            if ip_list:
                print(f"✅ 已重建：{operator}.txt (保留 {len(ip_list)} 个)")
            else:
                print(f"⚠️ 已置空：{operator}.txt (暂无有效IP)")
                
        except Exception as e:
            print(f"❌ 写入失败{operator}.txt: {e}")
    
    # 3. 同步清理计数文件
    all_survived_ips = set(ip for lst in province_map.values() for ip in lst)
    new_failed_count = {ip: cnt for ip, cnt in failed_count.items() if ip in all_survived_ips}
    save_failed_count(new_failed_count)
    
    print(f"🔚 第三阶段完成。")

# ================= 文件推送到GitHub =================
def push_all_files():
    print("\n🚀 开始推送更新文件到GitHub")
    try:
        # 配置Git用户信息
        os.system('git config --global user.name "github-actions"')
        os.system('git config --global user.email "github-actions@users.noreply.github.com"')
    except Exception:
        pass
    # 添加文件到暂存区
    os.system("git add ip/*.txt || true")
    os.system("git add IPTV.txt || true")
    os.system("git add 失效IP计数.json || true")
    # 提交并推送
    os.system('git commit -m "自动更新：IP池清理+频道线路+失败计数" || echo "⚠️ 暂无更新内容，无需提交"')
    os.system("git push origin main || echo '⚠️ GitHub推送失败'")
    print("📤 推送流程结束")

# ================= 主执行逻辑 =================
if __name__ == "__main__":
    # 确保基础目录存在
    os.makedirs(IP_DIR, exist_ok=True)
    os.makedirs(RTP_DIR, exist_ok=True)
    
    # 第一阶段：生成zubo.txt
    first_stage()
    # 第二阶段：检测IP+更新计数+生成IPTV.txt
    operator_ip_map, playable_ips = second_stage()
    # 第三阶段：清理≥3次失败的IP
    third_stage(operator_ip_map, playable_ips)
    # 推送文件到GitHub（必执行）
    push_all_files()
    
    print("\n🎉 本次脚本执行全部完成！")
