import pytest

from submission_evals.baselines import flag_everything, null_empty, oracle, plausible_liar
from submission_evals.cases import all_specs
from submission_evals.extract import GRADED_FIELDS
from submission_evals.generate import build_packet, packet_text
from submission_evals.grade import expected_value, grade, renderings
from submission_evals.truth import DocumentName, SourceMode

SPECS = all_specs()
IDS = [spec.case.case_id for spec in SPECS]

DERIVED_BY_NATURE = frozenset(
    {
        "total_insured_value_usd",
        "location_count",
        "loss_count_5y",
        "total_paid_5y_usd",
        "total_incurred_5y_usd",
        "is_update_of_prior_submission",
        "mailing_address",
    }
)


@pytest.fixture(params=SPECS, ids=IDS)
def spec(request):
    return request.param


def test_every_read_field_actually_appears_in_the_packet(spec):
    case = spec.case
    text = packet_text(spec)
    missing = []
    for field in GRADED_FIELDS:
        expectation = case.expectation_for(field)
        if expectation is not None and expectation.outcome == "flagged":
            continue
        if expectation is not None and expectation.source_mode == SourceMode.DERIVED:
            continue
        if expectation is None and field in DERIVED_BY_NATURE:
            continue
        wanted = expected_value(case, field)
        forms = renderings(field, wanted)
        if expectation is not None and expectation.source_document is not None:
            body = text[expectation.source_document]
            if not any(form in body for form in forms):
                missing.append(f"{field}={wanted!r} not in {expectation.source_document.value}")
            continue
        if not any(form in body for body in text.values() for form in forms):
            missing.append(f"{field}={wanted!r} not in any document")
    assert not missing, f"{case.case_id}: {missing}"


def test_oracle_passes_every_case_against_the_real_documents(spec):
    verdict = grade(spec.case, oracle(spec.case), packet_text=packet_text(spec))
    failures = [f.detail for f in verdict.fields if not _field_ok(f)]
    assert verdict.case_passed, f"{spec.case.case_id}: {failures}"
    assert verdict.value_score == 1.0
    assert verdict.provenance_score == 1.0
    assert verdict.location_rows_correct
    assert verdict.loss_rows_correct
    assert verdict.loss_rows_arithmetic_consistent


def _field_ok(verdict) -> bool:
    if verdict.value_correct is False:
        return False
    if verdict.provenance is not None and not verdict.provenance.ok:
        return False
    return verdict.flag_decision in ("correctly_flagged", "correctly_not_flagged")


def test_plausible_liar_never_passes(spec):
    verdict = grade(spec.case, plausible_liar(spec.case), packet_text=packet_text(spec))
    assert not verdict.case_passed
    assert verdict.provenance_score < 1.0


def test_null_empty_never_passes(spec):
    verdict = grade(spec.case, null_empty(spec.case), packet_text=packet_text(spec))
    assert not verdict.case_passed


def test_flag_everything_never_passes(spec):
    verdict = grade(spec.case, flag_everything(spec.case), packet_text=packet_text(spec))
    assert not verdict.case_passed


def test_controls_expect_no_flags_and_adversarial_cases_are_tagged(spec):
    case = spec.case
    if case.kind == "control":
        assert case.exercises is None
        assert case.should_flag_fields == ()
    else:
        assert case.exercises is not None


def test_every_expectation_carries_a_citation(spec):
    for expectation in spec.case.expectations:
        assert expectation.rationale.strip()
        assert expectation.rationale_source.startswith("https://")


def test_the_corruptions_actually_changed_the_documents():
    by_id = {spec.case.case_id: spec for spec in SPECS}

    stated = packet_text(by_id["02-clean-total-stated"])
    derived = packet_text(by_id["06-derived-total"])
    assert "8,400,000" in stated[DocumentName.BROKER_EMAIL]
    assert not any("8,400,000" in body for body in derived.values())

    stale = packet_text(by_id["04-stale-thread"])
    email = stale[DocumentName.BROKER_EMAIL]
    assert email.index("7,900,000") < email.index("8,400,000")

    conflict = packet_text(by_id["05-application-contradicts-loss-runs"])
    assert "CHK HERE IF NONE: [X]" in conflict[DocumentName.APPLICATION]
    assert "884213" in conflict[DocumentName.LOSS_RUN_A]

    mislabel = by_id["07-loss-run-column-mislabel"]
    body = packet_text(mislabel)[DocumentName.LOSS_RUN_B]
    assert "30,000      26,000" in body.replace("        ", "      ")

    paged = packet_text(by_id["08-sov-page-break"])
    assert "\f" in paged[DocumentName.SOV]
    assert paged[DocumentName.SOV].count("STATEMENT OF VALUES") == 2

    assert DocumentName.LOSS_RUN_A not in packet_text(by_id["09-missing-loss-runs"])
    assert DocumentName.NO_LOSSES_LETTER in packet_text(by_id["03-clean-no-losses-letter"])


def test_packet_documents_match_the_declared_manifest(spec):
    assert set(build_packet(spec)) == set(spec.case.documents)


def test_the_email_lists_what_is_actually_attached(spec):
    from submission_evals.manifest import ATTACHMENT_NAMES

    email = packet_text(spec)[DocumentName.BROKER_EMAIL]
    for name in spec.case.documents:
        if name in ATTACHMENT_NAMES:
            assert ATTACHMENT_NAMES[name] in email, f"{spec.case.case_id} omits {name.value}"
    absent = set(DocumentName) - set(spec.case.documents)
    for name in absent:
        if name in ATTACHMENT_NAMES:
            assert ATTACHMENT_NAMES[name] not in email
