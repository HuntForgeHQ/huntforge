import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class WpscanVulnModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        api_token = self._cfg('api_token')
        enumerate = self._cfg('enumerate', 'vp,vt,u,m')

        cmd = [
            'wpscan',
            '--url', f'https://{target}',
            '--output', container_out,
            '--format', 'json',
            '--enumerate', enumerate,
            '--disable-tls-checks'
        ]

        if api_token:
            cmd += ['--api-token', api_token]

        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'wpscan_vuln.json')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        self._run_subprocess(self.build_command(target, container_out))

        try:
            content = self._read_output_file(host_out)
            data = json.loads(content)
            vulnerabilities = data.get('vulnerabilities', [])
            main_theme = data.get('main_theme', {})
            if main_theme:
                main_theme['source'] = 'wpscan_main_theme'
                vulnerabilities.append(main_theme)
        except (EmptyOutputError, json.JSONDecodeError):
            vulnerabilities = []

        # Emit tags
        if vulnerabilities:
            tag_manager.add('has_cms', confidence='high', source='wpscan_vuln')
            tag_manager.add('has_vulnerabilities', confidence='high', source='wpscan_vuln')

            # Check for critical/high vulns
            for vuln in vulnerabilities:
                severity = vuln.get('severity', '').lower()
                if severity in ['critical', 'high']:
                    tag_manager.add('has_critical_vulns', confidence='high', source='wpscan_vuln')
                    break

        return {
            'results': vulnerabilities,
            'count': len(vulnerabilities),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        # Also implemented in run(), but keeping separate for clarity
        pass

    def estimated_requests(self) -> int:
        return 8000
