from typing import Any, Optional

from ...config import config
from ...flow_metrics import FlowMetric
from ...native import RawInvestigation
from ...schemas.investigation import (
    BaseInvestigationContext,
    ErrorBreakdown,
    Investigation,
    InvestigationExceptionInfo,
)
from ..limited_logger import limited_logger
from .investigation_utils import (
    get_error_records_from_investigation,
    get_investigation_dedup,
    get_investigation_deduping_key_for_errors,
    get_machine_metrics,
    get_system_info,
    get_total_investigations,
    increase_total_investigations,
    minimize_exception_info_in_place,
)


def finish_base_investigation(
    raw_investigation: RawInvestigation,
    metric: FlowMetric,
) -> Optional[Investigation[Any]]:
    if metric.flow_id is None:
        limited_logger.log("No flow id in metric")
        return None

    if raw_investigation.error_accoured == 1:
        limited_logger.log("Error accoured in investigation")
        return None

    try:
        metric_status = metric.get_status()
        if metric_status is None:
            metric_status = ""
            limited_logger.log("Metric status is None")

        error_records = get_error_records_from_investigation(raw_investigation)
        dedup_key = get_investigation_deduping_key_for_errors(
            error_records, metric_status
        )

        error_breakdown = ErrorBreakdown(
            key=dedup_key, errors=error_records, failure_type=metric_status
        )
        metric.set_error_breakdown(error_breakdown)
    except Exception:
        limited_logger.log("Error extracting error breakdown", exc_info=True)

    if get_total_investigations() >= config.max_investigations:
        limited_logger.log("Max investigations reached")
        return None

    investigation_dedup = get_investigation_dedup()

    if investigation_dedup.get(metric.flow_id) is None:
        investigation_dedup[metric.flow_id] = dict()

    if investigation_dedup[metric.flow_id].get(dedup_key) is None:
        investigation_dedup[metric.flow_id][dedup_key] = 0

    if investigation_dedup[metric.flow_id][dedup_key] >= config.max_same_investigation:
        limited_logger.log("Max same investigation reached")
        return None

    increase_total_investigations()
    investigation_dedup[metric.flow_id][dedup_key] += 1

    return Investigation(
        exceptions=[
            minimize_exception_info_in_place(InvestigationExceptionInfo(raw_exception))
            for raw_exception in raw_investigation.exceptions.values()
        ],
        context=BaseInvestigationContext(
            type="base",
            timestamp=raw_investigation.start_time,
            machine_metrics=get_machine_metrics(),
            system_info=get_system_info(),
            user_context=raw_investigation.user_context,
        ),
        flow_id=metric.flow_id,
    )
