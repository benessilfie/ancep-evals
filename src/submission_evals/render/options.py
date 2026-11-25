from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PacketOptions:
    agency: str = "Harbridge Insurance Brokers"
    broker_name: str = "Dana Whitfield"
    broker_email: str = "d.whitfield@harbridge.example"
    target_carrier: str = "Northgate Specialty Insurance Company"
    target_naic: str = "31887"
    underwriter_email: str = "newbusiness@northgate-specialty.example"
    submitted_on: date = date(2026, 12, 7)
    agency_customer_id: str = "HRB-004418"
    state_total_in_email: bool = True
    stale_total_in_email: int | None = None
    tick_no_losses_box: bool = False
    include_loss_runs: bool = True
    include_no_losses_letter: bool = False
    stale_location_values: bool = False
    promise_loss_summary_without_it: bool = False
    state_location_count_in_email: bool = True
    mislabel_loss_run_b_columns: bool = False
    sov_as_paged_text: bool = False
    sov_page_break_after: int = 9
    resend_note: str | None = None


def us_date(value: date) -> str:
    return value.strftime("%m/%d/%Y")


def long_date(value: date) -> str:
    return value.strftime("%d %B %Y")


def carrier_date(value: date) -> str:
    return value.strftime("%d-%b-%Y").upper()
