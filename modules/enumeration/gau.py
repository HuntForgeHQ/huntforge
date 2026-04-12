import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError


class GauModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['sh', '-c', f'gau {target} --o {container_out} --threads 5']

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None,
            live_hosts: str = None, live_hosts_txt: str = None, **kwargs) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'gau.txt')
        container_out = host_out.replace('\\', '/')
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        # Prefer live_hosts_txt (plain text) — pipe domains into gau
        input_file = None
        if live_hosts_txt and os.path.exists(live_hosts_txt):
            input_file = live_hosts_txt
        elif live_hosts and os.path.exists(live_hosts):
            # live_hosts is JSON — extract URLs to temp text file
            try:
                with open(live_hosts) as f:
                    urls = json.load(f)
                if urls:
                    input_file = os.path.join(output_dir, 'raw', 'gau_input.txt')
                    with open(input_file, 'w') as f:
                        f.write('\n'.join(urls) + '\n')
            except (json.JSONDecodeError, Exception):
                pass

        if input_file:
            container_input = input_file.replace('\\', '/')
            cmd = ['sh', '-c', f'cat {container_input} | gau --o {container_out} --threads 5']
        else:
            cmd = self.build_command(target, container_out)

        self._run_subprocess(cmd, output_file=host_out)

        try:
            urls = [l for l in self._read_output_file(host_out).splitlines() if l.strip()]
        except EmptyOutputError:
            urls = []

        return {'results': urls, 'count': len(urls), 'requests_made': 50}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('params_found', confidence='low', source='gau')
