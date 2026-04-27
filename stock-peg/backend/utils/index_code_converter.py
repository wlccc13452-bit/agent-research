"""指数代码格式转换工具"""


def normalize_index_code(code: str) -> dict:
    """
    标准化指数代码格式
    
    支持的输入格式:
    - "000001.SH" (带后缀，前端传递格式)
    - "sh000001" (带前缀)
    - "000001" (纯代码)
    
    返回: {
        'pure_code': '000001',      # 纯代码
        'market': 'sh',              # 市场（sh/sz）
        'akshare_code': 'sh000001', # Akshare格式
        'tencent_code': 'sh000001', # 腾讯API格式
        'original': '000001.SH'     # 原始代码
    }
    """
    result = {
        'pure_code': None,
        'market': None,
        'akshare_code': None,
        'tencent_code': None,
        'original': code
    }
    
    if '.' in code:
        # 格式: 000001.SH
        pure_code, suffix = code.split('.')
        market = suffix.lower()
    elif code.startswith(('sh', 'sz')):
        # 格式: sh000001
        market = code[:2]
        pure_code = code[2:]
    else:
        # 纯代码: 000001
        pure_code = code
        # 根据代码判断市场
        if code.startswith(('0', '5', '6')):
            market = 'sh'
        else:
            market = 'sz'
    
    result['pure_code'] = pure_code
    result['market'] = market
    result['akshare_code'] = f"{market}{pure_code}"
    result['tencent_code'] = f"{market}{pure_code}"
    
    return result


def normalize_index_codes(codes: list) -> list:
    """批量转换指数代码"""
    return [normalize_index_code(code) for code in codes]


def get_akshare_code(code: str) -> str:
    """
    快速获取Akshare格式的代码
    
    Args:
        code: 原始代码（如 000001.SH 或 sh000001 或 000001）
    
    Returns:
        Akshare格式的代码（如 sh000001）
    """
    normalized = normalize_index_code(code)
    return normalized['akshare_code']


def get_pure_code(code: str) -> str:
    """
    快速获取纯代码
    
    Args:
        code: 原始代码（如 000001.SH 或 sh000001 或 000001）
    
    Returns:
        纯代码（如 000001）
    """
    normalized = normalize_index_code(code)
    return normalized['pure_code']
