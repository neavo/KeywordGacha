class BaseData():

    _TYPE_FILTER = (int, str, bool, float, list, dict, tuple)

    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.get_vars()})"

    def get_vars(self) -> dict:
        return {
            k: v
            for k, v in vars(self).items()
            if isinstance(v, BaseData._TYPE_FILTER)
        }