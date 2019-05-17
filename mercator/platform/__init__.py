class Platform(object):
    def __init__(self, config, *args):
        raise NotImplementedError()

    def setup_measurement(self, config):
        raise NotImplementedError()
