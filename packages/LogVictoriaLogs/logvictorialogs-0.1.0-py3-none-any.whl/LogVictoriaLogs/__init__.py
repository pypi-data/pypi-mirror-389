import socket
import requests
import json
import logging
import inspect
from typing import List, Dict, Any, Union


class VictoriaLogsClient:
    """
    VictoriaLogs 客户端
    提供 HTTP / Syslog 日志发送与查询功能
    支持多层 stream：project + service
    """

    def __init__(
        self,
        host: str,
        http_port: int = 9428,
        syslog_udp_port: int = 514,
        timeout: int = 5,
        project: str = None,
        name: str = "logging-demo"
    ):
        """
        :param host: VictoriaLogs 主机
        :param http_port: HTTP 插入端口（默认 9428）
        :param syslog_udp_port: Syslog UDP 端口
        :param timeout: 请求超时
        :param project: 项目名，用于日志分层（可选）
        :param name: 当前模块/服务名
        """
        self.host = host
        self.http_port = http_port
        self.syslog_udp_port = syslog_udp_port
        self.timeout = timeout
        self.project = project
        self.name = name

        self.http_insert_url = f"http://{host}:{http_port}/insert/jsonline"
        self.query_url = f"http://{host}:{http_port}/select/logsql/query"

        # 内部 logger
        self.logger = logging.getLogger(f"{self.name}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    # ----------------------------------------------------------------------
    # 🌐 日志发送
    # ----------------------------------------------------------------------
    def _send_logs(
        self,
        logs: Union[Dict[str, Any], List[Dict[str, Any]]],
        protocol: str = "http",
        stream_fields: str = None,
        time_field: str = "timestamp",
        msg_field: str = "message"
    ) -> bool:
        """发送日志"""
        logs = [logs] if isinstance(logs, dict) else logs
        protocol = protocol.lower()

        # 自动选择 stream 层级结构
        if stream_fields is None:
            stream_fields = "project,service" if self.project else "service"

        if protocol == "http":
            return self._send_http(logs, stream_fields, time_field, msg_field)
        elif protocol == "syslog":
            return self._send_syslog(logs)
        else:
            raise ValueError(f"不支持的协议: {protocol}")

    def _send_http(
        self, logs: List[Dict[str, Any]],
        stream_fields: str, time_field: str, msg_field: str
    ) -> bool:
        """通过 HTTP API 发送日志"""
        params = {
            "_stream_fields": stream_fields,
            "_time_field": time_field,
            "_msg_field": msg_field
        }
        json_lines = "\n".join(json.dumps(log, ensure_ascii=False) for log in logs) + "\n"

        try:
            resp = requests.post(
                self.http_insert_url,
                params=params,
                data=json_lines.encode("utf-8"),
                timeout=self.timeout
            )
            if resp.ok:
                # self.logger.info("✅ HTTP 日志发送成功")
                return True
            self.logger.error(f"❌ HTTP 发送失败: {resp.status_code} {resp.text}")
        except requests.RequestException as e:
            self.logger.error(f"❌ 无法连接到 VictoriaLogs HTTP 接口: {e}")
        return False

    def _send_syslog(self, logs: List[Dict[str, Any]]) -> bool:
        """通过 Syslog UDP 发送日志"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                for log in logs:
                    service = log.get("service", "unknown")
                    level = log.get("level", "INFO").upper()
                    message = log.get("message", "")
                    msg = f"<14>{service} [{level}] {message}"
                    sock.sendto(msg.encode("utf-8"), (self.host, self.syslog_udp_port))
            # self.logger.info("✅ Syslog UDP 日志发送成功")
            return True
        except OSError as e:
            self.logger.error(f"❌ Syslog 发送失败: {e}")
            return False

    # ----------------------------------------------------------------------
    # 🔍 查询相关
    # ----------------------------------------------------------------------
    def query_logs(self, query: str = "*") -> List[Dict[str, Any]]:
        """执行 LogsQL 查询"""
        try:
            resp = requests.get(self.query_url, params={"query": query}, timeout=self.timeout)
            if not resp.ok:
                self.logger.error(f"❌ 查询失败: {resp.status_code} {resp.text}")
                return []

            logs = []
            for line in resp.text.strip().splitlines():
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ 无法解析日志行: {line}")

            self.logger.info(f"✅ 查询成功，共 {len(logs)} 条日志")
            return logs
        except requests.RequestException as e:
            self.logger.error(f"❌ 无法连接到 VictoriaLogs 查询接口: {e}")
            return []

    def print_logs(self, query: str = "*") -> None:
        """查询并打印日志"""
        logs = self.query_logs(query)
        if not logs:
            print("未查询到日志。")
            return
        for i, log in enumerate(logs, 1):
            print(f"\n--- 日志 {i} ---")
            for k, v in log.items():
                print(f"{k}: {v}")

    # ----------------------------------------------------------------------
    # 🧩 辅助函数
    # ----------------------------------------------------------------------
    def get_caller_info(self, depth: int = 2) -> Dict[str, str]:
        """动态获取调用者的函数名、文件、行号"""
        stack = inspect.stack()
        if len(stack) > depth:
            frame_info = stack[depth]
            return {
                "function": frame_info.function,
                "filename": frame_info.filename,
                "lineno": str(frame_info.lineno),
                "module": frame_info.frame.f_globals.get("__name__", "unknown")
            }
        return {"function": "unknown", "filename": "unknown", "lineno": "0", "module": "unknown"}

    def sent(self, message: str, service: str = None,error:bool = False,warning:bool = False, debug:bool = False,info:bool = False,**kwargs) -> bool:
        """发送带有上下文信息的日志（自动包含调用函数、行号）

        支持通过布尔参数自动设置日志级别：
        - error=True: 设置为 error 级别
        - warning=True: 设置为 warning 级别
        - debug=True: 设置为 debug 级别
        - info=True: 设置为 info 级别
        """
        # 根据布尔参数自动设置日志级别
        if error:
            level = "error"
        elif warning:
            level = "warning"
        elif debug:
            level = "debug"
        else:
            level = "info"

        # 默认 service 用实例 name
        service = service or self.name

        # 从kwargs中移除布尔参数，避免重复
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['error', 'warning', 'debug', 'info']}

        info = self.get_caller_info(depth=2)
        log = {
            "message": f"{service} | {message}",
            "level": level.upper(),
            "service": service,
            **({"project": self.project} if self.project else {}),
            **info,
            "source": "python-app",
            "environment": "development",
            **filtered_kwargs
        }

        # 控制台日志
        log_message = f"{service} | {info['function']}:{info['lineno']} - {message}"
        if level.lower() == "error":
            self.logger.error(log_message)
        elif level.lower() == "warning":
            self.logger.warning(log_message)
        elif level.lower() == "debug":
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)

        # 发送日志
        return self._send_logs(log)

    # ----------------------------------------------------------------------
    # 🔧 Python logging 集成（增强版）
    # ----------------------------------------------------------------------
    def setup_logging_handler(self, service: str = "python-app", level: int = logging.INFO) -> logging.Handler:
        """配置 Python logging Handler"""
        client = self

        class VictoriaLogsHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                try:
                    func = record.funcName
                    if func == "<module>":
                        func = record.filename.rsplit(".", 1)[0]

                    try:
                        formatted_message = self.format(record)
                    except Exception:
                        formatted_message = record.getMessage()

                    log = {
                        "message": formatted_message,
                        "level": record.levelname.upper(),
                        "service": service,
                        **({"project": client.project} if client.project else {}),
                        "function": func,
                        "filename": record.filename,
                        "lineno": str(record.lineno),
                        "module": record.module,
                        "source": "python-logging",
                        "environment": "development",
                        "thread": getattr(record, "thread", "unknown"),
                        "process": getattr(record, "process", "unknown")
                    }
                    client._send_logs(log)
                except Exception:
                    pass

        handler = VictoriaLogsHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S"
        ))
        return handler


# ----------------------------------------------------------------------
# 🎯 示例
# ----------------------------------------------------------------------
def demo_function():
    client = VictoriaLogsClient("192.168.164.31", project="shortlink-system", name="shortlink-updater")
    client.sent("从 demo_function 发出的日志")


if __name__ == "__main__":
    # 主项目日志
    main_client = VictoriaLogsClient("192.168.164.31", project="shortlink-system", name="main")
    updater_client = VictoriaLogsClient("192.168.164.31", project="shortlink-system", name="shortlink-updater")

    # 模拟模块日志
    demo_function()
    main_client.sent("主模块启动完成")
    updater_client.sent("短链更新成功")

    # 查询
    main_client.print_logs('project:"shortlink-system" service:"shortlink-updater"')
