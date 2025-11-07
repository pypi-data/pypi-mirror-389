from __future__ import annotations


import numpy
import warnings


class ReducedFramesInfos:
    """contains reduced frames metadata as count_time and machine_current"""

    MACHINE_ELECT_CURRENT_KEY = "machine_current"

    COUNT_TIME_KEY = "count_time"

    LR_FLIP = "lr_flip"
    """Save the information if the original raw frame was left-right flipped. Warning: tomoscan will only propagate this information but won't flip reduced frames saved"""

    UD_FLIP = "ud_flip"
    """Save the information if the original raw frame was up-down flipped. Warning: tomoscan will only propagate this information but won't flip reduced frames saved"""

    def __init__(self) -> None:
        self._count_time = []
        self._machine_current = []
        self._lr_flip = None
        self._ud_flip = None

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, dict):
            return ReducedFramesInfos().load_from_dict(__o) == self
        if not isinstance(__o, ReducedFramesInfos):
            return False
        return numpy.array_equal(
            numpy.array(self.count_time), numpy.array(__o.count_time)
        ) and numpy.array_equal(
            numpy.array(self.machine_current),
            numpy.array(__o.machine_current),
        )

    def clear(self):
        self._count_time.clear()
        self._machine_current.clear()
        self._lr_flip = None
        self._ud_flip = None

    @property
    def count_time(self) -> list:
        """
        frame exposure time in second
        """
        return self._count_time

    @count_time.setter
    def count_time(self, count_time: list | tuple | numpy.ndarray | None):
        if count_time is None:
            self._count_time.clear()
        else:
            self._count_time = list(count_time)

    @property
    def machine_electric_current(self) -> list:
        warnings.warn(
            "machine_electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.machine_current

    @machine_electric_current.setter
    def machine_electric_current(
        self, machine_current: list | tuple | numpy.ndarray | None
    ):
        warnings.warn(
            "machine_electric_current is deprecated and will be removed in a future version. Use machine_current instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.machine_current = machine_current

    @property
    def machine_current(self) -> list:
        """
        machine electric current in Ampere
        """
        return self._machine_current

    @machine_current.setter
    def machine_current(self, machine_current: list | tuple | numpy.ndarray | None):
        if machine_current is None:
            self._machine_current.clear()
        else:
            self._machine_current = list(machine_current)

    @property
    def lr_flip(self) -> bool | None:
        return self._lr_flip

    @lr_flip.setter
    def lr_flip(self, flip: bool | None):
        if not isinstance(flip, (bool, type(None))):
            raise TypeError(
                f"flip is expected to be None or a bool. got {type(flip)}, {flip}, {flip.dtype}"
            )
        self._lr_flip = flip

    @property
    def ud_flip(self) -> bool | None:
        return self._ud_flip

    @ud_flip.setter
    def ud_flip(self, flip: bool | None):
        if not isinstance(flip, (bool, type(None))):
            raise TypeError(
                f"flip is expected to be None or a bool. got {type(flip)}, {flip}, {flip.dtype}"
            )
        self._ud_flip = flip

    def to_dict(self) -> dict:
        res = {}
        if len(self.machine_current) > 0:
            res[self.MACHINE_ELECT_CURRENT_KEY] = self.machine_current
        if len(self.count_time) > 0:
            res[self.COUNT_TIME_KEY] = self.count_time
        if self.lr_flip is not None:
            res[self.LR_FLIP] = self.lr_flip
        if self.ud_flip is not None:
            res[self.UD_FLIP] = self.ud_flip
        return res

    def load_from_dict(self, my_dict: dict):
        self.machine_current = my_dict.get(self.MACHINE_ELECT_CURRENT_KEY, None)
        self.count_time = my_dict.get(self.COUNT_TIME_KEY, None)

        def cast_numpy_bool(value):
            if isinstance(value, numpy.ndarray):
                return bool(value)
            return value

        self.lr_flip = cast_numpy_bool(my_dict.get(self.LR_FLIP, None))
        self.ud_flip = cast_numpy_bool(my_dict.get(self.UD_FLIP, None))
        return self

    @staticmethod
    def pop_info_keys(my_dict: dict):
        if not isinstance(my_dict, dict):
            raise TypeError
        my_dict.pop(ReducedFramesInfos.MACHINE_ELECT_CURRENT_KEY, None)
        my_dict.pop(ReducedFramesInfos.COUNT_TIME_KEY, None)
        my_dict.pop(ReducedFramesInfos.LR_FLIP, None)
        my_dict.pop(ReducedFramesInfos.UD_FLIP, None)
        return my_dict

    @staticmethod
    def split_data_and_metadata(my_dict):
        metadata = ReducedFramesInfos().load_from_dict(my_dict)
        data = ReducedFramesInfos.pop_info_keys(my_dict)

        def cast_keys_to_int(key):
            try:
                return int(key)
            except ValueError:
                return key

        data = {cast_keys_to_int(key): value for key, value in data.items()}
        return data, metadata

    def __str__(self):
        return "\n".join(
            [
                f"machine_current {self.machine_current}",
                f"count_time {self.count_time}",
                f"lr_flip {self.lr_flip}",
                f"ud_flip {self.ud_flip}",
            ]
        )
