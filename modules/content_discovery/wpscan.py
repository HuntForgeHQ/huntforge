import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class WpscanModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['wpscan', '--url', f'https://{target}', '--output', container_out, '--format', 'json', '--enumerate', 'vp,vt,tt,cb,dbe,u,m']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_out = os.path.join(output_dir, 'raw', 'wpscan.json')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)
        
        cmd = self.build_command(target, container_out)
        api_token = os.environ.get("WPSCAN_API_TOKEN")
        if api_token:
            cmd.extend(['--api-token', api_token])

        self._run_subprocess(cmd)
        
        try:
            data = json.loads(self._read_output_file(host_out))
            vulns = []
            # Wpscan JSON is nested
            for version, v_data in data.get('version', {}).items():
                vulns.extend(v_data.get('vulnerabilities', []))
            for plugin, p_data in data.get('plugins', {}).items():
                vulns.extend(p_data.get('vulnerabilities', []))
        except (EmptyOutputError, json.JSONDecodeError):
            vulns = []
            
        return {'results': vulns, 'count': len(vulns), 'requests_made': 500}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('has_vulnerabilities', confidence='high', source='wpscan')
