# This file is part of fm-weck: executing fm-tools in containerized environments.
# https://gitlab.com/sosy-lab/software/fm-weck
#
# SPDX-FileCopyrightText: 2024 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0


import argparse
import logging
import os
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Union

try:
    from fm_tools.benchexec_helper import DataModel
except ImportError:
    from enum import Enum

    if not TYPE_CHECKING:

        class DataModel(Enum):
            """
            Enum representing the data model of the tool.
            """

            LP64 = "LP64"
            ILP32 = "ILP32"

            def __str__(self):
                return self.value


import contextlib

from fm_weck import Config
from fm_weck.cache_mgr import ask_and_clear, clear_cache
from fm_weck.config import _SEARCH_ORDER
from fm_weck.resources import fm_tools_choice_map, iter_fm_data, property_choice_map

from . import __version__
from .exceptions import NoImageError

logger = logging.getLogger(__name__)


@dataclass
class ToolQualifier:
    tool: Union[str, Path]
    version: Optional[str]

    def __init__(self, qualifier: str):
        """
        The string is of the form <tool>[:<version>]. Tool might be a path.
        """

        self.tool = qualifier.split(":")[0]

        self.version = None
        try:
            self.version = qualifier.split(":")[1]
        except IndexError:
            # No version given
            return


class ShellCompletion:
    @staticmethod
    def properties_completer(prefix, parsed_args, **kwargs):
        return list_known_properties()

    @staticmethod
    def versions_completer(prefix, parsed_args, **kwargs):
        return list_known_tools()

    @staticmethod
    def tool_completer(prefix, parsed_args, **kwargs):
        try:
            import yaml
        except ImportError:
            logger.error("PyYAML is not installed. Cannot complete tool names.")
            return []

        tools_and_versions: dict[str, list] = {}

        for tool_path in iter_fm_data():
            with open(tool_path) as stream:
                tool_data = yaml.safe_load(stream)

                try:
                    versions = [version_data["version"] for version_data in tool_data["versions"]]
                except KeyError:
                    continue
                tools_and_versions[tool_data["name"]] = versions

        tools_and_versions_list = [
            f"{tool.lower()}:{version}" for tool, versions in tools_and_versions.items() for version in versions
        ]

        selected_tools = set([tool.split(":")[0] for tool in tools_and_versions_list if tool.startswith(prefix)])
        if len(selected_tools) == 1:
            # If exactly one tool has been selected, suggest versions
            return [tool for tool in tools_and_versions_list if tool.startswith(prefix)]

        # If no tool has been selected, suggest tool names
        return selected_tools


def add_tool_arg(parser, nargs: str | None = "?"):
    parser.add_argument(
        "TOOL",
        help="The tool to obtain the container from. Can be in the form <tool>:<version>. "
        "The TOOL is either the name of a bundled tool (c.f. fm-weck --list) or "
        "the path to an fm-tools YAML file.",
        type=ToolQualifier,
        nargs=nargs,
    ).completer = ShellCompletion.tool_completer


def add_shared_args_for_run_modes(parser):
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run the tools offline. The offline mode assumes that both the tool and its info-module are located "
        "at the location specified by the config's 'cache_location' field.",
    )

    add_tool_arg(parser, nargs=None)


def add_shared_args_for_client(parser):
    parser.add_argument(
        "--host",
        action="store",
        dest="host",
        type=str,
        help=("Specifies the IP address and the port of the server."),
        required=True,
        default=None,
    )

    parser.add_argument(
        "--timelimit",
        action="store",
        dest="timelimit",
        type=str,
        help=("Specifies the maximum amount of time to wait for the server to finish a run, in seconds."),
        default=10,
    )


