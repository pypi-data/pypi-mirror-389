import filecmp
import os
import re
import shlex
from concurrent.futures import Future, as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import List

from pyhelper_utils.shell import run_command

OCP_RESOURCES_STR: str = "ocp_resources"


def delete_unchanged_files(updated_files: List[str]) -> List[str]:
    for file_ in updated_files:
        updated_file: str = file_.replace(".py", "_TEMP.py")
        if os.path.exists(updated_file) and filecmp.cmp(file_, updated_file):
            print(f"{file_} does not have any changes, deleting {updated_file} file.")
            Path.unlink(Path(updated_file))
            updated_files.remove(file_)

    return updated_files


def main() -> None:
    futures: List[Future] = []
    updated_files: List[str] = []
    exceptions: List[BaseException] = []

    with ThreadPoolExecutor() as executor:
        for obj in os.listdir(OCP_RESOURCES_STR):
            filepath = os.path.join(OCP_RESOURCES_STR, obj)
            if (
                os.path.isfile(filepath)
                and obj.endswith(".py")
                and obj not in ("__init__.py", "resource.py", "utils.py")
            ):
                with open(filepath) as fd:
                    data = fd.read()

                if data.startswith("# Generated using"):
                    kind = re.search(r"class\s+(.*?)\((Namespaced)?Resource", data)
                    if kind:
                        updated_files.append(filepath)
                        futures.append(
                            executor.submit(
                                run_command,
                                **{
                                    "command": shlex.split(
                                        f"uv run python class_generator/class_generator.py --kind {kind.group(1)}"
                                    ),
                                    "log_errors": False,
                                },
                            )
                        )

        if futures:
            for result in as_completed(futures):
                if _exception := result.exception():
                    exceptions.append(_exception)

        updated_files_to_review = "\n".join(delete_unchanged_files(updated_files=updated_files))
        print(
            f"The following files were updated:\n{updated_files_to_review}.\n"
            "Please review the changes before commiting."
        )

        if exceptions:
            exceptions_str = ", ".join(ex.args[1][-1] for ex in exceptions)
            print(f"Failed to update resources:\n{exceptions_str}")


if __name__ == "__main__":
    main()
