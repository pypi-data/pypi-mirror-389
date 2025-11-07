from importlib.metadata import version

def show_version():
    version_aidge_export_cpp = version("aidge_export_cpp")
    print(f"Aidge Export CPP: {version_aidge_export_cpp}")

def get_project_version()->str:
    return version("aidge_export_cpp")
