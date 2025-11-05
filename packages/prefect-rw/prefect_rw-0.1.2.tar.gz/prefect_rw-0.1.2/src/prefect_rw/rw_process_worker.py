import contextlib
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import anyio.abc
from prefect import get_client
from prefect.deployments.steps.core import run_steps
from prefect.workers.process import ProcessJobConfiguration, ProcessWorker, ProcessWorkerResult

if TYPE_CHECKING:
    from prefect.client.schemas.objects import FlowRun


error_msg_deployment_id = "Deployment ID not found"
error_pull_steps = "Pull steps not found - configure your deployment correctly to work with prefect_rw"
error_command = "Command not set - configure your workpool correctly to work with prefect_rw"


async def run(
    self: ProcessWorker,
    flow_run: "FlowRun",
    configuration: ProcessJobConfiguration,
    task_status: anyio.abc.TaskStatus[int] | None = None,
) -> ProcessWorkerResult:
    if task_status is None:
        task_status = anyio.TASK_STATUS_IGNORED

    working_dir_ctx = (
        tempfile.TemporaryDirectory(suffix="prefect")
        if not configuration.working_dir
        else contextlib.nullcontext(configuration.working_dir)
    )
    with working_dir_ctx as working_dir:
        if not flow_run.deployment_id:
            raise RuntimeError(error_msg_deployment_id)
        async with get_client() as client:
            deployment = await client.read_deployment(flow_run.deployment_id)
        os.environ["_CWD"] = str(working_dir)
        os.environ["WORKER_RUNNING"] = "1"
        if not deployment.pull_steps:
            raise RuntimeError(error_pull_steps)
        step_results = await run_steps(deployment.pull_steps)
        os.environ["WORKER_RUNNING"] = ""
        if not configuration.command:
            raise RuntimeError(error_command)
        configuration.command = configuration.command.format(step_results["dir"])

        process = await self._runner.execute_flow_run(
            flow_run_id=flow_run.id,
            command=configuration.command,
            cwd=Path(working_dir) / step_results["dir"],
            env=configuration.env,
            stream_output=configuration.stream_output,
            task_status=task_status,
        )

        if process is None or process.returncode is None:
            msg = "Failed to start flow run process."
            raise RuntimeError(msg)

    return ProcessWorkerResult(status_code=process.returncode, identifier=str(process.pid))
