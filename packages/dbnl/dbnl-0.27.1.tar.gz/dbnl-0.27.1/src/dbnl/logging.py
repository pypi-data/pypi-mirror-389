import sys
from logging import StreamHandler, getLogger

logger = getLogger("dbnl")
logger.addHandler(StreamHandler(stream=sys.stdout))
