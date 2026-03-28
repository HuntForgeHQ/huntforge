import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class CorsScannerModule(BaseModule):
    def build_command(self, target: str, container_out: str, input_file: str = None) -> list:
        # corsy.py -i <input_file> -o <output_file> -t <threads>
        threads = self._cfg('threads', 10)

        cmd = ['python3', '/usr/local/bin/corsy.py', '-i', input_file or f'/tmp/urls_{target}.txt', '-o', container_out, '-t', str(threads)]

        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}

        host_out = os.path.join(output_dir, 'raw', 'cors_scan.json')
        container_out = f"/{host_out.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_out), exist_ok=True)

        # Determine input file: use all_urls.txt from Phase 6 output
        input_file = os.path.join(output_dir, 'processed', 'all_urls.txt')
        if not os.path.exists(input_file):
            # Fallback: use live_hosts.json converted to simple URLs
            live_hosts_file = os.path.join(output_dir, 'processed', 'live_hosts.json')
            if os.path.exists(live_hosts_file):
                try:
                    with open(live_hosts_file, 'r') as f:
                        hosts = json.load(f)
                    urls = []
                    for host in hosts:
                        if isinstance(host, dict):
                            url = host.get('url', '')
                        elif isinstance(host, str):
                            url = host
                        else:
                            continue
                        if url and not url.startswith('http'):
                            url = f'https://{url}'
                        urls.append(url)
                    # Write temporary input file
                    temp_input = os.path.join(output_dir, 'raw', 'cors_input_urls.txt')
                    with open(temp_input, 'w') as f:
                        f.write('\n'.join(urls))
                    input_file = temp_input
                except (json.JSONDecodeError, KeyError):
                    input_file = None
            else:
                input_file = None

        if input_file:
            container_input = f"/{input_file.replace('\\', '/')}"
            command = self.build_command(target, container_out, container_input)
        else:
            # No input file available, skip
            return {'results': [], 'count': 0, 'requests_made': 0}

        try:
            self._run_subprocess(command)
        except Exception as e:
            # Tool may fail if no URLs found; treat as empty results
            return {'results': [], 'count': 0, 'requests_made': 0}

        try:
            content = self._read_output_file(host_out)
            data = json.loads(content)
            issues = data.get('issues', [])
        except (EmptyOutputError, json.JSONDecodeError):
            issues = []

        # Emit tags for CORS findings
        if issues:
            tag_manager.add('cors_bypass', confidence='high', source='cors_scanner')
            tag_manager.add('has_vulnerabilities', confidence='medium', source='cors_scanner')

        return {
            'results': issues,
            'count': len(issues),
            'requests_made': self.estimated_requests()
        }

    def estimated_requests(self) -> int:
        return 1000
