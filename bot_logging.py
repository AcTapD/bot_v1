# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='log_test.log', datefmt='%d.%m.%Y %H:%M:%S', level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def log_info(info):
    logger.info(f'{info}')
    return


def log_error(eRR):
    logger.error(f'{eRR}')
    return