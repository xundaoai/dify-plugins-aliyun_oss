import hashlib
import hmac
import os
import re
from datetime import datetime, timezone
from typing import Any, Union
from urllib.parse import quote as _url_quote

# 内容类型到扩展名的映射表（带点号）
CONTENT_TYPE_TO_EXTENSION_WITH_DOT = {
    # 图片格式
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/tiff': '.tiff',
    'image/x-icon': '.ico',
    'image/heic': '.heic',
    
    # 音频格式
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
    'audio/ogg': '.ogg',
    'audio/flac': '.flac',
    'audio/aac': '.aac',
    'audio/m4a': '.m4a',
    'audio/mp4': '.mp4',
    
    # 视频格式
    'video/mp4': '.mp4',
    'video/mov': '.mov',
    'video/avi': '.avi',
    'video/x-msvideo': '.avi',
    'video/x-ms-wmv': '.wmv',
    'video/webm': '.webm',
    'video/mpeg': '.mpg',
    'video/quicktime': '.mov',
    'video/x-matroska': '.mkv',
    
    # 文档格式
    'application/pdf': '.pdf',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/rtf': '.rtf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/vnd.oasis.opendocument.presentation': '.odp',
    
    # 文本格式
    'text/plain': '.txt',
    'text/csv': '.csv',
    'application/json': '.json',
    'application/xml': '.xml',
    'text/xml': '.xml',
    'text/html': '.html',
    'text/css': '.css',
    'application/javascript': '.js',
    'text/markdown': '.md',
    
    # 压缩格式
    'application/zip': '.zip',
    'application/gzip': '.gz',
    'application/x-rar-compressed': '.rar',
    'application/x-7z-compressed': '.7z',
    'application/x-tar': '.tar',
    'application/x-bzip2': '.bz2',
    
    # 可执行文件
    'application/x-msdownload': '.exe',
    'application/vnd.android.package-archive': '.apk',
    'application/java-archive': '.jar',
    'application/x-shockwave-flash': '.swf',
    
    # 代码文件
    'text/x-python': '.py',
    'text/x-java-source': '.java',
    'text/x-c++src': '.cpp',
    'text/x-csrc': '.c',
    'text/x-csharp': '.cs',
    'text/x-ruby': '.rb',
    'text/x-go': '.go',
    'text/x-rustsrc': '.rs',
    'text/x-swift': '.swift',
    'application/x-php': '.php'
}

# 内容类型到扩展名的映射表（不带点号）
CONTENT_TYPE_TO_EXTENSION = {k: v[1:] for k, v in CONTENT_TYPE_TO_EXTENSION_WITH_DOT.items()}


def get_file_type_from_content_type(content_type: str) -> str:
    """
    根据内容类型获取文件类型（不带点号）
    
    Args:
        content_type: 文件内容类型，如 'image/jpeg'
        
    Returns:
        文件类型，如 'jpg'，如果无法匹配则返回 'unknown'
    """
    # 直接匹配内容类型
    if content_type in CONTENT_TYPE_TO_EXTENSION:
        return CONTENT_TYPE_TO_EXTENSION[content_type]
    
    # 尝试匹配内容类型的前缀（例如 'application/vnd.openxmlformats-officedocument.'）
    for ct, ext in CONTENT_TYPE_TO_EXTENSION.items():
        if content_type.startswith(ct):
            return ext
    
    return "unknown"


def get_extension_from_content_type(content_type: str) -> str:
    """
    根据内容类型获取文件扩展名（带点号）
    
    Args:
        content_type: 文件内容类型，如 'image/jpeg'
        
    Returns:
        文件扩展名，如 '.jpg'，如果无法匹配则返回 '.dat'
    """
    # 直接匹配内容类型
    if content_type in CONTENT_TYPE_TO_EXTENSION_WITH_DOT:
        return CONTENT_TYPE_TO_EXTENSION_WITH_DOT[content_type]
    
    # 尝试匹配内容类型的前缀（例如 'application/vnd.openxmlformats-officedocument.'）
    for ct, ext in CONTENT_TYPE_TO_EXTENSION_WITH_DOT.items():
        if content_type.startswith(ct):
            return ext
    
    return ".dat"


