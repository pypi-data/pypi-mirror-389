import time
from typing import Optional, Any, TypedDict, List

from ..common import utils
from ..common.svc import Svc
from ..common.utils import StrEnum, json


class EJobStatus(StrEnum):
    waiting = "waiting"
    launched = "launched"
    pending = "pending"
    done = "done"
    failed = "failed"
    planned = "planned"


class EJobSuccess(StrEnum):
    finished = "finished"  # job abouti
    finalFailure = "finalFailure"  # Échec définitif, inutile de lancer une nouvelle tentative.
    attemptFailed = "attemptFailed"  # Échec de cette tentative. Peut être retenté ultérieurement.


class JJobBase(TypedDict):
    id: str
    jobSgn: Optional[str]
    created: int
    createdBy: str
    lastQueued: int
    lastStatus: EJobStatus
    planned: Optional[int]


class JJobResult(TypedDict):
    success: EJobSuccess
    system: Optional[Any]


class JJobPropsTry(TypedDict):
    started: int
    finished: int
    by: Optional[str]
    status: EJobStatus
    result: Optional[JJobResult]
    error: str


class JJob(JJobBase):
    tries: Optional[List[JJobPropsTry]]
    jobProps: Optional[Any]


class Executor(Svc):
    def create_job(self, job: str, job_data: Any = None) -> JJob:
        qs = {"cdaction": "CreateJob", "param": job}
        if job_data is not None:
            qs["jobDatas"] = utils.serialize_cdm(job_data)
        return json(self._s.put(self._url, params=qs))

    def get_job(self, job_id: str) -> JJob:
        return json(self._s.get(self._url, params={"cdaction": "GetJob", "jobId": job_id}))

    def wait_for_job(self, job: JJob) -> JJob:
        job = self.get_job(job["id"])
        while job["lastStatus"] in [EJobStatus.waiting.value, EJobStatus.launched.value, EJobStatus.pending.value, EJobStatus.planned.value]:
            time.sleep(1)
            job = self.get_job(job['id'])
        return job

    def create_and_wait_for_job(self, job: str, job_data: Any = None) -> JJob:
        job: JJob = self.create_job(job, job_data)
        return self.wait_for_job(job)
