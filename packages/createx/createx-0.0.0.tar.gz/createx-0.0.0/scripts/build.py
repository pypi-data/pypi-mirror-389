import json
from pathlib import Path

import click
from ape import project


@click.command()
def cli():
    Path("src/createx/manifest.json").write_text(
        project.dependencies["createx"]["main"].manifest.model_dump_json()
    )
    print("Wrote 'src/createx/manifest.json'")

    deployments = json.loads(
        (
            project.dependencies["createx"]["main"].path
            / "deployments"
            / "deployments.json"
        ).read_text()
    )
    print(f"Found {len(deployments)} deployments")
    Path("src/createx/deployments.json").write_text(
        json.dumps([deployment["chainId"] for deployment in deployments])
    )
    print("Wrote 'src/createx/deployments.json'")
