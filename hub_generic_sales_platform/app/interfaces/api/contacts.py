"""
Contacts API – Derive from runtime_session (no separate contact table per schema).
Returns "contacts" = aggregated session participants by external user id from ext_metadata.
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.engine import get_session
from app.infrastructure.database.models.runtime import RuntimeSession
from app.interfaces.api.dependencies import get_current_tenant_id

contacts_router = APIRouter(tags=["contacts"])


def _extract_contact_id(ext_metadata: dict | None) -> str | None:
    """Extract external user id from ext_metadata."""
    if not ext_metadata or not isinstance(ext_metadata, dict):
        return None
    for key in ("user_id", "zalo_user_id", "messenger_id", "external_id"):
        if ext_metadata.get(key):
            return str(ext_metadata[key])
    return None


@contacts_router.get("/contacts")
async def list_contacts(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200)
):
    """
    List contacts derived from runtime_session.
    Groups by external user id from ext_metadata (user_id, zalo_user_id, messenger_id) or session id.
    """
    stmt = select(
        RuntimeSession.id,
        RuntimeSession.ext_metadata,
        RuntimeSession.started_at,
        RuntimeSession.channel_code,
        RuntimeSession.lifecycle_state,
    ).where(
        RuntimeSession.tenant_id == tenant_id
    ).order_by(
        RuntimeSession.started_at.desc().nullslast()
    ).limit(limit * 3)  # Fetch extra to group, then limit

    result = await db.execute(stmt)
    rows = result.all()

    # Group by contact_id (from ext_metadata or session id)
    agg: dict[str, dict] = {}
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    for r in rows:
        cid = _extract_contact_id(r.ext_metadata) or r.id
        if cid not in agg:
            agg[cid] = {
                "id": cid[:36],
                "channel": r.channel_code or "webchat",
                "last_active": r.started_at,
                "session_count": 0,
                "lifecycle_state": r.lifecycle_state,
            }
        agg[cid]["session_count"] += 1
        if r.started_at and (not agg[cid]["last_active"] or r.started_at > agg[cid]["last_active"]):
            agg[cid]["last_active"] = r.started_at
            agg[cid]["channel"] = r.channel_code or agg[cid]["channel"]

    # Sort by last_active desc, apply skip/limit
    sorted_contacts = sorted(
        agg.values(),
        key=lambda x: (x["last_active"] or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True
    )[skip:skip + limit]

    contacts = []
    for c in sorted_contacts:
        last_active = c["last_active"]
        is_recent = last_active and (last_active.timestamp() if last_active else 0) >= cutoff.timestamp()
        status = "active" if is_recent else ("lead" if c["session_count"] >= 2 else "inactive")

        contacts.append({
            "id": c["id"],
            "name": f"User ({c['channel']})",
            "email": "",
            "phone": "",
            "status": status,
            "tags": [c["channel"]] if c["channel"] else [],
            "last_active": last_active.isoformat() if last_active else "",
        })

    return contacts
