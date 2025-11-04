import datetime
import time
import pytest
from datetimeops.datetime_utils import (
    now_utc, now_tz, epoch, validate_date, change_date_format,
    add_days_to_date, add_months_to_date, delta_between_dates,
    months_between_dates, days_between_dates, time_passed,
    offset_date, get_first_last_date_of_month, hhmmss_to_seconds,
    seconds_to_hhmmss, hhmmss_check, sleep_counter
)


# ----- NOW & EPOCH TESTS -----
def test_now_utc():
    assert isinstance(now_utc(), str)
    assert len(now_utc()) >= 10  # Ensures proper date format

def test_now_tz():
    assert isinstance(now_tz("Asia/Kolkata"), str)
    assert isinstance(now_tz("UTC"), str)

def test_epoch():
    assert isinstance(epoch(), int)
    assert epoch() > 0
    assert epoch("2023-01-01 00:00:00") == 1672531200


# ----- VALIDATION & FORMAT CONVERSION TESTS -----
def test_validate_date():
    """Tests validate_date with various input scenarios."""

    # ✅ Valid cases (String input)
    assert validate_date("2023-05-12 14:30:00")  # Valid date
    assert validate_date("2025-01-01")  # Valid, no format provided
    assert validate_date("2025-01-01", fmt="%Y-%m-%d")  # Explicit format

    # ✅ Valid cases (Datetime object input)
    assert validate_date(datetime.datetime(2025, 1, 1, 14, 30, 0))  # Datetime object

    # ✅ Future date checks (String input)
    future_date_str = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)).strftime("%Y-%m-%d")
    assert validate_date(future_date_str, chk_future_date=True)  # Should return True

    # ✅ Future date checks (Datetime object)
    future_date_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    assert validate_date(future_date_dt, chk_future_date=True)  # Should return True

    # ❌ Past date checks (String input)
    past_date_str = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
    assert not validate_date(past_date_str, chk_future_date=True)  # Should return False

    # ❌ Past date checks (Datetime object)
    past_date_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)
    assert not validate_date(past_date_dt, chk_future_date=True)  # Should return False

    # ❌ Invalid inputs
    assert not validate_date("Invalid Date")  # Garbage input
    assert not validate_date("2025/01/01", fmt="%Y-%m-%d")  # Wrong format
    assert not validate_date(1234567890)  # Invalid integer input

def test_change_date_format():
    """Tests change_date_format for valid and invalid inputs."""

    # ✅ Valid cases
    assert change_date_format("2023-05-12 14:30:00", "%d-%m-%Y") == "12-05-2023"
    assert change_date_format("2023-05-12 14:30:00", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S") == "2023-05-12"
    assert change_date_format("2023-05-12", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d") == "2023-05-12 00:00:00"

    # ❌ Invalid case: should raise ValueError
    with pytest.raises(ValueError):
        change_date_format("Invalid Date", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S")


# ----- DATE ARITHMETIC TESTS -----
def test_add_days_to_date():
    assert add_days_to_date("2023-05-12", 5) == "2023-05-17 00:00:00"

def test_add_months_to_date():
    assert add_months_to_date("2023-05-12", 2) == "2023-07-12 00:00:00"

def test_delta_between_dates():
    delta = delta_between_dates("2023-01-01", "2024-01-01")
    assert delta.years == 1 and delta.months == 0 and delta.days == 0


# ----- TIME DIFFERENCE TESTS -----
def test_months_between_dates():
    assert months_between_dates("2023-01-01", "2023-12-01") == 11

def test_days_between_dates():
    assert days_between_dates("2023-01-01", "2023-01-10") == 9

def test_time_passed():
    result = time_passed("2023-01-01 00:00:00", "2023-01-02 12:00:00")
    assert result["days"] == 1
    assert result["hours"] == 12


# ----- OFFSETS & MONTHLY DATE TESTS -----
def test_offset_date():
    assert offset_date("2023-01-01", "days", 10) == "2023-01-11 00:00:00"

def test_get_first_last_date_of_month():
    first, last = get_first_last_date_of_month("2023-05-15")
    assert first == "2023-05-01"
    assert last == "2023-05-31"


# ----- TIME FORMAT CONVERSION TESTS -----
def test_hhmmss_to_seconds():
    assert hhmmss_to_seconds("02:30:45") == 9045
    assert hhmmss_to_seconds("00:05:00") == 300

def test_seconds_to_hhmmss():
    assert seconds_to_hhmmss(9045) == "02:30:45"
    assert seconds_to_hhmmss(300) == "00:05:00"

def test_hhmmss_check():
    assert hhmmss_check("02:30:45") == "02:30:45"


# ----- SLEEP COUNTER TEST (Runs for 3 seconds) -----
def test_sleep_counter():
    start_time = time.time()
    sleep_counter(3)
    end_time = time.time()
    assert round(end_time - start_time) == 3  # Ensure sleep ran for ~3 sec
