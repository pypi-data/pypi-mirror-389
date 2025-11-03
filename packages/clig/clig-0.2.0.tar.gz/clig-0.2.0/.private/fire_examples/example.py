import fire


class BrokenCalculator(object):

    def __init__(self, offset=1):
        self._offset = offset

    def add(self, x, y):
        return x + y + self._offset

    def multiply(self, x, y, *args, **kwargs):
        return x * y + self._offset


if __name__ == "__main__":
    fire.Fire(BrokenCalculator)