def parse(raw_args: list[str]) -> Tuple[Callable[[], None], Namespace]:
    parser = argparse.ArgumentParser(description="fm-weck")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--config",
        action="store",
        type=Path,
        help="Path to the configuration file.",
        default=None,
    )

    loglevels_lower = ["debug", "info", "warning", "error", "critical"]
    loglevels = loglevels_lower + [level.upper() for level in loglevels_lower]
    parser.add_argument(
        "--loglevel",
        choices=loglevels,
        metavar="LEVEL",
        action="store",
        default=None,
        help="Set the log level. Valid values are: " + ", ".join(loglevels_lower),
    )

    parser.add_argument(
        "--logfile",
        action="store",
        help="Path to the log file.",
        default=None,
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all fm-tools that can be called by name.",
        required=False,
        default=False,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Just print the command that would be executed.",
        required=False,
        default=False,
    )

    subparsers = parser.add_subparsers()

    run = subparsers.add_parser("run", aliases=["r"], help="Run a verifier inside a container.")

    # guided mode
    run.add_argument(
        "-p",
        "--property",
        "--spec",
        action="store",
        help=(
            "Property that is forwarded to the fm-tool."
            " Either a path to a property file or a property name from SV-COMP or Test-Comp."
            " Use fm-weck serve --list to view all properties that can be called by name."
        ),
        required=False,
        default=None,
    ).completer = ShellCompletion.properties_completer  # type: ignore[assignment]

    run.add_argument(
        "-d",
        "--data-model",
        action="store",
        choices=list(DataModel),
        help="The data model that shall be used.",
        required=False,
        type=lambda dm: DataModel[dm],
        default=DataModel.LP64,
    )

    run.add_argument(
        "-w",
        "--witness",
        action="store",
        help="A witness that shall be passed to the tool.",
        required=False,
        default=None,
    )

    add_shared_args_for_run_modes(run)

    run.add_argument("files", metavar="FILES", nargs="+", help="Files to pass to the tool")
    run.add_argument(
        "argument_list",
        metavar="args",
        nargs="*",
        help="Additional arguments for the fm-tool. To add them, separate them with '--' from the files.",
    )
    run.set_defaults(main=main_run)

    expert = subparsers.add_parser(
        "expert",
        aliases=["e", "m"],
        help="Manually run a verifier inside a container."
        "Arguments are passed verbatim to the tool, so expert-ise about it's command line is required.",
    )

    add_shared_args_for_run_modes(expert)

    expert.add_argument("argument_list", metavar="args", nargs="*", help="Arguments for the fm-tool")
    expert.set_defaults(main=main_manual)

    shell = subparsers.add_parser("shell", help="Start an interactive shell inside the container.")

    shell.add_argument("--entry", action="store", help="The entry point of the shell.", default="/bin/bash")

    add_tool_arg(shell)
    shell.set_defaults(main=main_shell)

    install = subparsers.add_parser("install", aliases=["i"], help="Download and unpack a TOOL for later use.")
    install.add_argument(
        "-d", "--destination", action="store", help="The destination directory.", default=None, type=Path
    )
    add_tool_arg(install, nargs="+")
    install.set_defaults(main=main_install)

    runexec = subparsers.add_parser(
        "runexec",
        help="Run runexec on a command inside a container.",
        allow_abbrev=False,
    )
    runexec.add_argument(
        "--image",
        dest="use_image",
        action="store",
        default=None,
        type=str,
        help=(
            "The image that shall be used for the container."
            " The image is treated as 'full_container_image', i.e., fm-weck will not attempt to install any packages"
            " inside of the image"
        ),
    )

    runexec.add_argument(
        "--benchexec-path",
        action="store",
        dest="benchexec_package",
        type=Path,
        help=("The path to the benchexec .whl or .egg file. If not given, fm-weck will use its own benchexec package."),
        default=None,
    )

    # Arguments passed though to the container manager (i.e., docker or podman)
    runexec.add_argument(
        "--container-long-opt",
        dest="container_long_opts",
        help="Arguments passed as long options (prepending --) directly to the container manager "
        "(e.g., docker or podman). Each usage passes additional arguments to the container manager.",
        action="append",
        nargs="+",
    )

    runexec.add_argument("argument_list", metavar="args", nargs="*", help="Arguments for runexec.")
    runexec.set_defaults(main=main_runexec)

    clear_cache = subparsers.add_parser("clear-cache", help="Clear the cache directory.")
    clear_cache.add_argument(
        "--yes",
        "-y",
        "-Y",
        action="store_true",
        help="Add automatic approval for clearing the cache.",
        required=False,
        default=False,
    )
    clear_cache.set_defaults(main=main_clear_cache)

    versions = subparsers.add_parser("versions", help="Show the versions of the chosen tool(s).")
    versions.add_argument(
        "TOOL",
        help="The tool(s) for which to print the versions.",
        type=ToolQualifier,
        nargs="+",
    ).completer = ShellCompletion.versions_completer  # type: ignore[assignment]
    versions.set_defaults(main=main_versions)

    server = subparsers.add_parser("server", aliases=["s"], help="Run fm-weck remotely on a server.")
    server.add_argument(
        "--port",
        action="store",
        dest="port",
        type=str,
        help=("Specifies the port number on which the server will listen."),
        required=True,
        default=None,
    )

    server.add_argument(
        "--listen",
        action="store",
        dest="ipaddr",
        type=str,
        help=("Specifies the IP address on which the server will listen."),
        required=True,
        default=None,
    )
    server.set_defaults(main=main_server)

    client = subparsers.add_parser("remote-run", aliases=["rr"], help="Execute tasks remotely.")
    client.add_argument(
        "-p",
        "--property",
        "--spec",
        action="store",
        help=(
            "Property that is forwarded to the fm-tool."
            " Either a path to a property file or a property name from SV-COMP or Test-Comp."
            " Use fm-weck serve --list to view all properties that can be called by name."
        ),
        required=True,
        default=None,
    )

    add_shared_args_for_client(client)
    add_tool_arg(client, nargs=None)
    client.add_argument("files", metavar="FILES", nargs="+", help="Files to pass to the tool.")
    client.set_defaults(main=main_client)

    client_expert = subparsers.add_parser(
        "remote-expert", aliases=["re"], help="Execute tasks remotely in expert mode."
    )
    add_shared_args_for_client(client_expert)
    add_tool_arg(client_expert, nargs=None)
    client_expert.add_argument("argument_list", metavar="args", nargs="*", help="Arguments for the fm-tool.")
    client_expert.set_defaults(main=main_client_expert)

    client_get_run = subparsers.add_parser(
        "get-run", aliases=["gr"], help="Get the result for a remotely executed task."
    )
    add_shared_args_for_client(client_get_run)
    client_get_run.add_argument("run_id", metavar="RUN-ID", nargs=1, help="The run ID for which to get the result.")
    client_get_run.set_defaults(main=main_client_get_run)

    client_query_files = subparsers.add_parser(
        "query-files", aliases=["qf"], help="Get the resulting files for a remotely executed task."
    )
    client_query_files.add_argument("run_id", metavar="RUN-ID", nargs=1, help="The run ID for which to get the result.")
    client_query_files.add_argument("file_names", metavar="files", nargs="*", help="Files to query for.")
    add_shared_args_for_client(client_query_files)
    client_query_files.add_argument(
        "--output-path",
        action="store",
        dest="output_path",
        type=Path,
        help=(
            "Specifies the location where the incoming files from the server will be stored, "
            "relative to the current working directory."
        ),
        default=Path.cwd(),
    )
    client_query_files.set_defaults(main=main_client_query_files)

    smoke_test = subparsers.add_parser("smoke-test", help="Run a smoke test on the tool.")
    smoke_test.add_argument(
        "TOOL",
        help="The tool for which to run the smoke test.",
        type=ToolQualifier,
    ).completer = ShellCompletion.versions_completer  # type: ignore[assignment]

    smoke_test.add_argument(
        "--gitlab-ci-mode",
        action="store_true",
        help="Run in GitLab CI mode: directly install required packages with apt instead of building/pulling images.",
        required=False,
        default=False,
    )
    smoke_test.add_argument(
        "--competition-year",
        action="store",
        type=int,
        help="Automatically select the tool version used in the specified competition year (e.g., 2025). "
        "Searches for SV-COMP or Test-Comp participation in that year.",
        required=False,
        default=None,
    )
    smoke_test.set_defaults(main=main_smoke_test)

    with contextlib.suppress(ImportError):
        import argcomplete

        argcomplete.autocomplete(parser)

    def help_callback():
        parser.print_help()

    result, left_over = parser.parse_known_args(raw_args)

    if not left_over:
        # Parsing went fine
        return help_callback, result

    # Find the first offending argument and insert "--" before it
    # We do this to allow the user to pass arguments to the fm-tool without
    # having to specify the pseudo argument "--"
    idx = raw_args.index(left_over[0])
    raw_args.insert(idx, "--")

    return help_callback, parser.parse_args(raw_args)


