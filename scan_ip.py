from threading import Thread
import os
import time
import glob
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== 只提速不减量版全局配置 ====================
MAX_SCAN_DURATION = 2400    # 最大扫描时长 40 分钟
DEFAULT_MAX_WORKERS = 120     # 线程池大小（优化后）
REQUEST_TIMEOUT = 1       # 请求超时（提速关键）
PROGRESS_INTERVAL = 2000    # 进度日志间隔

def expand_ip_range(ip_str):
    ip_list = []
    parts = ip_str.split('.')
    if len(parts) != 4:
        return [ip_str]
    a_list = expand_part(parts[0])
    b_list = expand_part(parts[1])
    c_list = expand_part(parts[2])
    d_list = expand_part(parts[3])
    for a in a_list:
        for b in b_list:
            for c in c_list:
                for d in d_list:
                    ip_list.append(f"{a}.{b}.{c}.{d}")
    return ip_list

def expand_part(part):
    if '-' in part:
        start, end = part.split('-')
        return [str(i) for i in range(int(start), int(end) + 1)]
    else:
        return [part]

def read_config(config_file):
    print(f"读取配置文件：{config_file}")
    ip_configs = []
    original_lines = []
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line_num, line in enumerate(lines, 1):
            original_line = line.rstrip('\n')
            original_lines.append(original_line)
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                if "," in line:
                    parts = line.split(',')
                    ip_part_port = parts[0].strip()
                    option = int(parts[1])
                else:
                    ip_part_port = line.strip()
                    option = 12
                if ":" not in ip_part_port:
                    print(f"第{line_num}行格式错误: 缺少端口号 - {line}")
                    continue
                ip_part, port = ip_part_port.split(':')
                if '-' in ip_part:
                    expanded_ips = expand_ip_range(ip_part)
                    print(f"  第{line_num}行IP扩展: {ip_part} -> {len(expanded_ips)} 个IP")
                    for expanded_ip in expanded_ips:
                        ip_parts = expanded_ip.split('.')
                        a, b, c, d = ip_parts
                        url_end = "/status" if option >= 10 else "/stat"
                        base_ip = f"{a}.{b}.{c}.1" if option % 2 == 0 else f"{a}.{b}.1.1"
                        ip_configs.append((base_ip, port, option, url_end, line_num-1, f"{expanded_ip}:{port},{option}"))
                else:
                    ip_parts = ip_part.split('.')
                    if len(ip_parts) != 4:
                        print(f"第{line_num}行格式错误: IP地址格式不正确 - {line}")
                        continue
                    a, b, c, d = ip_parts
                    url_end = "/status" if option >= 10 else "/stat"
                    base_ip = f"{a}.{b}.{c}.1" if option % 2 == 0 else f"{a}.{b}.1.1"
                    ip_configs.append((base_ip, port, option, url_end, line_num-1, original_line))
            except Exception as e:
                print(f"第{line_num}行格式错误: {e} - {line}")
                continue
        return ip_configs, original_lines
    except Exception as e:
        print(f"读取文件错误: {e}")
        return [], []

def generate_ip_ports(ip, port, option):
    a, b, c, d = ip.split('.')
    if option == 2 or option == 12:
        c_extent = c.split('-')
        c_first = int(c_extent[0]) if len(c_extent) == 2 else int(c)
        c_last = int(c_extent[1]) + 1 if len(c_extent) == 2 else int(c) + 8  # 保持 +8，扫描总量不变
        return [f"{a}.{b}.{x}.{y}:{port}" for x in range(c_first, c_last) for y in range(1, 256)]
    elif option == 0 or option == 10:
        return [f"{a}.{b}.{c}.{y}:{port}" for y in range(1, 256)]
    else:
        c_start = max(0, int(c) - 4)
        c_end = min(256, c_start + 8)
        return [f"{a}.{b}.{x}.{y}:{port}" for x in range(c_start, c_end) for y in range(1, 256)]

def check_ip_port(ip_port, url_end):
    try:
        url = f"http://{ip_port}{url_end}"
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        if "Multi stream daemon" in resp.text or "udpxy status" in resp.text:
            return ip_port
    except:
        return None

