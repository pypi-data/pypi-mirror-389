"""
验证在执行器修复后，teardown 阶段仍能访问注入的上下文变量。
"""

from textwrap import dedent

from pytest_dsl.core.dsl_executor import DSLExecutor


def test_teardown_can_access_injected_context(monkeypatch):
    """执行器应在 teardown 开始前保留上下文变量。"""
    monkeypatch.setenv('PYTEST_DSL_KEEP_VARIABLES', '1')

    executor = DSLExecutor(enable_hooks=False, enable_tracking=False)
    dsl_content = dedent(
        """
        injected_copy = injected_var

        teardown do
            teardown_seen = injected_var
        end
        """
    ).strip()

    context = {'injected_var': 'context_value'}

    executor.execute_from_content(
        dsl_content,
        dsl_id='teardown_context_test',
        context=context,
    )

    assert executor.variables['injected_copy'] == 'context_value'
    assert executor.variables['teardown_seen'] == 'context_value'
