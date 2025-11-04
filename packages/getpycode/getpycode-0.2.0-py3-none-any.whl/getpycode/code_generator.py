from typing import Optional

from jinja2 import Environment, BaseLoader, StrictUndefined

from getpycode.types import Package, Module
from getpycode.comment import AbstractComment


class CodeGenerator:
    def __init__(
        self,
        loader: BaseLoader,
        *,
        overwrite: bool = True,
        comment: Optional[AbstractComment] = None
    ):
        self.environment = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            undefined=StrictUndefined,
            loader=loader,
            auto_reload=False,
            extensions=["jinja2.ext.do"]
        )
        self._overwrite = overwrite
        self._comment = comment

    def create_module(self, module: Module) -> None:
        if module.path.exists() and not self._overwrite:
            raise FileExistsError(f"Module {str(module.path)!r} already exists!")

        if module.template_path:
            template = self.environment.get_template(module.template_path)
            code = template.render(**module.fields)
        else:
            code = ""

        if self._comment is not None:
            comment = []

            for i in self._comment.get(module):
                if not i.startswith("#"):
                    i = f"# {i}"

                comment.append(i)

            comment = "\n".join(comment)

            if code:
                code = f"{comment}\n\n{code}"
            else:
                code = f"{comment}\n"

        with module.path.open("w", encoding="utf-8") as file:
            file.write(code)

    def create_package(self, package: Package) -> None:
        package.path.mkdir(exist_ok=True)

        for i in package.modules:
            self.create_module(i)

        for i in package.packages:
            self.create_package(i)
