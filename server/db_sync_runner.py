import time
from dbSync.Runner import start_sync, stop_sync
from Core.app_logging import get_logger

logger = get_logger(__name__)

if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description="Запуск синхронизации для device_id")
    # parser.add_argument("device_id", type=int, help="ID устройства для синхронизации")
    # args = parser.parse_args()

    start_sync(1)#args.device_id
    try:
        # держим основной процесс живым, пока не Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_sync(1)#args.device_id
        logger.info("Выход.")
