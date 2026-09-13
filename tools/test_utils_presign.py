"""presign_get_url_day_grid 与 Go 侧实现的字节级一致性测试。

golden 向量由 ai-friend-server internal/utils/oss_presign.go 的
presignGetURLV4 生成（固定 sign_time=2026-09-13T00:00:00Z、expires=90000），
两边算法/编码必须逐字节一致，否则浏览器按完整 URL 做缓存键会互相 miss。

直接运行：python3 tools/test_utils_presign.py（无 pytest 依赖）。
"""
import os
import sys
from datetime import datetime, timedelta, timezone

# 绕开 tools/__init__.py（其会 import dify_plugin，插件运行时之外不可用），
# 直接加载同目录的 utils 模块做纯算法测试
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (  # noqa: E402
    _coerce_sign_expired,
    _endpoint_host,
    _region_from_endpoint,
    presign_get_url_day_grid,
)

FIXED_TIME = datetime(2026, 9, 13, 0, 0, 0, tzinfo=timezone.utc)

# key → Go 侧签出的期望 URL（AKIDtest123/SKtest456, app-pic-temp, cn-beijing）
GOLDEN = {
    "chat/simple.jpg":
        "https://app-pic-temp.oss-cn-beijing.aliyuncs.com/chat%2Fsimple.jpg"
        "?x-oss-credential=AKIDtest123%2F20260913%2Fcn-beijing%2Foss%2Faliyun_v4_request"
        "&x-oss-date=20260913T000000Z&x-oss-expires=90000"
        "&x-oss-signature=d06e6f8095a8661dbef37d67b6f960fb899c621d284910f639af6c628a12f05e"
        "&x-oss-signature-version=OSS4-HMAC-SHA256",
    "avatar/user1000120/20260713/1783913999_51e1b9a1.jpg":
        "https://app-pic-temp.oss-cn-beijing.aliyuncs.com/avatar%2Fuser1000120%2F20260713%2F1783913999_51e1b9a1.jpg"
        "?x-oss-credential=AKIDtest123%2F20260913%2Fcn-beijing%2Foss%2Faliyun_v4_request"
        "&x-oss-date=20260913T000000Z&x-oss-expires=90000"
        "&x-oss-signature=5cd717fb447b66f0be4709722afd92a876268fd5d9d1284738055d16f9c49390"
        "&x-oss-signature-version=OSS4-HMAC-SHA256",
    "chat/中文 图 (1).png":
        "https://app-pic-temp.oss-cn-beijing.aliyuncs.com/chat%2F%E4%B8%AD%E6%96%87%20%E5%9B%BE%20%281%29.png"
        "?x-oss-credential=AKIDtest123%2F20260913%2Fcn-beijing%2Foss%2Faliyun_v4_request"
        "&x-oss-date=20260913T000000Z&x-oss-expires=90000"
        "&x-oss-signature=bc05d6f6d41fcf1697039132b9a77d943da5e00c1fe83254bf47846f7ce3cd6c"
        "&x-oss-signature-version=OSS4-HMAC-SHA256",
    "chat/plus+space~tilde._-dash.jpg":
        "https://app-pic-temp.oss-cn-beijing.aliyuncs.com/chat%2Fplus%2Bspace~tilde._-dash.jpg"
        "?x-oss-credential=AKIDtest123%2F20260913%2Fcn-beijing%2Foss%2Faliyun_v4_request"
        "&x-oss-date=20260913T000000Z&x-oss-expires=90000"
        "&x-oss-signature=4ef20fb547afa58877f25abd7915d08b9a605df538cef147a07ef1477ad62ca7"
        "&x-oss-signature-version=OSS4-HMAC-SHA256",
}

failures = []

# 1. golden 字节级一致（含中文/空格/加号/括号等编码边界）
for key, expected in GOLDEN.items():
    got = presign_get_url_day_grid(
        "AKIDtest123", "SKtest456", "app-pic-temp", key,
        "https://oss-cn-beijing.aliyuncs.com", sign_expired=3600,
        sign_time=FIXED_TIME)
    if got != expected:
        failures.append(f"golden mismatch key={key!r}\n  go  : {expected}\n  py  : {got}")

# 2. 网格确定性：同日任意两个时刻签出的 URL 相同（含跨时区输入）
t1 = datetime(2026, 9, 13, 8, 30, 0, tzinfo=timezone.utc)
t2 = datetime(2026, 9, 13, 23, 59, 59, tzinfo=timezone.utc)
u1 = presign_get_url_day_grid("a", "b", "bk", "k/x.jpg", "oss-cn-beijing.aliyuncs.com", sign_time=t1)
u2 = presign_get_url_day_grid("a", "b", "bk", "k/x.jpg", "oss-cn-beijing.aliyuncs.com", sign_time=t2)
if u1 != u2:
    failures.append(f"same-day resign differs:\n  {u1}\n  {u2}")

# 北京时间 9/14 02:00 = UTC 9/13 18:00 → 仍属同一 UTC 日，应与 u1 相同
t3 = datetime(2026, 9, 14, 2, 0, 0, tzinfo=timezone(timedelta(hours=8)))
u3 = presign_get_url_day_grid("a", "b", "bk", "k/x.jpg", "oss-cn-beijing.aliyuncs.com", sign_time=t3)
if u3 != u1:
    failures.append(f"beijing-time same UTC day differs:\n  {u1}\n  {u3}")

# 3. UTC 日切后换新 URL（有效期随之滚动）
u4 = presign_get_url_day_grid("a", "b", "bk", "k/x.jpg", "oss-cn-beijing.aliyuncs.com",
                              sign_time=datetime(2026, 9, 14, 0, 0, 1, tzinfo=timezone.utc))
if u4 == u1:
    failures.append("cross-day URL should differ")

# 4. expires 封顶：sign_expired 超 518400 时封顶 604800
u5 = presign_get_url_day_grid("a", "b", "bk", "k/x.jpg", "oss-cn-beijing.aliyuncs.com", sign_expired=10**9)
if "x-oss-expires=604800" not in u5:
    failures.append(f"expires not clamped: {u5}")

# 5. endpoint 解析与 region 推导
cases = [
    ("oss-cn-beijing.aliyuncs.com", "cn-beijing"),
    ("https://oss-cn-beijing.aliyuncs.com", "cn-beijing"),
    ("http://oss-cn-hangzhou-internal.aliyuncs.com", "cn-hangzhou"),
    ("oss-cn-beijing.aliyuncs.com:8080", None),  # 带端口=非标准形态，回退
    ("cdn.example.com", None),                    # 自定义域名，回退
]
for ep, want in cases:
    got = _region_from_endpoint(ep)
    if got != want:
        failures.append(f"region({ep!r}) = {got!r}, want {want!r}")
if _endpoint_host("https://oss-cn-beijing.aliyuncs.com/path/x") != "oss-cn-beijing.aliyuncs.com":
    failures.append("endpoint_host path strip broken")

# 6. sign_expired 容错
for bad, want in [("", 3600), (None, 3600), ("abc", 3600), (0, 3600), (-5, 3600), ("7200", 7200), (86400, 86400)]:
    got = _coerce_sign_expired(bad)
    if got != want:
        failures.append(f"coerce({bad!r}) = {got}, want {want}")

# 7. 自定义域名回退 None（调用方应改走 oss2.sign_url）
if presign_get_url_day_grid("a", "b", "bk", "k.jpg", "cdn.example.com") is not None:
    failures.append("custom domain should return None")

if failures:
    print(f"FAIL ({len(failures)}):")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("all presign golden/determinism tests passed")
