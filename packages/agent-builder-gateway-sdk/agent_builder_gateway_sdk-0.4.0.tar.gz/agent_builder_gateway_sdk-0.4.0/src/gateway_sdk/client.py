"""Gateway 客户端（内部版本）

用于 Agent/Prefab 内部调用网关

架构说明：
- Agent 从请求头获取 X-Internal-Token（由网关传入）
- Prefab 从请求头获取 X-Internal-Token（由 Agent 传入）
- SDK 直接传递 internal token，不做任何转换
"""

import httpx
from typing import Any, Dict, List, Optional, Union, Iterator
from .models import PrefabCall, PrefabResult, BatchResult, CallStatus, StreamEvent
from .streaming import parse_sse_stream
from .exceptions import (
    GatewayError,
    AuthenticationError,
    PrefabNotFoundError,
    ValidationError,
    QuotaExceededError,
    ServiceUnavailableError,
    MissingSecretError,
)


# Gateway 地址
DEFAULT_GATEWAY_URL = "http://agent-builder-gateway-test.sensedeal.vip"


class GatewayClient:
    """Gateway SDK 主客户端（内部版本）"""

    def __init__(
        self,
        internal_token: str,
        base_url: str = DEFAULT_GATEWAY_URL,
        timeout: int = 60,
    ):
        """
        初始化客户端

        Args:
            internal_token: 内部 token（从请求头 X-Internal-Token 获取）
            base_url: Gateway 地址（默认使用测试环境）
            timeout: 请求超时时间（秒）
        
        Note:
            此 SDK 专门用于 Agent/Prefab 内部调用，不支持外部 API Key/JWT。
            外部用户请使用外部端点 /v1/external/invoke_*
        """
        if not internal_token:
            raise ValueError("internal_token is required for Gateway SDK")
        
        self.base_url = base_url.rstrip("/")
        self.internal_token = internal_token
        self.timeout = timeout

    def run(
        self,
        prefab_id: str,
        version: str,
        function_name: str,
        parameters: Dict[str, Any],
        files: Optional[Dict[str, List[str]]] = None,
        stream: bool = False,
    ) -> Union[PrefabResult, Iterator[StreamEvent]]:
        """
        执行单个预制件

        Args:
            prefab_id: 预制件 ID
            version: 版本号
            function_name: 函数名
            parameters: 参数字典
            files: 文件输入（可选）
            stream: 是否流式返回

        Returns:
            PrefabResult 或 StreamEvent 迭代器

        Raises:
            AuthenticationError: 认证失败
            PrefabNotFoundError: 预制件不存在
            ValidationError: 参数验证失败
            QuotaExceededError: 配额超限
            ServiceUnavailableError: 服务不可用
            MissingSecretError: 缺少必需的密钥
        """
        call = PrefabCall(
            prefab_id=prefab_id,
            version=version,
            function_name=function_name,
            parameters=parameters,
            files=files,
        )

        if stream:
            return self._run_streaming(call)
        else:
            result = self.run_batch([call])
            return result.results[0]

    def run_batch(self, calls: List[PrefabCall]) -> BatchResult:
        """
        批量执行预制件

        Args:
            calls: 预制件调用列表

        Returns:
            BatchResult

        Raises:
            同 run() 方法
        """
        url = f"{self.base_url}/v1/internal/run"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token
        }

        payload = {"calls": [call.to_dict() for call in calls]}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=headers)
                self._handle_error_response(response)

                data = response.json()
                results = [
                    PrefabResult(
                        status=CallStatus(r["status"]),
                        output=r.get("output"),
                        error=r.get("error"),
                        job_id=data.get("job_id"),
                    )
                    for r in data["results"]
                ]

                return BatchResult(job_id=data["job_id"], status=data["status"], results=results)

        except httpx.TimeoutException:
            raise ServiceUnavailableError("请求超时")
        except httpx.RequestError as e:
            raise ServiceUnavailableError(f"网络请求失败: {str(e)}")

    def _run_streaming(self, call: PrefabCall) -> Iterator[StreamEvent]:
        """
        流式执行预制件

        Args:
            call: 预制件调用

        Yields:
            StreamEvent
        """
        url = f"{self.base_url}/v1/internal/run"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token
        }

        payload = {"calls": [call.to_dict()]}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream("POST", url, json=payload, headers=headers) as response:
                    self._handle_error_response(response)

                    # 解析 SSE 流
                    yield from parse_sse_stream(response.iter_bytes())

        except httpx.TimeoutException:
            raise ServiceUnavailableError("请求超时")
        except httpx.RequestError as e:
            raise ServiceUnavailableError(f"网络请求失败: {str(e)}")

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        处理错误响应

        Args:
            response: HTTP 响应

        Raises:
            对应的异常
        """
        if response.status_code < 400:
            return

        try:
            error_data = response.json()
            detail = error_data.get("detail", "Unknown error")

            # 解析错误详情
            if isinstance(detail, dict):
                error_code = detail.get("error_code", "UNKNOWN_ERROR")
                message = detail.get("message", str(detail))
            else:
                error_code = "UNKNOWN_ERROR"
                message = str(detail)

        except Exception:
            error_code = "UNKNOWN_ERROR"
            # 对于流式响应，需要先读取内容
            try:
                error_text = response.text
            except Exception:
                # 如果无法读取，先读取响应再获取文本
                try:
                    response.read()
                    error_text = response.text
                except Exception:
                    error_text = "Unable to read error response"
            message = f"HTTP {response.status_code}: {error_text}"

        # 根据状态码和错误码抛出对应异常
        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(message)
        elif response.status_code == 404:
            raise PrefabNotFoundError("unknown", "unknown", message)
        elif response.status_code == 422:
            raise ValidationError(message)
        elif response.status_code == 429:
            # 配额超限
            if isinstance(detail, dict):
                raise QuotaExceededError(
                    message,
                    limit=detail.get("limit", 0),
                    used=detail.get("used", 0),
                    quota_type=detail.get("quota_type", "unknown"),
                )
            else:
                raise QuotaExceededError(message, 0, 0, "unknown")
        elif response.status_code == 400 and error_code == "MISSING_SECRET":
            # 缺少密钥
            if isinstance(detail, dict):
                raise MissingSecretError(
                    prefab_id=detail.get("prefab_id", "unknown"),
                    secret_name=detail.get("secret_name", "unknown"),
                    instructions=detail.get("instructions"),
                )
            else:
                raise MissingSecretError("unknown", "unknown")
        elif response.status_code >= 500:
            raise ServiceUnavailableError(message)
        else:
            raise GatewayError(message, {"error_code": error_code})

