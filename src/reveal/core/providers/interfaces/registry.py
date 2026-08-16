from abc import ABC, abstractmethod
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Generic, TypeVar


PluginT = TypeVar("PluginT")


class RegistryInterface(ABC, Generic[PluginT]):
    """Base registry for automatically discovered plugins.

    Plugins are discovered from modules following a naming convention.
    Each module must expose an ``export`` variable containing plugin
    classes. Plugin classes are instantiated once during registry
    initialization.

    Example plugin module:

        export = [
            JsonFileReader,
        ]
    """

    def __init__(
        self,
        package: str,
        module_name: str,
    ) -> None:
        self._plugins: list[PluginT] = []

        self._discover(
            package=package,
            module_name=module_name,
        )

    def register(
        self,
        plugin: PluginT,
    ) -> None:
        """Register an already instantiated plugin."""
        self._plugins.append(plugin)

    def _discover(
        self,
        package: str,
        module_name: str,
    ) -> None:
        """Discover and instantiate plugins."""

        for module in self._find_modules(
            package,
            module_name,
        ):
            for plugin_class in getattr(
                module,
                "export",
                [],
            ):
                self.register(plugin_class())

    @staticmethod
    def _find_modules(
        package: str,
        module_name: str,
    ) -> list[ModuleType]:
        """Find plugin modules inside a package."""

        package_module = import_module(package)

        if package_module.__file__ is None:
            raise ValueError(
                f"Cannot determine package path: {package}"
            )

        package_path = Path(
            package_module.__file__
        ).parent

        modules: list[ModuleType] = []

        for plugin_dir in package_path.iterdir():
            if not plugin_dir.is_dir():
                continue

            module_path = (
                plugin_dir / f"{module_name}.py"
            )

            if not module_path.is_file():
                continue

            modules.append(
                import_module(
                    f"{package}."
                    f"{plugin_dir.name}."
                    f"{module_name}"
                )
            )

        return modules

    @property
    def plugins(self) -> tuple[PluginT, ...]:
        """Return all registered plugins."""
        return tuple(self._plugins)

    @abstractmethod
    def resolve(self, value) -> PluginT:
        """Resolve a plugin capable of handling a value."""
        ...
