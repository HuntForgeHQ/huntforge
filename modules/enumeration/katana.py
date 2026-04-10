import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError


class KatanaModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['katana', '-u', f'https://{target}', '-o', container_out, '-silent', '-jc', '-kf', 'all', '-d', '3']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, live_hosts: str = None, **kwargs) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'katana.txt')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        # If live_hosts file is provided, use -list mode
        if live_hosts and os.path.exists(live_hosts):
            container_input = live_hosts.replace('\\', '/')
            cmd = ['katana', '-list', container_input, '-o', container_out, '-silent', '-jc', '-kf', 'all', '-d', '3']
        else:
            cmd = self.build_command(target, container_out)

        self._run_subprocess(cmd)

        try:
            content = self._read_output_file(host_out)
            urls = [line.strip() for line in content.splitlines() if line.strip()]
        except EmptyOutputError:
            urls = []

        return {'results': urls, 'count': len(urls), 'requests_made': 1000}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('api_endpoints_found', confidence='medium', source='katana')
            if result['count'] > 1000:
                tag_manager.add('large_endpoint_set', confidence='high', source='katana')
