import re
from typing import Dict, Any, List


class OutputParser:
    def __init__(self):
        # Map device types to their specific parsing functions
        self.parsers = {
            "cisco_xe": self.parse_cisco,
            "cisco_ios": self.parse_cisco,
            "cisco_nxos": self.parse_cisco,
            "cisco_ios_xr": self.parse_cisco,
            "hirschmann": self.parse_hirschmann,
            "juniper": self.parse_juniper,
        }
        # Stats tracking
        self.hostname_stats = {"extracted": 0, "failed": 0}

    # -------------------------
    # Main entry point
    # -------------------------
    def parse_output(self, device_type: str, command_output: str) -> Dict[str, Any]:
        parser = self.parsers.get(device_type, self.generic_parse)
        parsed_data = parser(command_output)

        # If hostname missing, fallback
        if "hostname" not in parsed_data or parsed_data["hostname"] == "Unknown":
            hostname = self.extract_hostname(command_output)
            parsed_data["hostname"] = hostname
            if hostname == "Unknown":
                self.hostname_stats["failed"] += 1
            else:
                self.hostname_stats["extracted"] += 1

        return parsed_data

    # -------------------------
    # Vendor-specific parsers
    # -------------------------
    def parse_cisco(self, output: str) -> Dict[str, Any]:
        return {
            "hostname": self.extract_hostname(output),
            "version": self._search_regex(r"Version\s+([\S]+)", output),
            "serial": self._search_regex(r"System serial number\s*:\s*(\S+)", output),
            "model": self._search_regex(r"Model number\s*:\s*(\S+)", output),
            "uptime": self._search_regex(r"uptime is (.+)", output),
            "mac_address": self._search_regex(r"System MAC Address\s*:\s*([0-9a-f:.]+)", output),
        }

    def parse_hirschmann(self, output: str) -> Dict[str, Any]:
        # TODO: implement real parsing when needed
        return {"hostname": self.extract_hostname(output)}

    def parse_juniper(self, output: str) -> Dict[str, Any]:
        # TODO: implement real parsing when needed
        return {"hostname": self.extract_hostname(output)}

    # -------------------------
    # Generic fallback parser
    # -------------------------
    def generic_parse(self, output: str) -> Dict[str, Any]:
        return {
            "hostname": self.extract_hostname(output),
            "serial": self._search_regex(r"[Ss]erial\s*[Nn]umber\s*[:=]?\s*(\S+)", output),
            "mac_address": self._search_regex(r"([0-9a-f]{2}(?::[0-9a-f]{2}){5})", output),
            "model": self._search_regex(r"Model\s*[:=]?\s*(\S+)", output),
            "version": self._search_regex(r"[Vv]ersion\s*[:=]?\s*([\w.\-()]+)", output),
            "uptime": self._search_regex(r"[Uu]ptime\s*[:=]?\s*(.+)", output),
        }

    # -------------------------
    # Hostname extraction
    # -------------------------
    def extract_hostname(self, output: str) -> str:
        patterns = [
            r"([A-Za-z0-9\-_]+)\s*>",       # device>
            r"([A-Za-z0-9\-_]+)\s*#",       # device#
            r"Hostname\s*[:=]?\s*([A-Za-z0-9\-_]+)",  # explicit Hostname:
        ]
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        return "Unknown"

    # -------------------------
    # Utility functions
    # -------------------------
    def _search_regex(self, pattern: str, text: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else "Unknown"

    def get_hostname_extraction_stats(self) -> Dict[str, int]:
        return self.hostname_stats