def get_file_type(file: Any) -> str:
    """
    获取文件类型（不带点号）
    
    Args:
        file: 文件对象
        
    Returns:
        文件类型，如 'jpg'，如果无法匹配则返回 'unknown'
    """
    # 1. 首先尝试从文件名获取扩展名
    if hasattr(file, 'name') and file.name:
        _, extension = os.path.splitext(file.name)
        if extension:
            return extension.lower()[1:]  # 移除点号
    
    # 2. 如果无法从文件名获取，尝试从file.filename获取
    if hasattr(file, 'filename') and file.filename:
        _, extension = os.path.splitext(file.filename)
        if extension:
            return extension.lower()[1:]  # 移除点号
    
    # 3. 如果仍然无法获取，尝试从文件内容类型推断
    if hasattr(file, 'content_type') and file.content_type:
        return get_file_type_from_content_type(file.content_type)
    
    return "unknown"


def get_file_extension(file: Any) -> str:
    """
    获取文件扩展名（带点号）
    
    Args:
        file: 文件对象
        
    Returns:
        文件扩展名，如 '.jpg'，如果无法匹配则返回 '.dat'
    """
    # 1. 首先尝试从文件名获取扩展名
    if hasattr(file, 'name') and file.name:
        _, extension = os.path.splitext(file.name)
        if extension:
            return extension.lower()  # 确保是小写
    
    # 2. 如果无法从文件名获取，尝试从file.filename获取
    if hasattr(file, 'filename') and file.filename:
        _, extension = os.path.splitext(file.filename)
        if extension:
            return extension.lower()  # 确保是小写
    
    # 3. 如果仍然无法获取，尝试从文件内容类型推断
    if hasattr(file, 'content_type') and file.content_type:
        return get_extension_from_content_type(file.content_type)

    return ".dat"


# OSS 支持的存储类型（键为小写，值为 OSS API 要求的写法）
STORAGE_CLASSES = {
    'standard': 'Standard',
    'ia': 'IA',
    'archive': 'Archive',
    'coldarchive': 'ColdArchive',
}

# 默认存储类型：标准存储
DEFAULT_STORAGE_CLASS = 'Standard'

# 上传对象统一携带的浏览器缓存策略：内容不可变（key 含时间戳），
# 允许客户端缓存 7 天；桶为私有读，故用 private 而非 public
DEFAULT_CACHE_CONTROL = 'private, max-age=604800'


def get_upload_headers(storage_class: Any) -> dict:
    """
    构建上传请求头（存储类型 + 浏览器缓存策略）

    Args:
        storage_class: 存储类型，如 'Standard'、'IA'，大小写不敏感；
                       非法值一律回退为标准存储，避免上传失败

    Returns:
        请求头字典，如 {'x-oss-storage-class': 'Standard',
                       'Cache-Control': 'private, max-age=604800'}
    """
    canonical = STORAGE_CLASSES.get(str(storage_class or '').strip().lower())
    return {
        'x-oss-storage-class': canonical or DEFAULT_STORAGE_CLASS,
        'Cache-Control': DEFAULT_CACHE_CONTROL,
    }


# ==================== 预签名 URL：UTC 自然日网格（与 ai-friend-server Go 侧对齐） ====================

# OSS V4 预签名 URL 的有效期上限（秒）
OSS_V4_MAX_EXPIRES = 604800

# 网格额外加成：一个自然日，保证「UTC 日末最差时刻起至少还剩 sign_expired 秒」
_DAY_GRID_EXTRA_SECONDS = 86400

# sign_expired 参数缺省/非法时的回退值（与工具 yaml 宣称的默认一致）
_DEFAULT_SIGN_EXPIRED = 3600

_ENDPOINT_SCHEME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://')
_REGION_RE = re.compile(r'^oss-([a-z0-9-]+?)(?:-internal)?\.aliyuncs\.com$')


def _endpoint_host(endpoint):
    """endpoint → host：剥掉 scheme 与路径，兼容 http(s):// 前缀写法。"""
    ep = str(endpoint or '').strip()
    m = _ENDPOINT_SCHEME_RE.match(ep)
    if m:
        ep = ep[m.end():]
    return ep.split('/', 1)[0].strip()


def _region_from_endpoint(endpoint):
    """标准 endpoint → region（oss-cn-beijing.aliyuncs.com → cn-beijing，兼容 -internal）。

    自定义域名推不出 region 时返回 None（V4 签名必须携带 region，调用方回退旧签名）。
    """
    m = _REGION_RE.match(_endpoint_host(endpoint))
    return m.group(1) if m else None


