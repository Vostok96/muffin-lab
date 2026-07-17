"""Unit tests for outputs and integrations schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import (
    InstrumentMessageCreate,
    NotificationCreate,
    PrintJobCreate,
)


def test_print_job_kind_valid() -> None:
    job = PrintJobCreate(order_item_id="item-id", kind="LABEL")
    assert job.kind == "LABEL"


def test_print_job_kind_invalid() -> None:
    with pytest.raises(ValidationError, match="kind"):
        PrintJobCreate(order_item_id="item-id", kind="INVALID")


def test_notification_type_valid() -> None:
    notif = NotificationCreate(
        order_item_id="item-id",
        type="CRITICAL_VALUE",
        recipient="test@example.com",
    )
    assert notif.type == "CRITICAL_VALUE"


def test_notification_type_invalid() -> None:
    with pytest.raises(ValidationError, match="type"):
        NotificationCreate(
            order_item_id="item-id",
            type="WRONG_TYPE",
            recipient="test@example.com",
        )


def test_instrument_message_direction_valid() -> None:
    msg = InstrumentMessageCreate(
        direction="INBOUND",
        payload={"key": "value"},
    )
    assert msg.direction == "INBOUND"


def test_instrument_message_direction_invalid() -> None:
    with pytest.raises(ValidationError, match="direction"):
        InstrumentMessageCreate(
            direction="SIDEWAYS",
            payload={"key": "value"},
        )


def test_instrument_message_order_item_optional() -> None:
    msg = InstrumentMessageCreate(
        direction="OUTBOUND",
        payload={"cmd": "ping"},
    )
    assert msg.order_item_id is None
