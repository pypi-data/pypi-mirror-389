from pathlib import Path
from typing import Union, Optional


class Module:
    def __init__(
        self,
        path: Union[str, Path],
        template_path: Optional[str] = None,
        /,
        **fields
    ):
        self.path = Path(path).resolve()
        self.template_path = template_path
        self.fields = fields


class Package:
    def __init__(
        self,
        path: Union[str, Path],
        template_path: Optional[str] = None,
        /,
        **fields
    ):
        self.path = Path(path).resolve()
        self.modules: list[Module] = [
            Module(
                self.path / "__init__.py",
                template_path,
                **fields
            )
        ]
        self.packages: list["Package"] = []

    def add_module(
        self,
        name: str,
        template_path: Optional[str] = None,
        /,
        **fields
    ) -> Module:
        path = self.path / name

        if path in {i.path for i in self.modules}:
            raise ValueError(f"Module {str(path)!r} has already been added!")

        module = Module(
            path,
            template_path,
            **fields
        )
        self.modules.append(module)

        return module

    def add_package(
        self,
        name: str,
        template_path: Optional[str] = None,
        /,
        **fields
    ) -> "Package":
        path = self.path / name

        if path in {i.path for i in self.packages}:
            raise ValueError(f"Package {str(path)!r} has already been added!")

        package = Package(
            path,
            template_path,
            **fields
        )
        self.packages.append(package)

        return package
