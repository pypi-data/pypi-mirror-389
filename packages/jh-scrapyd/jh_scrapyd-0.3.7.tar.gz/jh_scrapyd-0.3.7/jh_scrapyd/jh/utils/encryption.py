import json
import hmac
import hashlib
from jh_scrapyd import get_config



class ApiSign:
    API_KEY = get_config(option="signature_key", section="api")

    @classmethod
    def verify_sign(cls, params: dict) -> bool:
        sign = params.pop("sign", None)
        return sign == cls.create_sign(params)

    @classmethod
    def create_sign(cls, params: dict) -> str:
        # 移除 sign 字段
        params = {k: v for k, v in params.items() if k != "sign"}

        # 排序
        items = sorted(params.items(), key=lambda x: x[0])

        # 拼接
        arr = []
        for k, v in items:
            arr.append(f"{k}={cls.canonical_value(v)}")
        sign_str = "&".join(arr)

        # 计算 HMAC-SHA256
        api_key = cls.API_KEY
        signature = hmac.new(api_key.encode("utf-8"), sign_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return signature

    @classmethod
    def canonical_value(cls, value):
        """将数组/对象转为规范化 JSON"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if value is None:
            return ""  # 和 PHP 保持一致
        return str(value)

    @classmethod
    def set_api_key(cls, api_key: str):
        cls.API_KEY = api_key