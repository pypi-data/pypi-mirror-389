import pytest
from xraybot import XrayBot, TestEntity, TestResultEntity, XrayResultType

local_tests = [
    TestEntity(
        key="XT-6353",
        summary="foo1",
        description="desc",
        repo_path=["foo", "2nd folder", "inner"],
        unique_identifier="tests.function.foo1",
    ),
    TestEntity(
        key="XT-6354",
        summary="foo2",
        description="desc",
        repo_path=["foo", "2nd folder"],
        unique_identifier="tests.function.foo2",
        labels=["foo", "bar"],
        req_keys=["XT-5380", "XT-5457"],
        defect_keys=["XT-6339", "XT-6338"]
    ),
    TestEntity(
        key="XT-6355",
        summary="foo3",
        description="desc",
        repo_path=["bar"],
        unique_identifier="tests.function.foo3",
        labels=["foo"],
        req_keys=["XT-5380"],
        defect_keys=["XT-6339"]
    ),
    TestEntity(
        key="XT-5791",
        summary="foo4",
        description="desc",
        repo_path=["bar"],
        unique_identifier="tests.function.foo4",
        labels=["bar"],
        req_keys=["XT-5380"]
    ),
    TestEntity(
        key="XT-6205",
        summary="foo5",
        description="desc",
        unique_identifier="tests.function.foo5",
        labels=["bar"],
        req_keys=["XT-5380"]
    )
]
test_results = [
    TestResultEntity(
        key="XT-6353",
        result=XrayResultType.FAILED
    ),
    TestResultEntity(
        key="XT-6205",
        result=XrayResultType.PASSED
    )
]
class TestXrayBot:
    @pytest.fixture(scope="class")
    def bot(self, jira_url, jira_username, jira_pwd, project_key) -> XrayBot:
        bot = XrayBot(jira_url, jira_username, jira_pwd, project_key)
        bot.config.configure_automation_folder_name("My Automation Test Folder")
        bot.configure_custom_field("Test Type", "Automated")
        return bot

    def test_create_tests_draft(self, bot):
        bot.create_tests_draft(local_tests)

    def test_sync_tests(self, bot):
        bot.sync_tests(local_tests)

    def test_get_xray_tests(self, bot):
        results = bot.get_xray_tests()
        assert results

    def test_sync_check(self, bot):
        bot.sync_check(local_tests)

    def test_upload_test_results(self, bot):
        bot.upload_test_results(
            "my test plan 1019",
            "my test execution 1019",
            test_results,
            ignore_missing=True,
            clean_obsolete=True
        )

    def test_upload_test_results_by_key(self, bot):
        bot.upload_test_results_by_key(
            "XT-6358",
            test_results,
            "XT-6356",
            full_test_set=True,
            clean_obsolete=True,
        )