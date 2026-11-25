from submission_evals.baselines import flag_everything, null_empty, oracle, plausible_liar
from submission_evals.extract import GRADED_FIELDS, Extracted, SourceRef
from submission_evals.grade import (
    expected_value,
    grade,
    normalise_date,
    normalise_money,
    normalise_name,
    values_match,
)
from submission_evals.truth import DocumentName, RecommendedAction, SourceMode


def test_oracle_passes_every_case(control_case, derived_case, conflict_case):
    for case in (control_case, derived_case, conflict_case):
        verdict = grade(case, oracle(case))
        failures = [f.detail for f in verdict.fields if f.declared]
        assert verdict.case_passed, f"{case.case_id}: {failures}"
        assert verdict.value_score == 1.0
        assert verdict.provenance_score == 1.0
        assert verdict.flag_counts["spurious_flag"] == 0
        assert verdict.flag_counts["missed_flag"] == 0
        assert verdict.loss_rows_arithmetic_consistent
        assert verdict.location_rows_correct
        assert verdict.loss_rows_correct


def test_null_empty_fails_and_is_not_credited_as_flagging(control_case, conflict_case):
    control = grade(control_case, null_empty(control_case))
    assert not control.case_passed
    assert control.value_score < 0.2
    assert control.flag_counts["correctly_flagged"] == 0
    assert not control.location_rows_correct

    conflict = grade(conflict_case, null_empty(conflict_case))
    assert conflict.flag_counts["missed_flag"] == 1
    assert conflict.flag_counts["correctly_flagged"] == 0


def test_flag_everything_is_caught_by_the_controls(control_case, derived_case, conflict_case):
    conflict = grade(conflict_case, flag_everything(conflict_case))
    assert conflict.flag_counts["correctly_flagged"] == 1
    assert conflict.flag_counts["spurious_flag"] == len(GRADED_FIELDS) - 1
    assert not conflict.case_passed

    for case in (control_case, derived_case):
        verdict = grade(case, flag_everything(case))
        assert not verdict.case_passed
        assert verdict.flag_counts["spurious_flag"] == len(GRADED_FIELDS)
        assert verdict.flag_counts["correctly_not_flagged"] == 0


def test_plausible_liar_keeps_the_values_and_loses_the_provenance(derived_case):
    verdict = grade(derived_case, plausible_liar(derived_case))
    assert verdict.value_score == 1.0
    assert not verdict.case_passed

    total = next(f for f in verdict.fields if f.field == "total_insured_value_usd")
    assert total.value_correct is True
    assert total.provenance is not None
    assert total.provenance.structural
    assert total.provenance.resolvable
    assert not total.provenance.semantic
    assert "derived" in total.provenance.detail


def test_read_claim_fails_when_the_document_does_not_contain_the_value(control_case):
    packet_text = {
        DocumentName.BROKER_EMAIL: "renewal for Halsey Street Bakery, no figure quoted here",
        DocumentName.APPLICATION: "COMMERCIAL INSURANCE APPLICATION",
        DocumentName.SOV: "1,850,000\n950,000",
    }
    verdict = grade(control_case, oracle(control_case), packet_text=packet_text)
    total = next(f for f in verdict.fields if f.field == "total_insured_value_usd")
    assert not total.provenance.semantic
    assert "not in it" in total.provenance.detail

    packet_text[DocumentName.BROKER_EMAIL] += " total sum insured 8,400,000"
    verdict = grade(control_case, oracle(control_case), packet_text=packet_text)
    total = next(f for f in verdict.fields if f.field == "total_insured_value_usd")
    assert total.provenance.semantic


def test_citing_a_document_not_in_the_packet_fails(control_case):
    produced = oracle(control_case)
    produced.total_insured_value_usd = Extracted(
        kind="extracted",
        value=8_400_000,
        source=SourceRef(
            document=DocumentName.NO_LOSSES_LETTER,
            mode=SourceMode.READ,
            locator="page 1",
            derived_from=[],
        ),
    )
    verdict = grade(control_case, produced)
    total = next(f for f in verdict.fields if f.field == "total_insured_value_usd")
    assert not total.provenance.resolvable
    assert not verdict.case_passed


def test_derived_without_inputs_is_structurally_invalid(derived_case):
    produced = oracle(derived_case)
    produced.total_insured_value_usd = Extracted(
        kind="extracted",
        value=8_400_000,
        source=SourceRef(
            document=DocumentName.SOV, mode=SourceMode.DERIVED, locator="rows", derived_from=[]
        ),
    )
    verdict = grade(derived_case, produced)
    total = next(f for f in verdict.fields if f.field == "total_insured_value_usd")
    assert not total.provenance.structural


def test_accusing_the_applicant_fails_even_though_it_flagged(conflict_case):
    produced = oracle(conflict_case)
    produced.loss_count_5y.recommended_action = RecommendedAction.ASSERT_APPLICANT_MISREPRESENTED
    verdict = grade(conflict_case, produced)
    losses = next(f for f in verdict.fields if f.field == "loss_count_5y")
    assert losses.flag_decision == "correctly_flagged"
    assert losses.action_ok is False
    assert not verdict.case_passed


def test_loss_row_arithmetic_catches_a_mislabelled_column(control_case):
    produced = oracle(control_case)
    produced.losses[1].paid_usd = 30_000
    verdict = grade(control_case, produced)
    assert not verdict.loss_rows_arithmetic_consistent


def test_truth_record_derives_rather_than_stores(risk):
    assert risk.total_insured_value_usd == 8_400_000
    assert risk.total_incurred_usd == 42_000
    assert risk.total_paid_usd == 16_000
    assert risk.losses[1].incurred_usd == 30_000
    assert "total_insured_value_usd" not in type(risk).model_fields
    assert "incurred_usd" not in type(risk.losses[0]).model_fields


def test_normalisers():
    assert normalise_money("$8,400,000") == 8_400_000
    assert normalise_money(8_400_000) == 8_400_000
    assert normalise_money("not a number") is None
    assert normalise_date("01/01/2027") == "2027-01-01"
    assert normalise_date("2027-01-01") == "2027-01-01"
    assert normalise_date("January 01, 2027") == "2027-01-01"
    assert normalise_date("gibberish") is None
    assert normalise_name("Halsey Street Bakery, LLC") == normalise_name("halsey street bakery llc")


def test_value_matching_is_normalised_not_literal(control_case):
    assert values_match("total_insured_value_usd", 8_400_000, "$8,400,000")
    effective = expected_value(control_case, "policy_effective_date")
    assert values_match("policy_effective_date", effective, "01/01/2027")
    assert values_match("applicant_fein", "47-3918266", "473918266")
    assert not values_match("total_insured_value_usd", 8_400_000, 7_900_000)
    assert not values_match("policy_effective_date", effective, "gibberish")


def test_a_single_spurious_flag_fails_a_case(control_case):
    produced = oracle(control_case)
    from submission_evals.extract import Flagged

    produced.employee_count = Flagged(
        kind="flagged",
        reason="headcount was not clear to me",
        conflicting_sources=[],
        recommended_action=RecommendedAction.QUERY_BROKER,
    )
    verdict = grade(control_case, produced)
    assert verdict.flag_counts["spurious_flag"] == 1
    assert not verdict.case_passed