def list_known_tools():
    return fm_tools_choice_map().keys()


def list_known_properties():
    return property_choice_map().keys()


def resolve_tool(tool: ToolQualifier) -> Path:
    tool_name = tool.tool
    if (as_path := Path(tool_name)).exists() and as_path.is_file():
        return as_path

    return fm_tools_choice_map()[str(tool_name)]


def resolve_property(prop_name: str) -> Path:
    if (as_path := Path(prop_name)).exists() and as_path.is_file():
        return as_path

    return property_choice_map()[prop_name]


def resolve_property_for_server(prop_name: str) -> Union[Path, str]:
    if (as_path := Path(prop_name)).exists() and as_path.is_file():
        return as_path

    return prop_name


def get_version_for_competition_year(tool_path: Path, year: int) -> Optional[str]:
    """
    Find the tool version used in a competition for the given year.
    Searches for SV-COMP or Test-Comp participation entries.

    Args:
        tool_path: Path to the tool's YAML file
        year: Competition year (e.g., 2025)

    Returns:
        Version string if found, None otherwise
    """
    import yaml

    if not tool_path.exists() or not tool_path.is_file():
        return None

    with tool_path.open("r") as f:
        data = yaml.safe_load(f)

    competition_participations = data.get("competition_participations", [])

    # Search for competition entries matching the year
    for participation in competition_participations:
        competition = participation.get("competition", "")
        # Match "SV-COMP 2025", "Test-Comp 2025", etc.
        if f"{year}" in competition and ("SV-COMP" in competition or "Test-Comp" in competition):
            version = participation.get("tool_version")
            if version:
                logger.info("Found version '%s' for %s in %s", version, tool_path.stem, competition)
                return version

    return None


