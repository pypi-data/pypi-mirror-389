from _typeshed import Incomplete
from minjiang_client.experiment.result import Result

def convert_timestamp_to_datetime(timestamp_str): ...

class ExperimentConfig:
    direct_exp_id: int
    config: Incomplete
    created_at: Incomplete
    terminated: bool
    def __init__(self, direct_exp_id: int, config_data: dict) -> None: ...

class ExperimentResult:
    result: Result
    created_at: Incomplete
    expires_at: Incomplete
    def __init__(self, result: Result) -> None: ...

class DirectLinkManager:
    direct_exp_queue: Incomplete
    results: dict[int, ExperimentResult]
    lock: Incomplete
    cleanup_interval: int
    cloud_group: Incomplete
    terminate_list: Incomplete
    def __init__(self, group_name: str) -> None: ...
    def add_exp(self, config_data: dict) -> int: ...
    def get_next_direct_exp(self) -> dict | None: ...
    def add_result(self, direct_exp_id: int, result_data: dict): ...
    def get_result(self, direct_exp_id: int) -> dict | None: ...
    def terminate_direct_exp(self, direct_exp_id: int) -> bool: ...
