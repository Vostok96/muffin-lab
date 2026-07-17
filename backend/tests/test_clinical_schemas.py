from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas import OrderCreate, PatientCreate, ReceiveSpecimenInput, SpecimenDetailsUpdate


def test_patient_birth_date_cannot_be_in_future() -> None:
    with pytest.raises(ValidationError, match="birth_date cannot be in the future"):
        PatientCreate(
            medical_record_number="HC-TEST",
            family_name="Fictitious",
            given_name="Patient",
            birth_date=date.today() + timedelta(days=1),
            sex="X",
        )


def test_order_datetime_requires_timezone() -> None:
    with pytest.raises(ValidationError, match="timezone offset"):
        OrderCreate(
            patient_id="patient-id",
            ordered_at=datetime.now(),
            origin_id="origin-id",
            service_id="service-id",
        )


def test_reception_datetimes_accept_timezone() -> None:
    received_at = datetime.now(timezone.utc)
    payload = ReceiveSpecimenInput(
        received_at=received_at,
        collection_at=received_at - timedelta(minutes=10),
        destination_id="destination-id",
    )
    assert payload.received_at == received_at


def test_specimen_correction_accepts_historical_dates() -> None:
    collection_at = datetime(2026, 7, 13, 8, 30, tzinfo=timezone(timedelta(hours=-5)))
    received_at = datetime(2026, 7, 14, 9, 15, tzinfo=timezone(timedelta(hours=-5)))
    payload = SpecimenDetailsUpdate(
        collection_at=collection_at,
        received_at=received_at,
        location="MESA DE MICROBIOLOGIA",
    )
    assert payload.collection_at == collection_at
    assert payload.received_at == received_at
