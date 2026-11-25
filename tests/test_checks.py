import pytest

from submission_evals.baselines import flagged, oracle, plausible_liar
from submission_evals.cases import all_specs
from submission_evals.checks import run_all
from submission_evals.generate import packet_text
from submission_evals.truth import RecommendedAction

SPECS = {spec.case.case_id: spec for spec in all_specs()}


@pytest.fixture(params=sorted(SPECS), ids=sorted(SPECS))
def spec(request):
    return SPECS[request.param]


def test_a_correct_record_raises_nothing_blocking(spec):
    findings = run_all(oracle(spec.case), packet_text(spec))
    blocking = [f for f in findings if f.severity == "blocking"]
    assert not blocking, [f.message for f in blocking]


def test_the_liar_is_caught_without_any_ground_truth(spec):
    findings = run_all(plausible_liar(spec.case), packet_text(spec))
    assert any(f.check == "citation_not_supported" for f in findings)


def test_the_unraised_conflict_is_caught_without_ground_truth():
    spec = SPECS["05-application-contradicts-loss-runs"]
    findings = run_all(oracle(spec.case), packet_text(spec))
    assert not any(f.check == "unraised_conflict" for f in findings)

    silent = oracle(spec.case)
    silent.loss_count_5y = type(silent.loss_count_5y)(
        status="extracted",
        value="2",
        mode="read",
        sources=silent.loss_count_5y.sources or [],
        derived_from=[],
        reason="",
        recommended_action=RecommendedAction.NONE,
    )
    findings = run_all(silent, packet_text(spec))
    conflict = [f for f in findings if f.check == "unraised_conflict"]
    assert conflict, "a silent record on the conflict packet must be caught"
    assert conflict[0].severity == "blocking"


def test_a_mislabelled_loss_column_is_caught_arithmetically():
    spec = SPECS["07-loss-run-column-mislabel"]
    produced = oracle(spec.case)
    produced.losses[0].paid_usd = produced.losses[0].incurred_usd
    findings = run_all(produced, packet_text(spec))
    assert any(f.check == "loss_row_does_not_reconcile" for f in findings)


def test_a_total_that_disagrees_with_its_own_rows_is_caught():
    spec = SPECS["02-clean-total-stated"]
    produced = oracle(spec.case)
    produced.total_insured_value_usd.value = "8010000"
    findings = run_all(produced, packet_text(spec))
    assert any(
        f.check == "total_disagrees_with_rows" and f.field == "total_insured_value_usd"
        for f in findings
    )


def test_flagging_the_conflict_clears_it():
    spec = SPECS["05-application-contradicts-loss-runs"]
    produced = oracle(spec.case)
    produced.loss_count_5y = flagged(
        "the application and the loss runs disagree",
        RecommendedAction.QUERY_BROKER,
        [],
    )
    findings = run_all(produced, packet_text(spec))
    assert not any(f.check == "unraised_conflict" for f in findings)
