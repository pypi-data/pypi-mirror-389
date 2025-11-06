# -*- coding:utf-8 -*-
import logging

from .models import *


logger = logging.getLogger(f"caerp.{__name__}")


def includeme(config):
    logger.debug("- Loading `caerp_sign_pdf` module -")
