from dbnl import config


def generate_app_url(path: str) -> str:
    app_url = config.app_url().rstrip("/")
    path = path.lstrip("/")
    return f"{app_url}/{path}"
