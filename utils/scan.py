import os
import re
import platform
import subprocess
import json


def normalize_path(input_path: str, prefix: str) -> str:
    norm_path = os.path.normpath(input_path)
    rel_path = os.path.relpath(norm_path, start=prefix)
    if rel_path.startswith('.' + os.sep):
        rel_path = rel_path[len('.' + os.sep):]
    return rel_path


class SCToolkit:
    """"""
    def __init__(self, scancode_path: str, tmp_path: str = "tmp/", number: int = 11) -> None:
        self.scancode_path = os.path.normpath(scancode_path)
        self.tmp_path = os.path.normpath(tmp_path)
        self.number = number
        self._check_toolkit()

    def scan_license(self, project_path: str, callback: callable = None, prefix: str = None) -> str:
        store_path = normalize_path(project_path, prefix)
        os.makedirs(os.path.dirname(f"{self.tmp_path}/{store_path}.json"), exist_ok=True)
        result = subprocess.run(
            f'{self.scaner_path} -n {self.number} --ignore=".*" --license --json {self.tmp_path}/{store_path}.json {project_path}',
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return f"{self.tmp_path}/{store_path}.json", result.stdout, result.stderr

    def _check_toolkit(self):
        if platform.system().lower() == "windows":
            check_file = "scancode.bat"
        elif platform.system().lower() == "linux" or platform.system().lower() == "darwin":
            check_file = "scancode"
        else:
            raise NotImplementedError(f"{platform.system().lower()} platform not implemented.")

        self.scaner_path = os.path.join(self.scancode_path, check_file)
        if not os.path.exists(self.scaner_path):
            raise FileNotFoundError("check your scancode path.")

        os.makedirs(self.tmp_path, exist_ok=True)


if __name__ == "__main__":

    import json
    from rich.progress import Progress
    from rich.console import Console

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("prefix", help="prefix")
    
    parser.add_argument("--n", type=int, default=11, help="thread number")
    args = parser.parse_args()

    prefix = args.prefix
    number = args.n
    result_path = os.path.normpath(f"./{prefix.strip(os.sep).split(os.sep)[-1]}-license")
    gn_out_path = os.path.normpath(f"{prefix}out/rk3568/out.json")
    sct = SCToolkit("./scancode-toolkit", result_path, number)

    nodes = json.load(open(gn_out_path, "r"))["targets"].keys()

    tgts = set()
    back_tgts = set()
    for node in nodes:

        node = "/".join(re.sub(r"//|:.+$", "", node).split(os.sep)[:3])
        node = os.path.join(prefix, node)

        if any(node.startswith(tgt) for tgt in tgts):
            continue

        if os.path.isfile(node):
            if os.path.exists(os.path.dirname(node)):
                tgts.add(os.path.dirname(node))
            continue

        if not os.path.exists(node):
            continue

        tgts.add(node)

    console = Console()
    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Scanning licenses...", total=len(tgts))
        for idx, tgt in enumerate(tgts):
            console.print(f"current target path: {tgt}, remain file number: {len(tgts) - idx}")
            new_tgt = normalize_path(tgt, prefix=prefix)

            if os.path.exists(f"{sct.tmp_path}{os.path.sep}{new_tgt}.json"):
                console.print(f"{sct.tmp_path}{os.path.sep}{new_tgt}.json already exists, next ..")
                progress.update(task, advance=1)
                continue

            try:
                result_path, stdout, stderr = sct.scan_license(tgt, callback=None, prefix=prefix)
                console.print(f"scan result path: {result_path}")
                console.print(stdout)
                if stderr:
                    console.print(f"stderr: {stderr}")

            except Exception as e:
                console.print(f"error: {e}")

            finally:
                progress.update(task, advance=1)
