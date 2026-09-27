import logging
from contextvars import ContextVar
from typing import Optional, Any

analysis_id_ctx: ContextVar[Optional[str]] = ContextVar("analysis_id_ctx", default=None)

class StructuredLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        aid = analysis_id_ctx.get()
        extra_items = []
        if aid:
            extra_items.append(f"analysis_id={aid}")
        
        extra_dict = kwargs.get("extra", {})
        for k, v in extra_dict.items():
            extra_items.append(f"{k}={v}")
        
        if extra_items:
            formatted_msg = f"{msg} " + " ".join(extra_items)
        else:
            formatted_msg = msg
            
        return formatted_msg, kwargs

def get_logger(name: str) -> StructuredLoggerAdapter:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return StructuredLoggerAdapter(logger, {})
