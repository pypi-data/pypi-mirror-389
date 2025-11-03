import abc
from typing import Literal


class VarGroup:
    """Construct a variable group"""

    def __init__(self, values: list[tuple[str, str]]):
        self._vars = sorted(values, key=lambda val: val[0])

    def as_dict(self) -> dict[str, dict | str]:
        content = {}
        key = None
        vars = []
        for val in self._vars:
            items = val[0].split(".")
            if len(items) == 1:
                content[items[0]] = val[1]
                continue

            if items[0] != key:
                if vars:
                    content[key] = VarGroup(vars).as_dict()
                key = items[0]
                vars = []

            vars.append((".".join(items[1:]), val[1]))

        if vars:
            content[key] = VarGroup(vars).as_dict()

        return content

    def merge(self, other: "VarGroup") -> "VarGroup":
        vars = {val[0]: val[1] for val in self._vars}
        for var in other._vars:
            vars[var[0]] = var[1]

        return VarGroup([(key, val) for key, val in vars.items()])

    def __bool__(self) -> bool:
        return bool(self._vars)


class VarsReader(abc.ABC):
    """Interface to access to variables in a store"""

    @abc.abstractmethod
    def list_vars(self) -> list[str]:
        """List all available keys in the store"""

    @abc.abstractmethod
    def read(self, key: str) -> str | None:
        """Return the value of a key, it doesn't exist return None"""


class VariableNotFound(Exception):
    def __init__(self, key: str, environment: str):
        self.key = key
        self.env = environment
        super().__init__(
            f'Variable with name "{key}" not found in environment "{environment}"'
        )


class ConfigService:
    def __init__(
        self,
        prod_reader: VarsReader,
        pre_reader: VarsReader,
        devel_reader: VarsReader | None = None,
    ):
        self._devel = devel_reader
        self._pre = pre_reader
        self._prod = prod_reader
        self._env = ""
        self._app = ""

    def set_environment(self, value: Literal["devel", "pre", "prod"]):
        """Set environment"""
        self._env = value

    def set_application(self, name: str):
        """Set application name to merge app var with general"""
        self._app = name

    def _list_family(self, key: str, reader: VarsReader) -> list[str]:
        vars = reader.list_vars()
        if key in vars:
            return [key]

        return [var for var in vars if var.startswith(key + ".")]

    def _get(self, key: str, reader: VarsReader) -> str | None:
        app_var = None
        if self._app and not key.startswith(self._app):
            app_var = self._get(f"{self._app}.{key}", reader)
            if app_var:
                return app_var

        return reader.read(key)

    def _get_group(self, key: str, reader: VarsReader) -> VarGroup:
        """Return value of a key, None it there is not content"""

        app_var = VarGroup([])
        if self._app and not key.startswith(self._app):
            app_var = self._get_group(f"{self._app}.{key}", reader)

        family = self._list_family(key, reader)
        if not family:
            return app_var

        names = [var[len(key) + 1 :] for var in family]
        values = [reader.read(var) for var in family]
        group = VarGroup(
            [(name, value) for name, value in zip(names, values) if value is not None]
        )
        return group.merge(app_var)

    def get_group(self, key: str) -> dict[str, dict | str]:
        """Return a group of variables as a dict"""
        if self._env == "devel":
            if not self._devel:
                raise VariableNotFound(key, "devel")

            return self._get_group(key, self._devel).as_dict()

        vars = self._get_group(key, self._prod)
        if self._env == "pre":
            vars = vars.merge(self._get_group(key, self._pre))

        return vars.as_dict()

    def get(self, key: str, default: str | None = None) -> str:
        """Return value of a key, None it there is not content"""
        if self._env == "devel":
            if not self._devel:
                raise VariableNotFound(key, "devel")

            var = self._get(key, self._devel)
            if not var:
                if not default:
                    raise VariableNotFound(key, "devel")
                return default
            return var

        if self._env == "pre":
            var = self._get(key, self._pre)
            if var:
                return var

        var = self._get(key, self._prod)
        if not var:
            if not default:
                raise VariableNotFound(key, self._env)
            return default
        return var
