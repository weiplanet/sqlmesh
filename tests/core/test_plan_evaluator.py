import pytest
from pytest_mock.plugin import MockerFixture
from sqlglot import parse_one

from sqlmesh.core.context import Context
from sqlmesh.core.model import FullKind, SqlModel, ViewKind
from sqlmesh.core.plan import (
    AirflowPlanEvaluator,
    BuiltInPlanEvaluator,
    MWAAPlanEvaluator,
    Plan,
)
from sqlmesh.core.snapshot import SnapshotChangeCategory
from sqlmesh.utils.errors import SQLMeshError


@pytest.fixture
def sushi_plan(sushi_context: Context, mocker: MockerFixture) -> Plan:
    mock_prompt = mocker.Mock()
    mock_prompt.ask.return_value = "2022-01-01"
    mocker.patch("sqlmesh.core.console.Prompt", mock_prompt)

    return Plan(
        sushi_context._context_diff("dev"),
        is_dev=True,
        include_unmodified=True,
    )


def test_builtin_evaluator_push(sushi_context: Context, make_snapshot):
    new_model = SqlModel(
        name="sushi.new_test_model",
        kind=FullKind(),
        owner="jen",
        cron="@daily",
        start="2020-01-01",
        query=parse_one("SELECT 1::INT AS one"),
    )
    new_view_model = SqlModel(
        name="sushi.new_test_view_model",
        kind=ViewKind(),
        owner="jen",
        start="2020-01-01",
        query=parse_one("SELECT 1::INT AS one FROM sushi.new_test_model, sushi.waiters"),
    )

    sushi_context.upsert_model(new_model)
    sushi_context.upsert_model(new_view_model)

    snapshots = sushi_context.snapshots
    new_model_snapshot = snapshots[new_model.name]
    new_view_model_snapshot = snapshots[new_view_model.name]

    new_model_snapshot.categorize_as(SnapshotChangeCategory.BREAKING)
    new_view_model_snapshot.categorize_as(SnapshotChangeCategory.BREAKING)

    plan = Plan(
        sushi_context._context_diff("prod"),
    )

    evaluator = BuiltInPlanEvaluator(
        sushi_context.state_sync,
        sushi_context.snapshot_evaluator,
        console=sushi_context.console,
    )
    evaluator._push(plan)

    assert (
        len(sushi_context.state_sync.get_snapshots([new_model_snapshot, new_view_model_snapshot]))
        == 2
    )
    assert sushi_context.engine_adapter.table_exists(new_model_snapshot.table_name())
    assert sushi_context.engine_adapter.table_exists(new_view_model_snapshot.table_name())


def test_airflow_evaluator(sushi_plan: Plan, mocker: MockerFixture):
    airflow_client_mock = mocker.Mock()
    airflow_client_mock.wait_for_dag_run_completion.return_value = True
    airflow_client_mock.wait_for_first_dag_run.return_value = "test_plan_application_dag_run_id"

    evaluator = AirflowPlanEvaluator(airflow_client_mock)
    evaluator.evaluate(sushi_plan)

    airflow_client_mock.apply_plan.assert_called_once_with(
        sushi_plan.new_snapshots,
        sushi_plan.environment,
        mocker.ANY,
        no_gaps=False,
        notification_targets=[],
        restatements={},
        backfill_concurrent_tasks=1,
        ddl_concurrent_tasks=1,
        skip_backfill=False,
        users=[],
        is_dev=True,
        forward_only=False,
    )

    airflow_client_mock.wait_for_dag_run_completion.assert_called_once()
    airflow_client_mock.wait_for_first_dag_run.assert_called_once()


def test_airflow_evaluator_plan_application_dag_fails(sushi_plan: Plan, mocker: MockerFixture):
    airflow_client_mock = mocker.Mock()
    airflow_client_mock.wait_for_dag_run_completion.return_value = False
    airflow_client_mock.wait_for_first_dag_run.return_value = "test_plan_application_dag_run_id"

    evaluator = AirflowPlanEvaluator(airflow_client_mock)

    with pytest.raises(SQLMeshError):
        evaluator.evaluate(sushi_plan)

    airflow_client_mock.apply_plan.assert_called_once()
    airflow_client_mock.wait_for_dag_run_completion.assert_called_once()
    airflow_client_mock.wait_for_first_dag_run.assert_called_once()


def test_mwaa_evaluator(sushi_plan: Plan, mocker: MockerFixture):
    mwaa_client_mock = mocker.Mock()
    mwaa_client_mock.wait_for_dag_run_completion.return_value = True
    mwaa_client_mock.wait_for_first_dag_run.return_value = "test_plan_application_dag_run_id"
    mwaa_client_mock.set_variable.return_value = "", ""

    state_sync_mock = mocker.Mock()

    plan_dag_spec_json = """{"request_id": "test_request_id"}"""

    plan_dag_spec_mock = mocker.Mock()
    plan_dag_spec_mock.json.return_value = plan_dag_spec_json

    create_plan_dag_spec_mock = mocker.patch("sqlmesh.schedulers.airflow.plan.create_plan_dag_spec")
    create_plan_dag_spec_mock.return_value = plan_dag_spec_mock

    evaluator = MWAAPlanEvaluator(mwaa_client_mock, state_sync_mock)
    evaluator.evaluate(sushi_plan)

    mwaa_client_mock.set_variable.assert_called_once_with(mocker.ANY, plan_dag_spec_json)

    mwaa_client_mock.wait_for_dag_run_completion.assert_called_once()
    mwaa_client_mock.wait_for_first_dag_run.assert_called_once()


def test_mwaa_evaluator_error_from_cli(sushi_plan: Plan, mocker: MockerFixture):
    mwaa_client_mock = mocker.Mock()
    mwaa_client_mock.wait_for_dag_run_completion.return_value = True
    mwaa_client_mock.wait_for_first_dag_run.return_value = "test_plan_application_dag_run_id"
    mwaa_client_mock.set_variable.return_value = "", "Error"

    state_sync_mock = mocker.Mock()

    plan_dag_spec_json = """{"request_id": "test_request_id"}"""

    plan_dag_spec_mock = mocker.Mock()
    plan_dag_spec_mock.json.return_value = plan_dag_spec_json

    create_plan_dag_spec_mock = mocker.patch("sqlmesh.schedulers.airflow.plan.create_plan_dag_spec")
    create_plan_dag_spec_mock.return_value = plan_dag_spec_mock

    evaluator = MWAAPlanEvaluator(mwaa_client_mock, state_sync_mock)

    with pytest.raises(SQLMeshError, match=r"Failed to submit a plan application request:\nError"):
        evaluator.evaluate(sushi_plan)

    mwaa_client_mock.set_variable.assert_called_once_with(mocker.ANY, plan_dag_spec_json)
