from typing import List
from io import StringIO
import pandas as pd


class Artifacts:
    id: str

    @classmethod
    def get_datasets(cls, _transport) -> List[dict]:
        return _transport.get_datasets()

    @classmethod
    def get_models(cls, _transport) -> List[dict]:
        return _transport.get_model()

    @classmethod
    def get_jobs(cls, _transport, job_type) -> List[dict]:
        return _transport.get_jobs(job_type)

    @classmethod
    def get_predictions(cls, _transport, job_id) -> List[dict]:
        t_type = job_id.split("-")[0]
        _r = _transport.get_predictions(job_id, t_type)
        return pd.read_csv(StringIO(_r))

    @classmethod
    def get_metrics(cls, _transport, job_id) -> List[dict]:
        t_type = job_id.split("-")[0]
        _r = _transport.get_job_metrics(job_id, t_type)
        return pd.read_csv(StringIO(_r))

    @classmethod
    def get_status(cls, _transport, job_id) -> List[dict]:
        return _transport.get_job_status(job_id)
