import argparse
import subprocess
import dns.resolver
import requests
import pymysql
import time
import re
from pathlib import Path
from collections import deque
import datetime

# 数据库配置（直接定义，和你的风格一致）
db_user = "qiyelist"
db_name = "qiyelist"
db_pass = "123456"
db = pymysql.connect(host='localhost', user=db_user, password=db_pass, database=db_name, charset='utf8')
table_name1 = ""  # 企业列表数据表（从命令行传）
table_name2 = ""  # 资产列表数据表（从命令行传）
output_dir = "subdomain_reports"  # 结果输出目录
# 正则：判断是否为IPv4地址（避免对IP扫子域名）
IP_PATTERN = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')


# ---------------------- 新增：IP-api请求频率控制（每分钟45次） ----------------------
class IPCallLimiter:
    def __init__(self, max_calls_per_minute=45):
        self.max_calls = max_calls_per_minute  # 每分钟最大请求数（ip-api免费版限制）
        self.call_timestamps = deque()  # 存储每次请求的时间戳

    def wait_for_available(self):
        """确保当前请求数不超过限制，若超则等待到下一个可用窗口"""
        now = datetime.datetime.now()
        # 1. 移除1分钟前的请求记录（过期的“令牌”）
        while self.call_timestamps and (now - self.call_timestamps[0]).total_seconds() > 60:
            self.call_timestamps.popleft()

        # 2. 若当前请求数已达上限，计算需要等待的时间（到下一个过期记录的时间）
        if len(self.call_timestamps) >= self.max_calls:
            next_available_time = self.call_timestamps[0] + datetime.timedelta(seconds=60)
            wait_seconds = (next_available_time - now).total_seconds()
            if wait_seconds > 0:
                print(f"⚠️ IP归属地查询请求已达每分钟上限（45次），需等待 {round(wait_seconds, 1)} 秒")
                time.sleep(wait_seconds)

        # 3. 记录当前请求时间戳（获取“令牌”）
        self.call_timestamps.append(datetime.datetime.now())


# 初始化频率控制器（全局唯一，确保所有查询共享限制）
ip_api_limiter = IPCallLimiter(max_calls_per_minute=45)


# -----------------------------------------------------------------------------------

def start():
    """主入口：获取目标（域名/IP）-> 处理目标"""
    # 1. 从数据库获取待处理目标（域名或IP）
    targets = get_target()
    if targets == 0:
        print("暂无待处理目标（域名/IP）")
        return
    # 2. 处理每个目标（顺序执行）
    print(f"共获取到 {len(targets)} 个待处理目标")
    process_all_targets(targets)


def get_target():
    sql = f"""
        SELECT code, qy_domain 
        FROM qiye_{table_name1} 
        WHERE qy_domain <> '' 
          AND qy_domain IS NOT NULL
          AND flag=0
    """
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result if result else 0
    except Exception as e:
        print(f"获取目标失败：{str(e)}")
        cursor.close()
        return 0


def process_all_targets(targets):
    """处理所有目标：先判断是IP还是域名，再分别处理"""
    # 初始化输出目录（不存在则创建）
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    # 顺序处理每个目标
    success_count = 0
    for i, (code, target) in enumerate(targets, 1):
        print(f"\n----- 处理第 {i}/{len(targets)} 个目标：{target}（编号：{code}）-----")
        try:
            # 核心：判断目标是IP还是域名，分开处理
            if is_ip(target):
                # 1. 若是IP：不扫子域名，直接查IP归属地+HTTP/HTTPS
                target_info = process_ip(target)
            else:
                # 2. 若是域名：扫子域名+兜底+查信息+HTTP/HTTPS
                subdomains = run_subfinder(target)
                subdomains = add_fallback_subdomains(subdomains, target)
                print(f"去重+兜底后，共 {len(subdomains)} 个子域名")
                target_info = get_subdomain_info(subdomains)
            # 3. 插入数据库（保留你的去重逻辑）
            insert(code, target_info)
            # 4. 更新状态（如果需要，保留你的原有逻辑）
            # update_domain_status(code)
            success_count += 1
            print(f"✅ 目标 {target} 处理完成")
        except Exception as e:
            print(f"❌ 目标 {target} 处理失败：{str(e)}")
    # 处理完成后统计
    print(f"\n===== 处理结束 =====")
    print(f"总目标数：{len(targets)} | 成功：{success_count} | 失败：{len(targets) - success_count}")
    updateFlag(code)