def _coerce_sign_expired(sign_expired):
    """LLM 表单参数 → 合法秒数：空/非数字/非正数一律回退默认 3600。"""
    try:
        value = int(sign_expired)
    except (TypeError, ValueError):
        return _DEFAULT_SIGN_EXPIRED
    return value if value > 0 else _DEFAULT_SIGN_EXPIRED


def presign_get_url_day_grid(access_key_id, access_key_secret, bucket_name, object_key,
                             endpoint, sign_expired=_DEFAULT_SIGN_EXPIRED,
                             use_https=True, sign_time=None):
    """生成签名时刻固定在 UTC 自然日零点的 V4 预签名 GET URL。

    与后端 ai-friend-server 的 internal/utils/oss_presign.go（presignGetURLV4
    + GeneratePresignedURL 网格化）逐字节对齐：
    - 签名时刻固定为当前 UTC 自然日零点（可用 sign_time 注入便于测试），
      同一天内同 key 重复生成的 URL 完全一致——浏览器 HTTP 缓存以完整 URL
      （含签名 query）为键，URL 稳定即命中缓存，重签不再回源；
    - 有效期 = 网格零点起 sign_expired + 86400 秒（上限 604800），即从当前
      时刻起最少仍有 sign_expired 秒，一天内不失效；
    - 两边使用相同 AK/endpoint 时，本函数与 Go 侧签出的 URL 字节级相同
      （golden 向量见 test_utils_presign.py）。

    不支持 STS 临时凭证（无 x-oss-security-token 参与签名）。
    endpoint 推不出 region（自定义域名）时返回 None，调用方回退 oss2.sign_url。
    """
    region = _region_from_endpoint(endpoint)
    if not region:
        return None

    seconds = _coerce_sign_expired(sign_expired)
    expires = min(seconds + _DAY_GRID_EXTRA_SECONDS, OSS_V4_MAX_EXPIRES)

    host = f"{bucket_name}.{_endpoint_host(endpoint)}"
    if sign_time is None:
        sign_time = datetime.now(timezone.utc)
    sign_time = sign_time.astimezone(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    str_day = sign_time.strftime('%Y%m%d')
    sign_date = sign_time.strftime('%Y%m%dT%H%M%SZ')

    def esc(value):
        # 等价 Go url.QueryEscape + "+"→"%20"：unreserved（字母数字 -_.~）外全部 %XX
        return _url_quote(str(value), safe='')

    # 规范化请求：GET / 规范化URI（斜杠字面量）/ 规范化查询串 / 空头 / 空附加头 / UNSIGNED-PAYLOAD
    canonical_resource = f"/{bucket_name}/{_url_quote(object_key, safe='/')}"
    credential = f"{access_key_id}/{str_day}/{region}/oss/aliyun_v4_request"
    canonical_query = "&".join([
        "x-oss-credential=" + esc(credential),
        "x-oss-date=" + esc(sign_date),
        "x-oss-expires=" + esc(expires),
        "x-oss-signature-version=" + esc("OSS4-HMAC-SHA256"),
    ])
    canonical_request = ("GET\n" + canonical_resource + "\n" + canonical_query
                         + "\n\n\n" + "UNSIGNED-PAYLOAD")

    scope = f"{str_day}/{region}/oss/aliyun_v4_request"
    string_to_sign = ("OSS4-HMAC-SHA256\n" + sign_date + "\n" + scope + "\n"
                      + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest())

    def _hmac(key, data):
        return hmac.new(key, data.encode('utf-8'), hashlib.sha256).digest()

    signing_key = _hmac(("aliyun_v4" + access_key_secret).encode('utf-8'), str_day)
    signing_key = _hmac(signing_key, region)
    signing_key = _hmac(signing_key, "oss")
    signing_key = _hmac(signing_key, "aliyun_v4_request")
    signature = _hmac(signing_key, string_to_sign).hex()

    # 最终 URL：查询参数按 x-oss-credential/date/expires/signature/signature-version 排序（与 Go 侧一致），
    # 路径中斜杠保持 %2F（OSS 服务端按规范化形式归一化后验签，两种写法等价且可用）
    query = "&".join([
        "x-oss-credential=" + esc(credential),
        "x-oss-date=" + esc(sign_date),
        "x-oss-expires=" + esc(expires),
        "x-oss-signature=" + signature,
        "x-oss-signature-version=" + esc("OSS4-HMAC-SHA256"),
    ])
    scheme = 'https' if use_https else 'http'
    return f"{scheme}://{host}/{_url_quote(object_key, safe='')}?{query}"