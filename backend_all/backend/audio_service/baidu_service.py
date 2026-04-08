import base64
import json

import requests

from backend.config import Config


def get_access_token():
    """
    获取百度API的访问令牌
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": Config.API_KEY,
        "client_secret": Config.SECRET_KEY
    }

    try:
        response = requests.post(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()

        if "access_token" in result:
            return result["access_token"]
        else:
            print(f"获取token失败: {result}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"请求token失败: {e}")
        return None
    except Exception as e:
        print(f"获取token异常: {e}")
        return None


def recognize_speech(audio_base64, filename):
    """
    调用百度语音识别API
    """
    try:
        # 获取访问令牌
        # token = get_access_token()
        # print(token)
        token = Config.TOKEN
        if not token:
            return {
                'success': False,
                'error': '无法获取API访问令牌'
            }

        # 百度语音识别API URL
        url = "https://vop.baidu.com/pro_api"


        # 准备请求数据
        payload = json.dumps({
            "format": "pcm",  # 音频格式
            "rate": 16000,  # 采样率
            "channel": 1,  # 声道数
            "cuid": "cRaXD8PFy8u2wYO4fQzt0UPgfemfXEvj",  # 用户标识
            "dev_pid": 80001,  # 语言模型
            "speech": audio_base64,  # 音频数据base64
            "len": len(base64.b64decode(audio_base64)),  # 音频数据长度
            "token": token
        }, ensure_ascii=False)

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # 调用百度API
        response = requests.request(
            "POST",
            url,
            headers=headers,
            data=payload.encode("utf-8"),
            timeout=30
        )
        # print(response.text)
        response.encoding = "utf-8"
        result = response.json()

        # 解析百度API响应
        if "err_no" in result:
            if result["err_no"] == 0:
                # 识别成功
                return {
                    'success': True,
                    'text': result.get("result", [""])[0],
                    # 'raw_result': result.get("result", []),
                    # 'confidence': result.get("corpus_no", ""),
                    # 'file_name': filename,
                    # 'api_response': result
                }
            else:
                # 识别失败
                error_messages = {
                    3300: "音频参数错误",
                    3301: "音频质量太差",
                    3302: "鉴权失败",
                    3303: "音频下载失败",
                    3304: "音频解码失败",
                    3305: "音频文件过大",
                    3306: "音频时长过长",
                    3307: "音频数据为空",
                    3308: "音频编码格式不支持",
                    3309: "语音识别服务错误",
                    3310: "音频格式不匹配",
                    3311: "音频采样率不匹配",
                    3312: "音频声道数不匹配"
                }

                error_msg = error_messages.get(
                    result["err_no"],
                    f"未知错误: {result.get('err_msg', '')}"
                )

                return {
                    'success': False,
                    'error': error_msg,
                    'error_code': result["err_no"],
                    'api_response': result
                }
        else:
            return {
                'success': False,
                'error': 'API响应格式错误',
                'api_response': result
            }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'API请求超时'
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API请求失败: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'处理失败: {str(e)}'
        }
