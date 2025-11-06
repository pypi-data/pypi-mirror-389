"""A Vulnerability Scanner that combines results from all configured scanners.

--------------------------------------------------------------------------------
SPDX-FileCopyrightText: Copyright © 2022 Lockheed Martin <open.source@lmco.com>
SPDX-FileName: hopprcop/combined/cli.py
SPDX-FileType: SOURCE
SPDX-License-Identifier: MIT
--------------------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
--------------------------------------------------------------------------------
"""

from __future__ import annotations

from pathlib import Path
from platform import python_version
from typing import TYPE_CHECKING

import rich
import typer

from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Typer

import hopprcop

from hopprcop.combined.combined_scanner import CombinedScanner, ScannerOptions
from hopprcop.enhancements.epss_enhancer import EpssEnhancer
from hopprcop.gemnasium.gemnasium_scanner import GemnasiumScanner
from hopprcop.grype.grype_scanner import GrypeScanner
from hopprcop.ossindex.oss_index_scanner import OSSIndexScanner
from hopprcop.reporting import Reporting
from hopprcop.reporting.models import CycloneDxRenderOptions, ReportFormat
from hopprcop.trivy.trivy_scanner import TrivyScanner
from hopprcop.utils import parse_sbom


if TYPE_CHECKING:
    from hopprcop.vulnerability_scanner import VulnerabilitySuper


app = Typer(
    name="hoppr-cop",
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Policing Your SBOM Vulnerabilities",
    no_args_is_help=False,
    pretty_exceptions_show_locals=False,
    rich_markup_mode="markdown",
)


def _output_dir(output_dir: Path | None) -> Path:
    """Use `Path.cwd()` as output directory if not provided."""
    return output_dir or Path.cwd()


def _version(version: bool) -> None:
    if version:
        rich.print(f"[green]HopprCop Version       [/] : {hopprcop.__version__}")
        rich.print(f"[green]Python Version         [/] : {python_version()}")
        raise typer.Exit(code=0)


def determine_scanners(
    scanners: list[ScannerOptions] | None, is_dbs: bool, is_offline: bool, os_distro_val: str | None
) -> list[VulnerabilitySuper]:
    """Determines the scanners based on the provided parameters."""
    if not scanners:
        scanners = [ScannerOptions.GRYPE, ScannerOptions.TRIVY, ScannerOptions.OSS, ScannerOptions.GEM]
        rich.print("Using default scanner values since none were specified.")

    scanner_list: list[VulnerabilitySuper] = []
    for scan in scanners:
        if scan == ScannerOptions.GRYPE:
            scanner_list.append(GrypeScanner(offline_mode=is_offline, grype_os_distro=os_distro_val))
        elif scan == ScannerOptions.TRIVY:
            scanner_list.append(TrivyScanner(offline_mode=is_offline, trivy_os_distro=os_distro_val))
        elif scan in [ScannerOptions.GEM, ScannerOptions.GEMNASIUM]:
            scanner_list.append(GemnasiumScanner(offline_mode=is_offline))
        elif scan in [ScannerOptions.OSS, ScannerOptions.OSSINDEX]:
            if is_dbs:
                rich.print("[yellow]oss scanner was not activated as it's not used for --download-dbs.[/]")
            else:
                scanner_list.append(OSSIndexScanner(offline_mode=is_offline))
        else:
            raise typer.BadParameter(
                f"A bad scanner parameter was added. {scan} is not a valid scanner option for this scenario. Use 'hopper-cop -h' to determine the valid options."
            )
    return scanner_list


def _formats(formats: list[ReportFormat] | None) -> list[str]:
    """Use `[ReportFormat.TABLE]` as report format if not provided."""
    return [format_.value for format_ in formats or [ReportFormat.TABLE]]


def dbs_path_function(scanner: list[ScannerOptions]) -> None:
    """This function contains the code that's run when performing dbs downloads."""
    combined = CombinedScanner()

    scanner_list = determine_scanners(scanner, True, False, "")

    combined.set_scanners(scanner_list)

    rich.print("Downloading databases now....")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching vulnerability databases...", total=None)
        combined.get_vulnerability_dbs()
        rich.print("Successfully downloaded vulnerability databases")
        typer.Exit(code=0)


