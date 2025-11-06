"""Type definitions for x402tools SDK."""

from typing import Optional, Dict, Any, Literal
from datetime import datetime
from dataclasses import dataclass


PeriodType = Literal["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]


@dataclass
class Envelope:
    """Represents a usage envelope."""
    id: str
    name: str
    limit: int
    period: PeriodType
    organization_id: str
    created_at: datetime
    updated_at: datetime
    reset_day: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Envelope":
        """Create an Envelope from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            limit=data["limit"],
            period=data["period"],
            organization_id=data["organizationId"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00")),
            reset_day=data.get("resetDay"),
        )


@dataclass
class Usage:
    """Represents a usage record."""
    id: str
    envelope_id: str
    amount: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Usage":
        """Create a Usage from API response dictionary."""
        return cls(
            id=data["id"],
            envelope_id=data["envelopeId"],
            amount=data["amount"],
            timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
            metadata=data.get("metadata"),
        )


@dataclass
class ApiKey:
    """Represents an API key."""
    id: str
    key: str
    name: str
    organization_id: str
    created_at: datetime
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApiKey":
        """Create an ApiKey from API response dictionary."""
        last_used = None
        if data.get("lastUsed"):
            last_used = datetime.fromisoformat(data["lastUsed"].replace("Z", "+00:00"))
        
        expires_at = None
        if data.get("expiresAt"):
            expires_at = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            key=data["key"],
            name=data["name"],
            organization_id=data["organizationId"],
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")),
            last_used=last_used,
            expires_at=expires_at,
        )


@dataclass
class UsageStats:
    """Represents usage statistics."""
    total_usage: int
    envelope_count: int
    active_envelopes: int
    period_usage: list[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageStats":
        """Create UsageStats from API response dictionary."""
        return cls(
            total_usage=data["totalUsage"],
            envelope_count=data["envelopeCount"],
            active_envelopes=data["activeEnvelopes"],
            period_usage=data.get("periodUsage", []),
        )
