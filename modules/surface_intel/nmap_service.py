import os
import xml.etree.ElementTree as ET
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class NmapServiceModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['nmap', '-sV', '-sC', '--open', '-oX', container_out, target]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'nmap.xml')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        ports_file = os.path.join(output_dir, 'raw', 'naabu.txt')
        if os.path.exists(ports_file):
            try:
                with open(ports_file, 'r') as f:
                    ports = ','.join([l.strip() for l in f.readlines() if l.strip()])
                cmd = ['nmap', '-sV', '-sC', '--open', '-p', ports, '-oX', container_out, target]
            except:
                cmd = self.build_command(target, container_out)
        else:
            cmd = self.build_command(target, container_out)

        self._run_subprocess(cmd)
        
        try:
            tree = ET.parse(host_out)
            root = tree.getroot()
            ports_found = root.findall(".//port")
        except:
            ports_found = []
            
        return {'results': [], 'count': len(ports_found), 'requests_made': 1000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('services_identified', confidence='high', source='nmap')