def bom_path_function(
    scanner: list[ScannerOptions],
    bom: str,
    offline: bool,
    os_distro: str,
    base_report_name: str,
    output_dir: Path,
    epss: bool,
    keep_serial_numbers: bool,
    increment_version: bool,
    formats: list[ReportFormat],
    assessment: str,
) -> None:
    """This function contains the code that's run when performing the BOM vulnerability checks based on a provided BOM and other values."""
    bom_path = Path(bom)
    if not bom_path.exists():
        rich.print(f"[red] {bom} does not exist")
        raise typer.Exit(code=1)

    if base_report_name is None:
        base_report_name = bom_path.stem

    reporting = Reporting(output_dir, base_report_name)
    combined = CombinedScanner()

    if assessment:
        combined.set_assessment_path(assessment)

    scanner_list = determine_scanners(scanner, False, offline, os_distro)

    combined.set_scanners(scanner_list)

    combined.set_enhancers([EpssEnhancer(offline_mode=offline, enabled=epss)])

    parsed_bom = parse_sbom(bom_path)

    render_options = CycloneDxRenderOptions(
        keep_serial_numbers=keep_serial_numbers, increment_version=increment_version
    )

    rich.print("Grabbing vulnerabilities now....")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Fetching vulnerabilities...", total=None)
        results = combined.get_vulnerabilities_for_sbom(parsed_bom)

    reporting.generate_vulnerability_reports(formats, results, parsed_bom, options=render_options)


@app.callback(invoke_without_command=True)
def vulnerability_report(
    bom: str = typer.Argument(
        None,
        help="Path to a CycloneDX SBOM",
        show_default=False,
    ),
    formats: list[ReportFormat] = typer.Option(
        None,
        "--format",
        "-f",
        callback=_formats,
        encoding="utf-8",
        help='The report formats to generate [default: ["table"]]',
        show_default=False,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-d",
        callback=_output_dir,
        help="The directory where reports will be written [default: .]",
        show_default=False,
    ),
    base_report_name: str = typer.Option(
        None,
        "--base-report-name",
        "-b",
        help='The base name supplied for the generated reports [default: "hoppr-cop-report"]',
        show_default=False,
    ),
    os_distro: str = typer.Option(
        None,
        "--os-distro",
        "-o",
        envvar="OS_DISTRIBUTION",
        help=(
            "The operating system distribution; this is important "
            "to ensure accurate reporting of OS vulnerabilities from grype. "
            "Examples include rhel:8.6 or rocky:9"
        ),
        show_default=False,
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Mode to allow for offline scans",
        rich_help_panel="Experimental Options",
        show_default=False,
    ),
    download_dbs: bool = typer.Option(
        False,
        "--download-dbs",
        help="Mode to allow for downloading vulnerabilty databases",
        show_default=False,
    ),
    trace: bool = typer.Option(
        False,
        help="Print traceback information on unhandled error [default: no-trace]",
        show_default=False,
    ),
    assessment: str = typer.Option(
        None,
        help="Directory path to your analysis.assessment.yml [default: None]",
        show_default=False,
    ),
    epss: bool = typer.Option(
        False,
        "--epss",
        help="Enable EPSS score enhancement",
        show_default=False,
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version,
        is_eager=True,
        help="Show HopprCop version information",
    ),
    keep_serial_numbers: bool = typer.Option(False, help="Do not make a new serial number when enhancing SBOMs"),
    increment_version: bool = typer.Option(
        False,
        help=("Increment the version of the SBOM when enhancing. Only used if --keep-serial-numbers is also specifed"),
    ),
    scanner: list[ScannerOptions] = typer.Option(
        None,
        "--scanner",
        "-s",
        case_sensitive=False,
        help=(
            "Specify the scanners to use. If un-set, all relevant scanners are used. Valid options are any combination of the specified values in Yellow."
        ),
        show_default=False,
    ),
):
    """Generates vulnerability reports based on the specified SBOM and formats."""
    try:
        if not (bom or download_dbs):
            raise typer.BadParameter("Either a path to an SBOM file or the --download-dbs option is required")

        elif download_dbs:
            dbs_path_function(scanner)
        else:
            bom_path_function(
                scanner,
                bom,
                offline,
                os_distro,
                base_report_name,
                output_dir,
                epss,
                keep_serial_numbers,
                increment_version,
                formats,
                assessment,
            )
    except Exception as exc:
        if trace:
            rich.get_console().print_exception(show_locals=False)

        rich.print(f"[red]unexpected error: {exc}")
        raise typer.Exit(code=1) from exc