def set_log_options(loglevel: Optional[str], logfile: Optional[str], config: dict[str, Any]):
    level = "WARNING"
    level = loglevel.upper() if loglevel else config.get("logging", {}).get("level", level)
    if logfile:
        logging.basicConfig(level=level, filename=logfile)
    else:
        logging.basicConfig(level=level)
    logging.getLogger("httpcore").setLevel("WARNING")


def main_run(args: argparse.Namespace):
    from .serve import run_guided

    if not args.TOOL:
        logger.error("No fm-tool given. Aborting...")
        return 1
    try:
        fm_data = resolve_tool(args.TOOL)
    except KeyError:
        logger.error("Unknown tool %s", args.TOOL)
        return 1

    try:
        property_path = resolve_property(args.property) if args.property else None
    except KeyError:
        logger.error("Unknown property %s", args.property)
        return 1

    result = run_guided(
        fm_tool=fm_data,
        version=args.TOOL.version,
        configuration=Config(),
        prop=property_path,
        witness=Path(args.witness) if args.witness else None,
        program_files=args.files,
        additional_args=args.argument_list,
        data_model=args.data_model,
        offline_mode=args.offline,
    )

    return result.exit_code


def main_runexec(args: argparse.Namespace):
    from .runexec_mode import run_runexec

    result = run_runexec(
        benchexec_package=args.benchexec_package,
        use_image=args.use_image,
        configuration=Config(),
        extra_container_args=args.container_long_opts or [],
        command=args.argument_list,
    )

    if result is None:
        return 1  # Indicate failure due to runexec setup issues

    return result.exit_code


def main_manual(args: argparse.Namespace):
    from .serve import run_manual

    if not args.TOOL:
        logger.error("No fm-tool given. Aborting...")
        return 1
    try:
        fm_data = resolve_tool(args.TOOL)
    except KeyError:
        logger.error("Unknown tool %s", args.TOOL)
        return 1

    result = run_manual(
        fm_tool=fm_data,
        version=args.TOOL.version,
        configuration=Config(),
        command=args.argument_list,
        offline_mode=args.offline,
    )

    return result.exit_code


def main_install(args: argparse.Namespace):
    from .serve import install_fm_tool

    for tool in args.TOOL:
        try:
            fm_data = resolve_tool(tool)
        except KeyError:
            logger.error("Unknown tool %s. Skipping installation...", tool)
            continue

        install_fm_tool(fm_tool=fm_data, version=tool.version, configuration=Config(), install_path=args.destination)

    return 0


