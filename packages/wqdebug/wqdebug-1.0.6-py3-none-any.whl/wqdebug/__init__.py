try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution("wqdebug").version
except Exception:
    __version__ = "1.0.0"