def updateFlag(code):
    s = f"update qiye_{table_name1} set flag=1 where code='{code}'"
    c = db.cursor()
    c.execute(s)
    db.commit()
    c.close()

def is_ip(target):
    """判断目标是否为IPv4地址"""
    match = IP_PATTERN.match(target)
    if not match:
        return False
    # 验证每个段是否在0-255范围内（避免无效IP格式）
    return all(0 <= int(part) <= 255 for part in match.groups())


def process_ip(ip):
    """处理IP地址：查归属地 + 检查HTTP(80)/HTTPS(443)"""
    ip_info = []
    # 1. 查IP归属地（先过频率控制，再重试）
    country, province, city = get_ip_location_with_retry_and_limit(ip)
    gsd = f"{country}-{province}-{city}".replace(",", "").replace(" ", "_")
    # 2. 检查HTTP和HTTPS状态（超时3秒，避免卡太久）
    http_status = check_http_https(ip, 80, is_https=False)
    https_status = check_http_https(ip, 443, is_https=True)
    # 3. 组装信息（和子域名信息格式对齐，方便插入数据库）
    ip_info.append([ip, ip, gsd, http_status, https_status,
                    "有效" if (http_status.startswith(("2", "3")) or https_status.startswith(("2", "3"))) else "无效"])
    return ip_info


def run_subfinder(domain):
    """调用subfinder扫描子域名（保留你的原有逻辑）"""
    try:
        result = subprocess.run(
            ["subfinder", "-all", "-d", domain, "-silent"],
            capture_output=True, text=True, timeout=300  # 300秒超时
        )
        subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        print(f"subfinder 扫描到 {len(subdomains)} 个子域名")
        return subdomains
    except FileNotFoundError:
        raise Exception("未找到subfinder！请先安装并添加到环境变量")
    except subprocess.TimeoutExpired:
        raise Exception("subfinder扫描超时（超过300秒）")
    except Exception as e:
        raise Exception(f"subfinder执行失败：{str(e)}")


def add_fallback_subdomains(subdomains, main_domain):
    """加兜底：确保主域名和www子域名存在（保留你的原有逻辑）"""
    subdomain_set = set(subdomains)
    subdomain_set.add(main_domain)
    subdomain_set.add(f"www.{main_domain}")
    return list(subdomain_set)


def get_subdomain_info(subdomains):
    """获取子域名信息：DNS解析 + 归属地（带频率控制） + HTTP/HTTPS检查"""
    info_list = []
    for sub in subdomains:
        # 查DNS解析（IP）
        ips = check_dns(sub)
        if ips:
            for ip in ips:
                # 1. 查归属地（先过频率控制，再重试）
                country, province, city = get_ip_location_with_retry_and_limit(ip)
                gsd = f"{country}-{province}-{city}".replace(",", "").replace(" ", "_")
                # 2. 查HTTP/HTTPS状态
                http_status = check_http_https(ip, 80, is_https=False)
                https_status = check_http_https(ip, 443, is_https=True)
                # 3. 组装信息
                info_list.append([sub, ip, gsd, http_status, https_status, "有效" if (
                            http_status.startswith(("2", "3")) or https_status.startswith(("2", "3"))) else "无效"])
        else:
            # 解析失败不插入（保留你的原有逻辑）
            pass
    return info_list


def check_http_https(ip, port, is_https):
    """检查HTTP/HTTPS服务状态：返回状态码或错误信息"""
    scheme = "https" if is_https else "http"
    url = f"{scheme}://{ip}:{port}"
    try:
        resp = requests.get(url, timeout=3, allow_redirects=False)
        return str(resp.status_code)
    except requests.exceptions.ConnectTimeout:
        return "连接超时"
    except requests.exceptions.ConnectionError:
        return "连接失败"
    except Exception as e:
        return str(e)[:10]