def main_shell(args: argparse.Namespace):
    from .engine import Engine

    if not args.TOOL:
        engine = Engine.from_config(Config())
    else:
        try:
            fm_data = resolve_tool(args.TOOL)
        except KeyError:
            logger.error("Unknown tool %s", args.fm_data)
            return 1
        engine = Engine.from_config(fm_data, args.TOOL.version, Config())
    engine.interactive = True
    result = engine.run(args.entry)
    return result.exit_code


def main_clear_cache(args: argparse.Namespace):
    if args.yes:
        clear_cache(Config().get("defaults", {}).get("cache_location"))  # type: ignore
    else:
        ask_and_clear(Config().get("defaults", {}).get("cache_location"))  # type: ignore
    return


def main_versions(args: argparse.Namespace):
    from .version_listing import VersionListing

    tools = args.TOOL
    tool_paths = []
    if not args.TOOL:
        logger.error("No fm-tool given. Aborting...")
        return 1

    for tool in tools:
        try:
            tool_paths.append(resolve_tool(tool))
        except KeyError:
            logger.error("Unknown tool %s", tool)
            return 1

    VersionListing(tool_paths).print_versions()


def main_server(args: argparse.Namespace):
    from .grpc_service import serve

    serve(ipaddr=args.ipaddr, port=args.port)


def main_client(args: argparse.Namespace):
    from .grpc_service import client_run

    tool = resolve_tool(args.TOOL)
    property = resolve_property(args.property)
    timelimit, _ = check_client_options(args.timelimit)

    client_run((tool, args.TOOL.version), args.host, property, args.files, timelimit)


def main_client_expert(args: argparse.Namespace):
    from .grpc_service import client_expert_run

    tool = resolve_tool(args.TOOL)
    command = args.argument_list
    client_expert_run((tool, args.TOOL.version), args.host, command, args.timelimit)


def main_client_get_run(args: argparse.Namespace):
    from .grpc_service import client_get_run

    timelimit, _ = check_client_options(args.timelimit)
    client_get_run(args.host, args.run_id[0], timelimit)


def main_client_query_files(args: argparse.Namespace):
    from .grpc_service import query_files

    timelimit, _ = check_client_options(args.timelimit)
    file_names = args.file_names

    query_files(args.host, args.run_id[0], file_names, timelimit, args.output_path)


def check_client_options(timelimit_arg, output_path=None):
    try:
        timelimit = int(timelimit_arg)
    except ValueError:
        logger.error("Invalid timelimit value: %s. It must be an integer.", timelimit_arg)
        exit(1)

    if output_path:
        output_path = Path.cwd() / Path(output_path)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed to create output path %s: %s", output_path, e)
                exit(1)

    return timelimit, output_path


def _do_smoke_test_mode(fm_data, shelve_space, tool, gitlab_ci_mode) -> int:
    from .smoke_test_mode import (
        run_smoke_test,
        run_smoke_test_gitlab_ci,
    )

    # GitLab CI mode installs packages directly and runs the script on the host
    if gitlab_ci_mode:
        from subprocess import CalledProcessError

        try:
            run_smoke_test_gitlab_ci(fm_data, shelve_space)
            return 0
        except CalledProcessError as e:
            logger.error(
                "Smoke test script failed in GitLab CI mode (exit code %d).\n- Tool: %s\n- Script directory: %s\n",
                e.returncode,
                tool.stem,
                shelve_space,
            )
            return e.returncode

    # Containerized mode: run script inside the configured image
    result = run_smoke_test(fm_data, shelve_space, Config())
    if result.exit_code != 0:
        # Print a concise but informative error for CI logs
        output_lines = result.raw_output.splitlines()
        tail = "\n".join(output_lines[-50:]) if output_lines else "<no output captured>"
        logger.error(
            "Smoke test failed (exit code %d).\n"
            "- Tool: %s\n"
            "- Tool cache dir (host): %s\n"
            "- Script name: smoketest.sh\n"
            "Last 50 lines of output:\n%s",
            result.exit_code,
            tool.stem,
            shelve_space,
            tail,
        )
        return result.exit_code

    return 0


