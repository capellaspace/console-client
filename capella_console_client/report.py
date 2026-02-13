from typing import Dict, Any

from capella_console_client.logconf import logger


def print_cancelation_result(results_by_tr_id: Dict[str, Any], task_type: str):
    cancel_ids = list(results_by_tr_id.keys())
    success_ids = [k for k, v in results_by_tr_id.items() if v["success"]]
    cancel_error = {k: v for k, v in results_by_tr_id.items() if not v["success"]}

    if success_ids:
        logger.info(f"{len(success_ids)} out of {len(cancel_ids)} {task_type} requests successfully canceled")

        for _id in success_ids:
            logger.info(f"{_id:25s}: ✅")

    if cancel_error:
        logger.info(f"{len(cancel_error)} out of {len(cancel_ids)} {task_type} requests could not be canceled")

        for _id, cancel_result in cancel_error.items():
            logger.info(f"{_id:25s}: {cancel_result['error']} ❌")


def print_task_search_result(trs):
    if not trs:
        logger.info(f"found no tasking requests matching search query")
    else:
        multiple_suffix = "s" if len(trs) > 1 else ""
        logger.info(f"found {len(trs)} tasking request{multiple_suffix} matching search query")
