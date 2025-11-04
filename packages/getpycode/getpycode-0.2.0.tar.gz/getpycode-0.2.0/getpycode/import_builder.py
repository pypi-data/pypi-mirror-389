import sysconfig
from pathlib import Path
import importlib.util
from enum import IntEnum
from typing import Optional


stdlib_dir = Path(sysconfig.get_paths()["stdlib"])


class ImportType(IntEnum):
    STANDARD = 1
    THIRD_PARTY = 2
    LOCAL = 3
    TYPE_CHECKING = 4


class ImportBuilder:
    def __init__(self, package: str, *, exclude: Optional[tuple[str, str]] = None):
        self.package = package
        self._exclude = exclude
        self._imports = {i: {} for i in ImportType}

    def add(self, module_path: str, entity: str, *, for_type_checking: bool = False) -> None:
        if (module_path, entity) == self._exclude:
            return

        type_ = self._get_import_type(module_path)

        if for_type_checking:
            if type_ is not ImportType.LOCAL:
                raise ValueError(f"Module path {module_path!r} is not local!")

            type_ = ImportType.TYPE_CHECKING
            self.add("typing", "TYPE_CHECKING")

            if module_path in self._imports[ImportType.LOCAL]:
                try:
                    self._imports[ImportType.LOCAL][module_path].remove(entity)
                except ValueError:
                    pass
                else:
                    if not self._imports[ImportType.LOCAL][module_path]:
                        del self._imports[ImportType.LOCAL][module_path]
        elif (
            (type_ is ImportType.LOCAL)
            and (entity in self._imports[ImportType.TYPE_CHECKING].get(module_path, []))
        ):
            return

        if module_path not in self._imports[type_]:
            self._imports[type_][module_path] = []
        elif entity in self._imports[type_][module_path]:
            return

        self._imports[type_][module_path].append(entity)

    def check(self, module_path: str, entity: str) -> bool:
        for i in self._imports.values():
            if module_path in i and entity in i[module_path]:
                return True

        return False

    def get(self) -> str:
        blocks = [
            "\n".join(
                self._get_imports(i)
            )
            for i in (
                ImportType.STANDARD,
                ImportType.THIRD_PARTY,
                ImportType.LOCAL
            )
        ]
        imports = "\n\n".join(i for i in blocks if i)
        type_checking_imports = self._get_imports(ImportType.TYPE_CHECKING)

        if type_checking_imports:
            imports += "\nif TYPE_CHECKING:\n" + "\n".join(f"    {i}" for i in type_checking_imports)

        return imports

    def _get_imports(self, type_: ImportType) -> list[str]:
        imports = []

        for module_path, entities in self._imports[type_].items():
            imports.append(f"from {module_path} import {', '.join(entities)}")

        return sorted(imports)

    def _get_import_type(self, module_path: str) -> ImportType:
        import_name = _get_module_path_package(module_path)

        if import_name in (".", self.package):
            return ImportType.LOCAL
        elif _check_standard_import_name(import_name):
            return ImportType.STANDARD

        return ImportType.THIRD_PARTY


def _get_module_path_package(path: str) -> str:
    if path.startswith("."):
        return "."

    return path.split(".", 1)[0]


def _check_standard_import_name(name: str) -> bool:
    spec = importlib.util.find_spec(name)

    if spec is None:
        return False

    if spec.origin in ("built-in", "frozen"):
        return True

    return stdlib_dir in Path(spec.origin).parents
