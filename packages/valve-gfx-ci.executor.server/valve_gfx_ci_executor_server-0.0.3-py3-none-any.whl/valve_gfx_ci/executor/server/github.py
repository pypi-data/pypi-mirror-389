from dataclasses import dataclass

from . import config
from .gitlab import requests_session, SanitizedFieldsMixin
from .job_source import JobSourceExternalCommand


@dataclass
class GithubRunnerRegistration(SanitizedFieldsMixin):
    id: int
    encoded_jit_config: str


@dataclass
class Runner(SanitizedFieldsMixin):
    id: int
    name: str
    os: str
    status: str
    busy: bool
    labels: list[str]

    @classmethod
    def from_api(cls, fields, **kwargs):
        # Transform labels from dict format to string format
        if 'labels' in fields:
            fields = dict(fields)  # Make a copy to avoid modifying original
            fields['labels'] = [
                label["name"] for label in fields['labels']
            ]

        return super().from_api(fields, **kwargs)


def _register_runner(github_url: str, authorization_token: str,
                     name: str, labels: list[str],
                     runner_group_id: int) -> GithubRunnerRegistration | None:

    data = {
        "name": name,
        "labels": labels,
        "runner_group_id": runner_group_id,
        "work_folder": "_work",
    }

    r = requests_session.post(f"{github_url}/actions/runners/generate-jitconfig",
                              headers={"Authorization": f"Bearer {authorization_token}"}, json=data)

    if r.status_code == 201:
        # Extract the nested runner data and flatten it
        response_data = r.json()
        flattened_data = {
            "id": response_data["runner"]["id"],
            "encoded_jit_config": response_data["encoded_jit_config"]
        }
        return GithubRunnerRegistration.from_api(flattened_data)
    else:
        return None


def _unregister_runner(github_url: str, authorization_token: str, runner_id: int) -> bool:
    r = requests_session.delete(f"{github_url}/actions/runners/{runner_id}",
                                headers={"Authorization": f"Bearer {authorization_token}"})
    return r.status_code == 204


def _find_runner_by_name(github_url: str, authorization_token: str, name: str) -> GithubRunnerRegistration | None:
    """Find a runner by name and return its ID"""
    r = requests_session.get(f"{github_url}/actions/runners",
                             headers={"Authorization": f"Bearer {authorization_token}"})
    if r.status_code == 200:
        runners = r.json().get('runners', [])
        for runner in runners:
            if runner.get('name') == name:
                return Runner.from_api(runner)
    return None


def _is_runner_online(github_url: str, authorization_token: str, runner_id: int) -> bool:
    """Check if a runner is online"""
    r = requests_session.get(f"{github_url}/actions/runners/{runner_id}",
                             headers={"Authorization": f"Bearer {authorization_token}"})
    if r.status_code == 200:
        runner = Runner.from_api(r.json())
        return runner.status == 'online'

    return False


@dataclass
class GithubJobSource(JobSourceExternalCommand):
    JOB_SOURCE_NAME = "Github"

    runner_id: int = None
    encoded_jit_config: str = None

    def _setup_job(self) -> bool:
        # Use dut_runner's runner_group_id if set, otherwise fall back to gh_instance's default, or 1
        self.runner_group_id = self.db_dut_job_src.runner_group_id
        if self.runner_group_id is None:
            self.runner_group_id = self.job_src.runner_group_id
        if self.runner_group_id is None:
            self.runner_group_id = 1

        # Verify that there are no stale runner registered under our name
        runner = _find_runner_by_name(
            github_url=self.job_src.url,
            authorization_token=self.job_src.authorization_token,
            name=self.db_dut.full_name,
        )

        if runner:
            _unregister_runner(
                github_url=self.job_src.url,
                authorization_token=self.job_src.authorization_token,
                runner_id=runner.id
            )

        # Register runner with JIT config
        runner = _register_runner(
            github_url=self.job_src.url,
            authorization_token=self.job_src.authorization_token,
            name=self.db_dut_job_src.description,
            labels=self.db_dut_job_src.tags,
            runner_group_id=self.runner_group_id
        )

        if not runner:
            return False

        self.runner_id = runner.id
        self.encoded_jit_config = runner.encoded_jit_config.strip()

        return True

    def _try_cancel_job_pickup(self) -> bool:
        # if we can unregister the runner, there is no active job
        return _unregister_runner(
            github_url=self.job_src.url,
            authorization_token=self.job_src.authorization_token,
            runner_id=self.runner_id
        )

    def _runner_job_polling_complete(self) -> bool:
        return _is_runner_online(
            github_url=self.job_src.url,
            authorization_token=self.job_src.authorization_token,
            runner_id=self.runner_id
        )

    def _subprocess_kwargs(self) -> dict[str, str]:
        env = {
            "CI_TRON_JOB_COOKIE": self.job_cookie,
            "CI_TRON_DUT_FULL_NAME": self.db_dut.full_name,
            "PATH": "/usr/bin:/usr/local/bin",
        }

        run_single_command = [
            config.GITHUB_RUNNER_PATH,
            "--jitconfig", self.encoded_jit_config,
        ]
        return {"env": env, "args": run_single_command}
