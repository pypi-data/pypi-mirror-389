import importlib.metadata
import importlib.resources


def read_version() -> str:
    try:
        return importlib.metadata.version(__package__ or "cnworkdays")
    except importlib.metadata.PackageNotFoundError:
        return (
            importlib.resources.files("cn_workdays")
            .joinpath("VERSION")
            .read_text()
            .strip()
        )


__version__ = read_version()
