from typing import Dict, Any

from capella_console_client.logconf import logger


def print_cancelation_result(results_by_tr_id: Dict[str, Any]):
    tasking_request_ids = list(results_by_tr_id.keys())
    success_trs = [k for k, v in results_by_tr_id.items() if v["success"]]
    cancel_error = {k: v for k, v in results_by_tr_id.items() if not v["success"]}

    if success_trs:
        logger.info(f"{len(success_trs)} out of {len(tasking_request_ids)} tasking requests successfully canceled")

        for tr_id in success_trs:
            logger.info(f"{tr_id:25s}: ✅")

    if cancel_error:
        logger.info(f"{len(cancel_error)} out of {len(tasking_request_ids)} tasking requests could not be canceled")

        for tr_id, cancel_result in cancel_error.items():
            logger.info(f"{tr_id:25s}: {cancel_result['error']} ❌")
