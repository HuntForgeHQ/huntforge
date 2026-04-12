import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError


class DalfoxModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['dalfox', 'url', target, '-o', container_out, '--silence']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'dalfox.txt')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        # Use paramspider output if available for file-based scanning
        params_file = os.path.join(output_dir, 'raw', 'paramspider.txt')

        if os.path.exists(params_file):
            container_input = params_file.replace('\\', '/')
            cmd = ['dalfox', 'file', container_input, '-o', container_out, '--silence']
        else:
            cmd = self.build_command(f'https://{target}', container_out)

        self._run_subprocess(cmd, output_file=host_out)

        try:
            vulns = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            vulns = []

        return {'results': vulns, 'count': len(vulns), 'requests_made': 500}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('xss_found', confidence='high', source='dalfox')
            tag_manager.add('has_vulnerabilities', confidence='high', source='dalfox')
