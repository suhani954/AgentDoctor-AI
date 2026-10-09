from typing import Any

from app.db.mongodb import get_database
from app.models.diagnostic_report import (
    diagnostic_report_document,
    serialize_diagnostic_report,
)
from app.schemas.diagnostic_schema import DiagnosticReportRecord


DIAGNOSTIC_REPORT_COLLECTION = "diagnostic_reports"


async def save_diagnostic_report(
    *,
    user_id: str,
    agent_id: str,
    agent_name: str,
    report_type: str,
    payload: dict[str, Any],
) -> DiagnosticReportRecord:
    database = get_database()
    document = diagnostic_report_document(
        user_id=user_id,
        agent_id=agent_id,
        agent_name=agent_name,
        report_type=report_type,
        payload=payload,
    )
    result = await database[DIAGNOSTIC_REPORT_COLLECTION].insert_one(document)
    created = await database[DIAGNOSTIC_REPORT_COLLECTION].find_one(
        {"_id": result.inserted_id}
    )
    return DiagnosticReportRecord(**serialize_diagnostic_report(created))


async def list_diagnostic_reports(user_id: str) -> list[DiagnosticReportRecord]:
    database = get_database()
    cursor = (
        database[DIAGNOSTIC_REPORT_COLLECTION]
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(100)
    )
    documents = await cursor.to_list(length=100)
    return [
        DiagnosticReportRecord(**serialize_diagnostic_report(document))
        for document in documents
    ]


async def clear_diagnostic_reports(user_id: str) -> int:
    database = get_database()
    result = await database[DIAGNOSTIC_REPORT_COLLECTION].delete_many(
        {"user_id": user_id}
    )
    return result.deleted_count
