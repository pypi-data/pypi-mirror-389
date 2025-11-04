from dataclasses import dataclass
from typing import Any, Dict, Optional

from ...flow_metrics import EndpointMetric
from ...investigation_manager import send_investigation_to_worker
from ...native import RawInvestigation
from ..apm_trace_ids import collect_apm_trace_ids
from ..limited_logger import limited_logger
from .http_investigation import (
    finish_base_http_investigation,
    safe_get_header,
)
from .investigation_utils import minimize_object_with_defaults


@dataclass
class FlaskRequestData:
    request_body: Optional[Any] = None
    query: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    path: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None


def finish_flask_investigation(
    raw_investigation: RawInvestigation,
    metric: Optional[EndpointMetric],
    flask_data: FlaskRequestData,
) -> None:
    try:
        apm_trace_ids = collect_apm_trace_ids(flask_data.headers)
        investigation = finish_base_http_investigation(
            raw_investigation,
            metric,
            flask_data.path,
            apm_trace_ids,
        )

        if investigation is None:
            return

        investigation.context.request_body = minimize_object_with_defaults(
            flask_data.request_body
        )
        investigation.context.query = minimize_object_with_defaults(flask_data.query)
        investigation.context.params = minimize_object_with_defaults(flask_data.params)
        investigation.context.content_type = safe_get_header(
            flask_data.headers, "content-type"
        )
        investigation.context.content_encoding = safe_get_header(
            flask_data.headers, "content-encoding"
        )

        send_investigation_to_worker(investigation)
    except Exception:
        limited_logger.log(
            "An error occurred in finish_flask_investigation", exc_info=True
        )