def main_smoke_test(args: argparse.Namespace):
    from fm_tools.exceptions import DownloadUnsuccessfulException, UnsupportedDOIException

    from .serve import setup_fm_tool
    from .smoke_test_mode import (
        NoSmokeTestFileError,
        SmokeTestError,
        SmokeTestFileIsEmptyError,
        SmokeTestFileIsNotExecutableError,
    )

    try:
        tool = resolve_tool(args.TOOL)
    except KeyError:
        logger.error("Unknown tool: %s", args.TOOL.tool)
        return 1

    # Handle --competition-year flag
    version = args.TOOL.version
    if args.competition_year:
        if version:
            logger.warning(
                "Both explicit version '%s' and --competition-year %d specified. "
                "Using competition year to determine version.",
                version,
                args.competition_year,
            )
        competition_version = get_version_for_competition_year(tool, args.competition_year)
        if competition_version:
            logger.info("Using version '%s' for competition year %d", competition_version, args.competition_year)
            version = competition_version
        else:
            logger.error("No competition participation found for year %d in tool %s", args.competition_year, tool.stem)
            return 1

    try:
        fm_data, shelve_space = setup_fm_tool(
            fm_tool=tool,
            version=version,
            configuration=Config(),
        )
    except (DownloadUnsuccessfulException, UnsupportedDOIException) as e:
        if "code: 504" in str(e).lower():
            print(
                "Failed to download the tool due to a timeout (504 Gateway Timeout). "
                "This issue is likely caused by Zenodo. Retry by rerunning the smoke test.",
            )
        else:
            print(f"There was an error while downloading and unpacking the tool:\n{e}")

    try:
        return _do_smoke_test_mode(fm_data, shelve_space, tool, args.gitlab_ci_mode)
    except NoSmokeTestFileError as e:
        print(
            f"{e}\n"
            "Expected a smoke test script named 'smoketest.sh' in the tool directory.\n"
            "Action: Add a minimal script 'smoketest.sh' to the root of the tool directory that exercises the tool.\n"
            "The top level contents of the tool directory were:\n"
            f"{os.linesep.join([str(p.name) for p in shelve_space.iterdir()])}",
        )
        return 1
    except SmokeTestFileIsEmptyError as e:
        print(
            f"{e}\nAction: Populate the smoke test script with at least one command that validates basic startup.",
        )
        return 1
    except SmokeTestFileIsNotExecutableError as e:
        print(
            f"{e}\nAction: Make the smoke test script executable. On linux, you can do this by running:\n"
            f"  chmod +x {e.smoke_test_file}",
        )
        return 1
    except ValueError as e:
        # e.g., invalid shelve space path, or other validation errors
        print(f"Smoke test setup failed: {e}")
        return 1
    except SmokeTestError as e:
        # Fallback for any other smoke-test specific errors
        print(f"Error starting the smoke test: {e}")
        return 1


def log_no_image_error(tool, config):
    order = []
    for path in _SEARCH_ORDER:
        if path.is_relative_to(Path.cwd()):
            order.append(str(path.relative_to(Path.cwd())))
        else:
            order.append(str(path))

    text = ""
    if tool:
        text = f"{os.linesep}No image specified in the fm-tool yml file for {tool.tool}."
    else:
        text = f"{os.linesep}No image specified."
    if config is None:
        text += f"""
There is currently no configuration file found in the search path.
The search order was 
{os.linesep.join(order)}
Please specify an image in the fm-tool yml file or add a configuration.

To add a configuration you can do the following (on POSIX Terminals):

printf '[defaults]\\nimage = "<your_image>"' > .fm-weck

Replace <your_image> with the image you want to use.
        """
        logger.error(text)
        return

    text = """
No image specified in the fm-tool yml file for %s nor in the configuration file %s.
Please specify an image in the fm-tool yml file or in the configuration file.
To specify an image add

[defaults]
image = "your_image"

to your .fm-weck file.
    """

    logger.error(text, tool, config)


def cli(raw_args: list[str]):
    help_callback, args = parse(raw_args)
    configuration = Config().load(args.config)

    set_log_options(args.loglevel, args.logfile, configuration)
    if args.dry_run:
        Config().set_dry_run(True)

    if args.list:
        print("List of fm-tools callable by name:")
        for tool in sorted(list_known_tools()):
            print(f"  - {tool}")
        print("\nList of properties callable by name:")
        for prop in sorted(list_known_properties()):
            print(f"  - {prop}")
        return

    if not hasattr(args, "main"):
        return help_callback()

    try:
        return args.main(args)
    except NoImageError:
        log_no_image_error(args.TOOL, Config()._config_source)
        return 1
