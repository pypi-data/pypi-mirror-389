from collections.abc import Iterable

from asgikit._constants import HEADER_ENCODING
from asgikit.multi_value_dict import MultiValueDict, MutableMultiValueDict, T


class Headers(MultiValueDict[str]):
    def __init__(
        self, data: Iterable[tuple[bytes, bytes]] | dict[str, str | list[str]]
    ):
        if not data:
            super().__init__()
            return

        if isinstance(data, dict):

            def _items():
                for key, value in data.items():
                    if isinstance(value, list):
                        yield from ((key, v) for v in value)
                    else:
                        yield key, value

            data = list(_items())
        else:
            data = [
                (key.decode(HEADER_ENCODING).lower(), value.decode(HEADER_ENCODING))
                for key, value in data
            ]

        super().__init__(data)

    def encode(self) -> Iterable[tuple[bytes, bytes]]:
        for name, value in self.items():
            encoded_name = name.encode(HEADER_ENCODING)
            encoded_value = ", ".join(value).encode(HEADER_ENCODING)
            yield encoded_name, encoded_value

    def get_first(self, key: str, default: T = None) -> T | None:
        return super().get_first(key.lower(), default)

    def get(self, key: str, default: T = None) -> T | None:
        return self.get_first(key, default)

    def get_all(self, key: str, default: list[T] = None) -> list[T] | None:
        return super().get(key.lower(), default)

    def __getitem__(self, key: str) -> str:
        if data := super().get_first(key.lower()):
            return data
        raise KeyError(key)


class MutableHeaders(MutableMultiValueDict[str], Headers):
    def __init__(self):
        super().__init__([])

    def add(self, key: str, value: str):
        super().add(key.lower(), value)

    def set(self, key: str, value: str | list[str]):
        super().set(key.lower(), value)

    def __setitem__(self, key: str, value: str | list[str]):
        self.set(key, value)

    def __delitem__(self, key: str):
        super().__delitem__(key.lower())
