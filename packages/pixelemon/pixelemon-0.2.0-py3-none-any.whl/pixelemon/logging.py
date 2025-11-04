import logging

pixelemon_LOG = logging.getLogger(__name__)
pixelemon_LOG.setLevel(logging.INFO)


# set logger name
pixelemon_LOG.name = "pixelemon"

# format time to yyyy-mm-ddThh:mm:ss.sss
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
pixelemon_LOG.addHandler(handler)
