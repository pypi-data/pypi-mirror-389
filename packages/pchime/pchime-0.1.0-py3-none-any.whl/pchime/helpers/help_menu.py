from importlib import metadata
# from typing import Optional
import importlib
from rich.console import Console
console = Console()

def get_app_version():
    package_name = "pchime"
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        try:
            pkg = importlib.import_module(package_name)
            return getattr(pkg, "__version__", None)
        except Exception:
            return None
        

def return_package_name(args):
    pkg_version = get_app_version()
    console.print(f"[green]Pchime[/green] : version : {pkg_version}")
    console.print(f"""[green]Pipechime[/green] [blue](pchime)[/blue] is a CLI package used to perform federated based machine learning centric data analytics with the help of flwr, pandas and python based ml frameworks.

[yellow]**Developer Notes**[/yellow]
Pipechime is an ongoing project and is currently staged precautiously for experimentation purpose only. Model performance can only be determined only while comparing with centralised learning.

[yellow]**Roadmap**[/yellow]
Pchime is focused on creating easy to use CLI that could further support to GUI centric application integrations. The below figure represents the current state that only utilises server-client architecture with example banking specific scenario""")
