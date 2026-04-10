import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError


class SQLMapModule(BaseModule):
    def build_command(self, target: str, container_out: str, param_file: str = None) -> list:
        cmd = ['sqlmap', '--batch', '--random-agent', '--output', container_out, '--output-format=json']

        threads = self._cfg('threads', 4)
        level = self._cfg('level', 2)
        risk = self._cfg('risk', 2)

        cmd += ['--threads', str(threads), '--level', str(level), '--risk', str(risk)]

        if param_file:
            cmd += ['-m', param_file]
        else:
            cmd += ['-u', f'https://{target}']

        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None, **kwargs) -> dict:
        self.config = config or {}

        host_output_file = os.path.join(output_dir, 'raw', 'sqlmap.json')
        container_output_file = host_output_file.replace('\\', '/')
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        # Check for parameters file from Phase 5
        params_file = os.path.join(output_dir, 'processed', 'parameters.json')
        container_params_file = None

        if os.path.exists(params_file):
            try:
                with open(params_file, 'r') as f:
                    params_data = json.load(f)
                urls = []
                if isinstance(params_data, list):
                    for param_entry in params_data:
                        if isinstance(param_entry, dict):
                            url = param_entry.get('url', '')
                            if url:
                                urls.append(url)
                        elif isinstance(param_entry, str):
                            urls.append(param_entry)
                if urls:
                    urls_file = os.path.join(output_dir, 'raw', 'sqlmap_urls.txt')
                    with open(urls_file, 'w') as f:
                        f.write('\n'.join(urls[:20]))  # Limit to 20 URLs to avoid blowup
                    container_params_file = urls_file.replace('\\', '/')
            except (json.JSONDecodeError, KeyError):
                pass

        command = self.build_command(target, container_output_file, container_params_file)
        self._run_subprocess(command)

        try:
            content = self._read_output_file(host_output_file)
            results = []
            if content.strip():
                data = json.loads(content)
                for url, details in data.items():
                    if isinstance(details, dict) and 'data' in details:
                        for item in details['data']:
                            item['url'] = url
                            results.append(item)
                    else:
                        results.append({'url': url, 'info': details})
        except (EmptyOutputError, json.JSONDecodeError):
            results = []

        return {
            'results': results,
            'count': len(results),
            'requests_made': self.estimated_requests()
        }

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('sqli_found', confidence='high', source='sqlmap')
            tag_manager.add('has_vulnerabilities', confidence='high', source='sqlmap')

    def estimated_requests(self) -> int:
        return 15000
