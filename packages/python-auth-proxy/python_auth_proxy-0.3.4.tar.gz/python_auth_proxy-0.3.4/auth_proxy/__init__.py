from importlib.metadata import version, PackageNotFoundError

try:
    version = version("python-auth-proxy")
except PackageNotFoundError:
    version = "0.0.0.dev0"