def check_dns(subdomain):
    """检查子域名DNS解析（保留你的原有逻辑）"""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10
        answers = resolver.resolve(subdomain, 'A')
        return [str(rdata) for rdata in answers]
    except Exception:
        return []


# ---------------------- 修改：归属地查询增加“频率控制+重试” ----------------------
def get_ip_location_with_retry_and_limit(ip, max_retries=2):
    """查询IP归属地（先过频率控制，再重试，避免限流）"""
    for retry in range(max_retries + 1):
        # 关键：每次查询前先检查频率限制，超了就等待
        ip_api_limiter.wait_for_available()

        try:
            resp = requests.get(
                f"http://ip-api.com/json/{ip}?lang=zh-CN",
                timeout=5
            )
            # 额外处理ip-api的限流响应（HTTP 429）
            if resp.status_code == 429:
                print(f"⚠️ IP {ip} 查询触发限流（HTTP 429），将重试")
                # 限流时等待10秒再重试（避免反复触发）
                time.sleep(10)
                continue

            data = resp.json()
            if data.get("status") == "success":
                return (
                    data.get("country", "未知"),
                    data.get("regionName", "未知"),
                    data.get("city", "未知")
                )
        except Exception as e:
            print(f"第{retry + 1}次查询IP {ip} 归属地失败: {str(e)}")

        # 非限流的普通失败，重试前等待1秒
        if retry < max_retries:
            time.sleep(1)

    # 多次重试后仍失败，返回空值（后续过滤）
    return None, None, None


def insert(code, target_info):
    """插入数据库：过滤归属地全空的记录（保留你的原有逻辑）"""
    for d in target_info:
        sub_domain = d[0]  # 子域名/IP
        ip = d[1]  # IP
        gsd = d[2]  # 归属地
        http_status = d[3]  # HTTP状态
        https_status = d[4]  # HTTPS状态

        # 过滤归属地为"None-None-None"的记录
        if gsd == "None-None-None":
            print(f"❌ IP {ip} 归属地查询失败，已过滤")
            continue

        if chkData(code, ip):
            pass
        else:
            if http_status == '连接超时' and https_status == '连接超时':
                pass
            else:
                if gsd != '未知-未知-未知':
                    inputData(code, sub_domain, ip, gsd, http_status, https_status)


def inputData(code, sub_domain, ip, gsd, http_status, https_status):
    """插入数据（保留你的原有逻辑）"""
    sql = (f"INSERT INTO `qiye_{table_name2}_domain_zichan` "
           f"(`code`, `domain`, `ip`, `guishudi`, `http_status`, `https_status`) "
           f"VALUES ('{code}', '{sub_domain}', '{ip}', '{gsd}', '{http_status}', '{https_status}')")
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except Exception as e:
        print(f"插入数据失败：{str(e)} | SQL：{sql[:100]}")
        db.rollback()
        cursor.close()


def chkData(code, ip):
    """去重检查（保留你的原有逻辑）"""
    sql = f"select * from qiye_{table_name2}_domain_zichan where code='{code}' and ip='{ip}'"
    cursor = db.cursor()
    cursor.execute(sql)
    data = cursor.fetchone()
    cursor.close()
    return True if data else False


def update_domain_status(code):
    """更新状态（保留你的原有逻辑）"""
    sql = f"UPDATE qiye_{table_name1} SET domain_status = 1 WHERE code = '{code}'"
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        db.commit()
        cursor.close()
    except Exception as e:
        print(f"更新域名状态失败：{str(e)}")
        db.rollback()
        cursor.close()


if __name__ == '__main__':
    # 解析命令行参数（保留你的原有风格）
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', required=True, type=str, help='企业列表数据表名（如daqing）')
    parser.add_argument('-z', required=True, type=str, help='资产列表数据表名（如daqing）')
    args = parser.parse_args()
    # 给全局变量赋值
    table_name1 = args.t
    table_name2 = args.z
    # 启动程序
    start()
    # 关闭数据库连接
    db.close()