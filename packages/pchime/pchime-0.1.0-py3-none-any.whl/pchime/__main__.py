from rich.console import Console
from pchime_cli import create_parser
import time
from pchime.local_data_instances.fresh_installation_conditions.create_storage_blob_directory import create_storage_blob_folder
from logging import INFO


# import toml
# configurations imported from toml files
# config = toml.load("config.toml")
# app_title, app_desc, app_version = config["details"]["title"], config["details"]["description"],config["details"]["version"]
# end of configurations

console = Console() 

def main():
    # console.print(f"[bold cyan]{app_title}[/bold cyan]")
    # console.print(f"[green] Version [/green] {app_version}")
    # console.print(f"[yellow] Description [/yellow] {app_desc}")
    storage_path = create_storage_blob_folder()
    # time.sleep(2)
    if storage_path is not None:
        console.print(f"✅ [green]Directory re-initialized for blob storage [/green]")
        console.print(f"📂 [blue][INFO] :: Current storage blob is located at :[/blue] {storage_path}")
        console.print(f"⚠️  [yellow][CAUTION][/yellow] :: Storage paths are re-initialized and the logs related to it are only enforced to development branches. Production branches do not log or re-initialise storage blobs everytime when pchime is executed or called.")
        
    parser = create_parser()
    args = parser.parse_args()
    args.func(args)



if __name__ == "__main__":
    main()

