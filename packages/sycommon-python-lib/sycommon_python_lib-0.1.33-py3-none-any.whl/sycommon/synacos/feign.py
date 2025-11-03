import io
import os
import time

import aiohttp
from sycommon.logging.kafka_log import SYLogger
from sycommon.synacos.nacos_service import NacosService

"""
支持异步Feign客户端
    方式一: 使用 @feign_client 和 @feign_request 装饰器
    方式二: 使用 feign 函数
"""


async def feign(service_name, api_path, method='GET', params=None, headers=None, file_path=None,
                path_params=None, body=None, files=None, form_data=None, timeout=None):
    """
    feign 函数，显式设置JSON请求的Content-Type头
    """
    session = aiohttp.ClientSession()
    try:
        # 初始化headers，确保是可修改的字典
        headers = headers.copy() if headers else {}

        # 处理JSON请求的Content-Type
        is_json_request = method.upper() in ["POST", "PUT", "PATCH"] and not (
            files or form_data or file_path)
        if is_json_request and "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        nacos_service = NacosService(None)
        version = headers.get('s-y-version')

        # 获取服务实例
        instances = nacos_service.get_service_instances(
            service_name, target_version=version)
        if not instances:
            SYLogger.error(f"nacos:未找到 {service_name} 的健康实例")
            return None

        # 简单轮询负载均衡
        instance = instances[int(time.time()) % len(instances)]

        SYLogger.info(f"nacos:开始调用服务: {service_name}")
        SYLogger.info(f"nacos:请求头: {headers}")

        ip = instance.get('ip')
        port = instance.get('port')

        # 处理path参数
        if path_params:
            for key, value in path_params.items():
                api_path = api_path.replace(f"{{{key}}}", str(value))

        url = f"http://{ip}:{port}{api_path}"
        SYLogger.info(f"nacos:请求地址: {url}")

        try:
            # 处理文件上传
            if files or form_data or file_path:
                data = aiohttp.FormData()
                if form_data:
                    for key, value in form_data.items():
                        data.add_field(key, value)
                if files:
                    # 兼容处理：同时支持字典（单文件）和列表（多文件）
                    if isinstance(files, dict):
                        # 处理原有字典格式（单文件）
                        # 字典格式：{field_name: (filename, content)}
                        for field_name, (filename, content) in files.items():
                            data.add_field(field_name, content,
                                           filename=filename)
                    elif isinstance(files, list):
                        # 处理新列表格式（多文件）
                        # 列表格式：[(field_name, filename, content), ...]
                        for item in files:
                            if len(item) != 3:
                                raise ValueError(
                                    f"列表元素格式错误，需为 (field_name, filename, content)，实际为 {item}")
                            field_name, filename, content = item
                            data.add_field(field_name, content,
                                           filename=filename)
                    else:
                        raise TypeError(f"files 参数必须是字典或列表，实际为 {type(files)}")
                if file_path:
                    filename = os.path.basename(file_path)
                    with open(file_path, 'rb') as f:
                        data.add_field('file', f, filename=filename)
                # 移除Content-Type，让aiohttp自动处理
                headers.pop('Content-Type', None)
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    data=data,
                    timeout=timeout
                ) as response:
                    return await _handle_feign_response(response)
            else:
                # 普通JSON请求
                async with session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    json=body,
                    timeout=timeout
                ) as response:
                    return await _handle_feign_response(response)
        except aiohttp.ClientError as e:
            SYLogger.error(
                f"nacos:请求服务接口时出错ClientError path: {api_path} error:{e}")
            return None
    except Exception as e:
        import traceback
        SYLogger.error(
            f"nacos:请求服务接口时出错 path: {api_path} error:{traceback.format_exc()}")
        return None
    finally:
        await session.close()


async def _handle_feign_response(response):
    """处理Feign请求的响应"""
    if response.status == 200:
        content_type = response.headers.get('Content-Type')
        if 'application/json' in content_type:
            return await response.json()
        else:
            content = await response.read()
            return io.BytesIO(content)
    else:
        error_msg = await response.text()
        SYLogger.error(f"nacos:请求失败，状态码: {response.status}，响应内容: {error_msg}")
        return None
