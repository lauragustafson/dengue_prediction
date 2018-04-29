#!/usr/bin/env python

import logging
import sys

import click

import dengue_prediction.features.travis as travis
from dengue_prediction.features.validate_features import (
    PullRequestFeatureValidator )

logger = logging.getLogger(__name__)

@click.command()
@click.argument('pr_num', required=False, default=None, type=int)
def main(pr_num=None):

    RETVAL_VALID = 0
    RETVAL_NOT_PR = 1
    RETVAL_INVALID = 2

    if pr_num is None:
        logger.info('No PR provided. Trying to detect PR from Travis ENV.')
        pr_num = travis.get_pr_num()
        if pr_num is None:
            logger.info('Could not detect PR. Exiting...')
            return RETVAL_NOT_PR
        else:
            logger.info('Detected PR {}'.format(pr_num))

    logger.info('Validating PR {}...'.format(pr_num))

    validator = PullRequestFeatureValidator(pr_num)
    result = validator.validate()

    if result is True:
        return RETVAL_VALID
    else:
        return RETVAL_INVALID

if __name__ == '__main__':
    _logger = logging.getLogger('dengue_prediction')
    _logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    _logger.addHandler(handler)
    sys.exit(main())
