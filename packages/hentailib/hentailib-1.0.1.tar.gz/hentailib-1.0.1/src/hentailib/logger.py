import logging
import sys


def setup_logging(debug=False):

    # Очищаем предыдущие настройки
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler('app.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Вывод в консоль
            ]
        )
        logging.getLogger().info("Логирование в debug режиме включено")
    else:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger().setLevel(logging.ERROR)


def get_logger(name):
    return logging.getLogger(name)