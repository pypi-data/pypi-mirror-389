"""Scan an SBOM using the Grype CLI.

--------------------------------------------------------------------------------
SPDX-FileCopyrightText: Copyright © 2022 Lockheed Martin <open.source@lmco.com>
SPDX-FileName: hopprcop/grype/grype_scanner.py
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

import contextlib
import json
import os

from subprocess import PIPE, Popen
from typing import ClassVar

import rich

from hoppr import HopprError, Sbom, Vulnerability
from hoppr.utils import get_package_url

from hopprcop.utils import (
    create_bom_from_purl_list,
    unsupported_purl_feedback,
)
from hopprcop.vulnerability_scanner import VulnerabilitySuper


class GrypeScanner(VulnerabilitySuper, author="Anchore", name="Grype", offline_mode_supported=True):
    """This scanner utilizes the anchore grype command line to gather vulnerabilities."""

    required_tools_on_path: ClassVar[list[str]] = ["grype"]
    grype_os_distro = os.getenv("OS_DISTRIBUTION", None)

    process_environment = None
    supported_types: ClassVar[list[str]] = [
        "cargo",
        "composer",
        "docker",
        "gem",
        "golang",
        "maven",
        "npm",
        "nuget",
        "oci",
        "pypi",
        "rpm",
    ]

    def __init__(self, offline_mode: bool = False, grype_os_distro: str | None = None):
        self.grype_os_distro = grype_os_distro or os.getenv("OS_DISTRIBUTION", None)

        self.offline_mode = offline_mode
        self.process_environment = os.environ.copy()
        if self.offline_mode:
            self.process_environment["GRYPE_DB_AUTO_UPDATE"] = "false"
            self.process_environment["GRYPE_DB_VALIDATE_AGE"] = "false"

        super().__init__()

    def get_vulnerability_db(self) -> bool:
        """Downloads vulnerability database."""
        args = ["grype", "db", "update"]

        with Popen(args, stdout=PIPE, stderr=PIPE) as process:
            stdout, stderr = process.communicate()

            if not stdout and stderr:
                rich.print(f"GrypeScanner: generated an exception: {stderr.decode()}")
                return False

            rich.print(f"GrypeScanner: {stdout.decode()}")
            return True

    def get_vulnerabilities_for_purl(self, purls: list[str]) -> list[Vulnerability]:  # pragma: no cover
        """Get the vulnerabilities for a list of package URLS (purls).

        Returns a list of CycloneDX vulnerabilities.
        """
        bom = create_bom_from_purl_list(purls)
        return self.get_vulnerabilities_for_sbom(bom)

    def get_vulnerabilities_for_sbom(self, bom: Sbom) -> list[Vulnerability]:
        """Get the vulnerabilities for a CycloneDx compatible Software Bill of Materials (SBOM).

        Returns a list of CycloneDX vulnerabilities.
        """
        # Check for unsupported purl types and report if found
        purls = [component.purl for component in bom.components or [] if component.purl]
        unsupported_purl_feedback(self._scanner_name, self.supported_types, [get_package_url(purl) for purl in purls])

        results: dict[str, Vulnerability] = {}

        args = ["grype", "--output", "cyclonedx-json", "--by-cve"]
        if self.grype_os_distro is not None:
            args += ["--distro", self.grype_os_distro]

        with Popen(args, stdout=PIPE, stdin=PIPE, stderr=PIPE, env=self.process_environment) as process:
            # Remove tools from metadata due to cyclonedx-go only having partial support for spec version 1.5 (as of 0.72.0)
            # TODO: roll back once full support is in cyclonedx-go
            parsed_bom = bom.copy(deep=True)
            if parsed_bom.metadata:
                parsed_bom.metadata.tools = None

            stdout, stderr = process.communicate(input=(bytes(parsed_bom.json(), "utf-8")))
            if process.returncode != 0:
                raise HopprError(f"{self.__class__.__name__} generated an exception: {stderr.decode()}")

            # Code from here on out will be pretty similar to how Trivy handles the process.
            bom_dict = json.loads(stdout)
            purl_by_bom_ref: dict[str, str] = {}

            for component in bom_dict.get("components", []):
                # Get the purls now....
                with contextlib.suppress(KeyError):
                    purl_by_bom_ref[component["bom-ref"]] = component["purl"]

            for vulnerability_dict in bom_dict.get("vulnerabilities", []):
                vulnerability = Vulnerability.parse_obj(vulnerability_dict)
                self._prep_scanner_vulnerabilities(results, vulnerability, purl_by_bom_ref, purls)

        return list(results.values())
