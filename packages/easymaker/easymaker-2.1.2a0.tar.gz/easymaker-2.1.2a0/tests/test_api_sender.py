import os
from unittest.mock import MagicMock, patch

import pytest
import responses
from requests.exceptions import RetryError

from easymaker.api.api_sender import ApiSender

TEST_REGION = "test_region"
TEST_APPKEY = "test_appkey"
TEST_ACCESS_TOKEN = "test_access_token"


@pytest.fixture(autouse=True)
def cleanup_env():
    """각 테스트 전후로 환경 변수를 정리합니다."""
    # 테스트 전: 환경 변수 백업
    original_env = {}
    for key in ["EM_API_URL", "EM_PROFILE", "EM_ENVIRONMENT_TYPE"]:
        original_env[key] = os.environ.get(key)

    yield

    # 테스트 후: 환경 변수 복원
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@patch("easymaker.api.api_sender.Session")
def test_get_experiment_list_no_params(mock_session):
    os.environ["EM_PROFILE"] = "local"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "header": {
            "isSuccessful": True,
            "resultCode": 0,
            "resultMessage": "SUCCESS",
        },
        "paging": {
            "totalCount": 2,
            "page": 1,
            "limit": 50,
        },
        "experimentList": [
            {
                "experimentId": "1",
                "experimentName": "Experiment 1",
            },
            {
                "experimentId": "2",
                "experimentName": "Experiment 2",
            },
        ],
    }
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response

    api_sender = ApiSender(region=TEST_REGION, appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)
    result = api_sender.get_experiment_list()

    assert result == [{"experimentId": "1", "experimentName": "Experiment 1"}, {"experimentId": "2", "experimentName": "Experiment 2"}]
    mock_session_instance.get.assert_called_with(f"http://127.0.0.1:10090/v1.0/appkeys/{TEST_APPKEY}/experiments", params={})


@patch("easymaker.api.api_sender.Session")
def test_get_experiment_list_with_params(mock_session):
    os.environ["EM_PROFILE"] = "local"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "header": {
            "isSuccessful": True,
            "resultCode": 0,
            "resultMessage": "SUCCESS",
        },
        "paging": {
            "totalCount": 2,
            "page": 1,
            "limit": 50,
        },
        "experimentList": [
            {
                "experimentId": "3",
                "experimentName": "Experiment 3",
            },
            {
                "experimentId": "4",
                "experimentName": "Experiment 4",
            },
        ],
    }
    mock_session_instance = mock_session.return_value
    mock_session_instance.get.return_value = mock_response

    api_sender = ApiSender(region=TEST_REGION, appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)
    result = api_sender.get_experiment_list(name_list=["Experiment 3", "Experiment 4"])

    assert result == [{"experimentId": "3", "experimentName": "Experiment 3"}, {"experimentId": "4", "experimentName": "Experiment 4"}]
    # 실제로는 리스트가 그대로 전달됨
    mock_session_instance.get.assert_called_with(f"http://127.0.0.1:10090/v1.0/appkeys/{TEST_APPKEY}/experiments", params={"experimentNameList": ["Experiment 3", "Experiment 4"]})


