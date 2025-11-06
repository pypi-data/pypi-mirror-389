"""Templates for irods_environment.json for Utrecht University servers."""
from __future__ import annotations

from string import Template

_SERVERS_TO_ZONE = {
    "uu-youth": "nluu1p",
    "uu-geo": "nluu11p",
    "uu-i-lab": "nluu5p",
    "uu-dgk": "nluu9ot",
    "uu-science": "nluu6p",
    "uu-fsw": "nluu10p",
    "uu-its": "nluu12p",
    "uu-surf": "uu",
}


_BASE_TEMPLATE = """{
    "irods_host": "${host}.uu.nl",
    "irods_port": 1247,
    "irods_home": "/${zone}/home",
    "irods_user_name": "${email_address}",
    "irods_default_resource": "${resc}",
    "irods_zone_name": "${zone}",
    "irods_authentication_scheme": "${pam_scheme}",
    "irods_encryption_algorithm": "AES-256-CBC",
    "irods_encryption_key_size": 32,
    "irods_encryption_num_hash_rounds": 16,
    "irods_encryption_salt_size": 8,
    "irods_client_server_policy": "CS_NEG_REQUIRE",
    "irods_client_server_negotiation": "request_server_negotiation"
}
"""


class IBridgesUUTemplates:
    """Template for creating iRODS environment json files at Utrecht University."""

    name = "Utrecht University templates"
    questions = ["email_address"]
    descriptions = {
        "uu-youth": "YOUth Cohort Study",
        "uu-geo": "Geosciences",
        "uu-i-lab": "Humanities, Law, Economics, Governance, Open Societies",
        "uu-dgk": "Veterinary Medicine, Medicine",
        "uu-science": "Science",
        "uu-fsw": "Social and Behavioral Sciences",
        "uu-its": "University Corporate Offices",
        "uu-surf": "Yoda instance hosted at SURF"
    }

    @staticmethod
    def list_templates() -> list[str]:
        """List all templates for servers that are available."""
        return list(_SERVERS_TO_ZONE)

    @staticmethod
    def contains(template_name: str) -> bool:
        """Whether a template name is provided by this template."""
        return template_name in _SERVERS_TO_ZONE

    @staticmethod
    def environment_json(template_name: str, email_address: str) -> str:
        """Create a valid environment.json with the given inputs."""
        host = template_name[3:]+".data" if template_name != "uu-surf" else "data.yoda"
        zone = _SERVERS_TO_ZONE[template_name]
        template = Template(_BASE_TEMPLATE)
        pam_scheme = "pam_password" if template_name != "uu-surf" else "pam"
        resc = "irodsResc2" if template_name in ["uu-dgk", "uu-youth"] else "irodsResc"
        return template.substitute({"zone": zone, "email_address": email_address,
                                    "host": host, "resc": resc, "pam_scheme": pam_scheme})