def scan_ip_port(ip, port, option, url_end, start_time):
    valid_ip_ports = []
    ip_ports = generate_ip_ports(ip, port, option)
    if not ip_ports:
        return valid_ip_ports
    checked = [0]
    print(f"  待扫描: {len(ip_ports)} 个IP")
    with ThreadPoolExecutor(max_workers=DEFAULT_MAX_WORKERS) as executor:
        futures = {executor.submit(check_ip_port, ip_port, url_end): ip_port for ip_port in ip_ports}
        for future in as_completed(futures):
            elapsed = time.time() - start_time
            if elapsed > MAX_SCAN_DURATION:
                print("\n⚠️  扫描超时，提前终止")
                executor.shutdown(wait=False, cancel_futures=True)
                break
            result = future.result()
            if result:
                valid_ip_ports.append(result)
            checked[0] += 1
            if checked[0] % PROGRESS_INTERVAL == 0:
                print(f"  已扫描: {checked[0]}/{len(ip_ports)}")
    return valid_ip_ports

def process_config_file(config_file, start_time):
    filename = os.path.basename(config_file)
    province_name = os.path.splitext(filename)[0].replace("_config", "")
    if province_name in ["北京", "上海"]:
        province_name = f"{province_name}市"
    print(f"\n{'='*25}\n   处理: {province_name}\n{'='*25}")
    configs, original_lines = read_config(config_file)
    if not configs:
        print(f"配置文件 {filename} 中没有有效配置行")
        return []
    all_valid_ip_ports = []
    total_configs = len(configs)
    for idx, (ip, port, option, url_end, line_num, original_line) in enumerate(configs, 1):
        elapsed = time.time() - start_time
        if elapsed > MAX_SCAN_DURATION:
            print("\n⚠️  总扫描超时，跳过剩余配置行")
            break
        print(f"\n[{idx}/{total_configs}] 扫描: {original_line}")
        valid_ips = scan_ip_port(ip, port, option, url_end, start_time)
        if valid_ips:
            all_valid_ip_ports.extend(valid_ips)
            print(f"  找到 {len(valid_ips)} 个有效IP")
        else:
            print(f"  没有找到有效IP")
    return all_valid_ip_ports, province_name

def main():
    start_time = time.time()
    ip_dir = "ip_demo"
    if not os.path.exists(ip_dir):
        print(f"错误：配置目录 {ip_dir} 不存在，请先同步代码")
        return
    result_dir = "ip"
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        print(f"创建结果目录: {result_dir}")
    config_files = glob.glob(os.path.join(ip_dir, "*_config.txt"))
    if not config_files:
        print(f"在 '{ip_dir}' 目录下未找到配置文件")
        return
    print(f"找到 {len(config_files)} 个省份配置文件")
    for config_file in config_files:
        elapsed = time.time() - start_time
        if elapsed > MAX_SCAN_DURATION:
            print("\n⚠️  总扫描超时，跳过剩余省份")
            break
        valid_ip_ports, province_name = process_config_file(config_file, start_time)
        if valid_ip_ports:
            valid_ip_ports = sorted(set(valid_ip_ports))
            result_filename = f"{province_name}.txt"
            result_path = os.path.join(result_dir, result_filename)
            existing_ips = set()
            if os.path.exists(result_path):
                try:
                    with open(result_path, 'r', encoding='utf-8') as f:
                        existing_ips = set(line.strip() for line in f if line.strip())
                except:
                    existing_ips = set()
            all_ips = sorted(set(list(existing_ips) + valid_ip_ports))
            new_count = len(all_ips) - len(existing_ips)
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_ips))
            print(f"{province_name}: 保存 {len(all_ips)} 个有效IP (新增 {new_count} 个)")
        else:
            print(f"{province_name}: 没有找到有效IP")
        print("-" * 50)
    elapsed_total = time.time() - start_time
    print(f"\n✅ 扫描完成！总耗时: {elapsed_total:.2f} 秒")
    print(f"📁 结果保存在 {result_dir}/ 目录下")

if __name__ == "__main__":
    main()