@responses.activate
def test_retry_logic():
    os.environ["EM_PROFILE"] = "test"

    # client_ip 조회를 위한 mock 추가
    responses.add(
        responses.GET,
        "http://127.0.0.1:8888/em_client_ip",
        json={"client_ip": "127.0.0.1"},
        status=200,
    )

    responses.add(
        responses.GET,
        f"https://{TEST_REGION}-easymaker-test.api.nhncloudservice.com/v1.0/appkeys/{TEST_APPKEY}/experiments",
        status=503,
    )

    api_sender = ApiSender(region=TEST_REGION, appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

    with pytest.raises(RetryError):
        api_sender.get_experiment_list()

    # client_ip 조회 1번 + 초기 시도 1번 + 재시도 3번 = 총 5번
    assert len(responses.calls) == 5


# URL 생성 로직 테스트
class TestApiUrlGeneration:
    """API URL 생성 로직을 테스트합니다."""

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_custom_api_url(self, mock_requests_get, mock_session):
        """EM_API_URL 환경 변수가 설정되면 해당 URL을 사용합니다."""
        os.environ["EM_API_URL"] = "https://custom-url.com"

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://custom-url.com"

    @patch("easymaker.api.api_sender.Session")
    def test_local_environment(self, mock_session):
        """local 환경에서는 localhost URL을 사용합니다."""
        os.environ["EM_PROFILE"] = "local"

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "http://127.0.0.1:10090"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_public_real_environment(self, mock_requests_get, mock_session):
        """public real 환경에서 올바른 URL을 생성합니다."""
        os.environ.pop("EM_PROFILE", None)
        os.environ.pop("EM_ENVIRONMENT_TYPE", None)

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://kr1-easymaker.api.nhncloudservice.com"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_public_alpha_environment(self, mock_requests_get, mock_session):
        """public alpha 환경에서 올바른 URL을 생성합니다."""
        os.environ["EM_PROFILE"] = "alpha"
        os.environ.pop("EM_ENVIRONMENT_TYPE", None)

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://kr1-easymaker-alpha.api.nhncloudservice.com"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_public_beta_environment(self, mock_requests_get, mock_session):
        """public beta 환경에서 올바른 URL을 생성합니다."""
        os.environ["EM_PROFILE"] = "beta"
        os.environ.pop("EM_ENVIRONMENT_TYPE", None)

        api_sender = ApiSender(region="kr3", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://kr3-easymaker-beta.api.nhncloudservice.com"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_gov_real_environment(self, mock_requests_get, mock_session):
        """gov real 환경에서 올바른 URL을 생성합니다."""
        os.environ.pop("EM_PROFILE", None)
        os.environ["EM_ENVIRONMENT_TYPE"] = "gov"

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://kr1-easymaker.api.gov-nhncloudservice.com"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_gov_beta_environment(self, mock_requests_get, mock_session):
        """gov beta 환경에서 올바른 URL을 생성합니다."""
        os.environ["EM_PROFILE"] = "beta"
        os.environ["EM_ENVIRONMENT_TYPE"] = "gov"

        api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

        assert api_sender._easymakerApiUrl == "https://kr1-easymaker-beta.api.gov-nhncloudservice.com"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_case_insensitive_environment_type(self, mock_requests_get, mock_session):
        """environment_type이 대소문자 구분 없이 처리됩니다."""
        test_cases = [
            ("GOV", "https://kr1-easymaker.api.gov-nhncloudservice.com"),
            ("Gov", "https://kr1-easymaker.api.gov-nhncloudservice.com"),
            ("gov", "https://kr1-easymaker.api.gov-nhncloudservice.com"),
            ("PUBLIC", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("Public", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("public", "https://kr1-easymaker.api.nhncloudservice.com"),
        ]

        for env_type, expected_url in test_cases:
            os.environ["EM_ENVIRONMENT_TYPE"] = env_type
            os.environ.pop("EM_PROFILE", None)

            api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

            assert api_sender._easymakerApiUrl == expected_url, f"Failed for EM_ENVIRONMENT_TYPE={env_type}"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_case_insensitive_profile(self, mock_requests_get, mock_session):
        """profile이 대소문자 구분 없이 처리됩니다."""
        test_cases = [
            ("ALPHA", "https://kr1-easymaker-alpha.api.nhncloudservice.com"),
            ("Alpha", "https://kr1-easymaker-alpha.api.nhncloudservice.com"),
            ("alpha", "https://kr1-easymaker-alpha.api.nhncloudservice.com"),
            ("BETA", "https://kr1-easymaker-beta.api.nhncloudservice.com"),
            ("Beta", "https://kr1-easymaker-beta.api.nhncloudservice.com"),
            ("beta", "https://kr1-easymaker-beta.api.nhncloudservice.com"),
            ("REAL", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("Real", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("real", "https://kr1-easymaker.api.nhncloudservice.com"),
        ]

        for profile, expected_url in test_cases:
            os.environ["EM_PROFILE"] = profile
            os.environ.pop("EM_ENVIRONMENT_TYPE", None)

            api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

            assert api_sender._easymakerApiUrl == expected_url, f"Failed for EM_PROFILE={profile}"

    @patch("easymaker.api.api_sender.Session")
    def test_case_insensitive_local_profile(self, mock_session):
        """local profile이 대소문자 구분 없이 처리됩니다."""
        test_cases = ["LOCAL", "Local", "local", "LoCaL"]

        for profile in test_cases:
            os.environ["EM_PROFILE"] = profile

            api_sender = ApiSender(region="kr1", appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

            assert api_sender._easymakerApiUrl == "http://127.0.0.1:10090", f"Failed for EM_PROFILE={profile}"

    @patch("easymaker.api.api_sender.Session")
    @patch("easymaker.api.api_sender.requests.get")
    def test_case_insensitive_region(self, mock_requests_get, mock_session):
        """region이 대소문자 구분 없이 처리됩니다."""
        test_cases = [
            ("KR1", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("Kr1", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("kr1", "https://kr1-easymaker.api.nhncloudservice.com"),
            ("KR3", "https://kr3-easymaker.api.nhncloudservice.com"),
        ]

        for region, expected_url in test_cases:
            os.environ.pop("EM_PROFILE", None)
            os.environ.pop("EM_ENVIRONMENT_TYPE", None)

            api_sender = ApiSender(region=region, appkey=TEST_APPKEY, access_token=TEST_ACCESS_TOKEN)

            assert api_sender._easymakerApiUrl == expected_url, f"Failed for region={region}"
