# Adapted from: https://github.com/HarrisonTotty/tmpl/blob/master/src/tmpl/utils.py

import logging

def setup_logging( args: any ):
    # good for live debugging
    f_simple = '[%(levelname)s] [%(module)s.%(funcName)s(%(lineno)d)] %(message)s'
    # add timestamps for file logging
    f_file = '[%(levelname)s] [%(asctime)s] [%(module)s.%(funcName)s(%(lineno)d)] %(message)s'
    # add process information ?why?
    f_process = '[%(levelname)s] [%(asctime)s] [%(process)d] [%(module)s.%(funcName)s] %(message)s'
    enable_logging = False
    params = {
        'level': logging.WARNING,
        'format': f_simple,
        'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    if args.debug:
        enable_logging = True
        params[ 'level' ] = logging.DEBUG
    elif args.verbose:
        enable_logging = True
        params[ 'level' ] = logging.INFO

    log_file = getattr( args, 'log_file', None )
    if log_file:
        enable_logging = True
        params[ 'filename' ] = log_file

    if enable_logging:
        logging.basicConfig( **params )
        # logging.addLevelName(logging.CRITICAL, 'FATAL')
        # logging.addLevelName(logging.ERROR, 'ERROR')
        # logging.addLevelName(logging.WARNING, 'WARNG')
        # logging.addLevelName(logging.INFO, 'INFO')
        # logging.addLevelName(logging.DEBUG, 'DEBUG')
    else:
        logger = logging.getLogger()
        logger.disabled = True

