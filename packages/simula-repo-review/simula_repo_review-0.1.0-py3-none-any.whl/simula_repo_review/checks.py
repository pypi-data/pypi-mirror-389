from importlib.resources.abc import Traversable
from repo_review.ghpath import GHPath


class Simula:
    family = "Simula"
    url = "https://simulink.simula.no/policy/56"


def find_license_file(package: Traversable) -> str | None:
    """Check for the presence of a LICENSE file in the package directory.
    Returns the filename if found, otherwise None."""
    options = {"LICENSE", "LICENSE.txt", "LICENSE.md"}
    for option in options:
        if package.joinpath(option).is_file():
            return option
    return None


class SI001(Simula):
    "LICENSE file is OSI approved"

    @staticmethod
    def check(package: Traversable) -> bool:
        """
        All projects should have a LICENSE file that is OSI approved
        """
        path = find_license_file(package)
        if path is None:
            return False

        license = package.joinpath(path)
        content = license.read_text().lower()
        osi_approved_licenses = [
            "mit license",
            "apache license",
            "gnu general public license",
            "bsd license",
            "mozilla public license",
            "gnu lesser general public license",
            "gnu general public license",
        ]
        return any(osi_license in content for osi_license in osi_approved_licenses)


valid_companies = ("simula", "simula research laboratory", "simulamet", "simula uib")


class SI002(Simula):
    "Simula is copyright holder"

    @staticmethod
    def check(package: Traversable) -> bool:
        """
        All projects should have a LICENSE where Simula is listed as a copyright holder
        """
        path = find_license_file(package)
        if path is None:
            return False

        license = package.joinpath(path)
        content = license.read_text().lower()
        for company in valid_companies:
            if company in content:
                return True
        return False


valid_organizations = ("simula", "scientificcomputing", "computationalphysiology")


class SI003(Simula):
    "Part of Simula organization"

    @staticmethod
    def check(package: GHPath) -> bool:
        """
        All repositories should be part of a Simula GitHuborganization
        """
        org = package.repo.split("/")[0].lower()
        for valid_org in valid_organizations:
            if valid_org == org:
                return True
        return False


def repo_review_checks() -> dict[str, Simula]:
    return {p.__name__: p() for p in Simula.__subclasses__()}
