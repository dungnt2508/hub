"""
Logger tiếng Việt với structlog
Hỗ trợ logging có cấu trúc, dễ debug và trace
"""
import logging
import logging.handlers
import sys
import traceback as tb
from typing import Any, Optional
from pathlib import Path
import structlog
from structlog.types import EventDict, Processor


# Mapping log level sang tiếng Việt
LEVEL_MAPPING = {
    "debug": "GHI_LOG",
    "info": "THÔNG_TIN",
    "warning": "CẢNH_BÁO",
    "error": "LỖI",
    "critical": "NGHIÊM_TRỌNG",
}


def add_vietnamese_level(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Thêm tên level tiếng Việt"""
    level = event_dict.get("level", "info")
    event_dict["level_vn"] = LEVEL_MAPPING.get(level.lower(), level.upper())
    return event_dict


def add_domain_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Thêm context domain nếu có"""
    return event_dict


def format_exception(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Format exception info sang tiếng Việt"""
    if event_dict.get("exc_info"):
        event_dict["có_lỗi"] = True
    return event_dict


def simple_traceback_formatter(sio, exc_info):
    """
    Simple exception formatter không dùng rich
    Tránh lỗi islice() với rich traceback khi chạy trong môi trường không hỗ trợ
    """
    sio.write("\n")
    tb.print_exception(*exc_info, file=sio)


def _add_file_handler(
    log_file_path: str,
    log_level: str,
    max_bytes: int,
    backup_count: int
) -> None:
    """
    Thêm file handler với log rotation
    
    Args:
        log_file_path: Đường dẫn file log
        log_level: Mức độ log
        max_bytes: Kích thước tối đa của file trước khi rotate
        backup_count: Số file backup giữ lại
    """
    try:
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        
    except Exception as e:
        print(f"Không thể setup file logging: {e}")


def _configure_library_loggers(log_level: str = "WARNING") -> None:
    """
    Cấu hình log level cho các thư viện để giảm noise
    """
    noisy_loggers = [
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "urllib3.connectionpool",
        "urllib3.util.retry",
        "httpx",
        "httpcore",
        "asyncpg",
        "asyncpg.protocol",
        "asyncpg.connection",
        "uvicorn.access",
        "uvicorn",
        "starlette.middleware",
        "qdrant_client",
        "qdrant_client.http",
    ]
    
    for logger_name in noisy_loggers:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.setLevel(logging.WARNING)
        lib_logger.propagate = False


def configure_logger(
    log_level: str = "INFO",
    log_format: str = "console",
    enable_colors: bool = True,
    environment: str = "dev",
    log_file_enabled: bool = False,
    log_file_path: str = "logs/app.log",
    log_file_max_bytes: int = 10485760,
    log_file_backup_count: int = 5
) -> None:
    """
    Cấu hình logger cho toàn hệ thống
    """
    
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_vietnamese_level,
        add_domain_context,
        format_exception,
        structlog.processors.TimeStamper(fmt="iso", utc=False),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=False if sys.platform == "win32" else enable_colors,
                exception_formatter=simple_traceback_formatter
            )
        )
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Force UTF-8 encoding cho console
    import io
    utf8_stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',
        line_buffering=True
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=utf8_stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
    
    if log_file_enabled:
        _add_file_handler(
            log_file_path,
            log_level,
            log_file_max_bytes,
            log_file_backup_count
        )
    
    if environment in ["prod", "production"]:
        _configure_library_loggers(log_level)


def get_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """
    Tạo logger với context
    """
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger


def format_step_message(step_num: int, step_name: str, action: str = "") -> str:
    """
    Format log message cho RAG pipeline steps
    """
    formatted_message = f"[BƯỚC {step_num}] {step_name}"
    if action:
        formatted_message += f" - {action}"
    return formatted_message


class LoggerMixin:
    """
    Mixin class để thêm logger vào usecase/service
    """
    
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        if not hasattr(self, "_logger"):
            class_name = self.__class__.__name__
            module_name = self.__class__.__module__
            
            domain = "unknown"
            if "domains." in module_name:
                domain = module_name.split("domains.")[1].split(".")[0]
            
            self._logger = get_logger(
                f"{module_name}.{class_name}",
                domain=domain,
                component=class_name
            )
        return self._logger
