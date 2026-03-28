import os
import xml.etree.ElementTree as ET
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class NiktoModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['nikto', '-h', f'https://{target}', '-o', container_out, '-Format', 'xml', '-maxtime', '600', '-nointeractive']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'nikto.xml')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        self._run_subprocess(self.build_command(target, container_out))

        try:
            content = self._read_output_file(host_out)
            root = ET.fromstring(content)
            # Nikto XML: <scanlist><item id="1" ...><description>...</description></item>...
            vulns = []
            for item in root.findall('.//item'):
                desc_elem = item.find('description')
                if desc_elem is not None and desc_elem.text:
                    vulns.append(desc_elem.text.strip())
        except (EmptyOutputError, ET.ParseError):
            vulns = []

        return {
            'results': vulns,
            'count': len(vulns),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_vulnerabilities', confidence='medium', source='nikto')

    def estimated_requests(self) -> int:
        return 2000
