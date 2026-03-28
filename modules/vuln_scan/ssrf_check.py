import os
import json
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class SSRFCheckModule(BaseModule):
    def build_command(self, target: str, container_out: str, input_file: str = None) -> list:
        # Use nuclei with ssrf templates only
        cmd = ['nuclei', '-json-export', container_out, '-silent']

        if input_file:
            cmd += ['-l', input_file]
        else:
            cmd += ['-target', f'https://{target}']

        # Force ssrf tag
        cmd += ['-tags', 'ssrf']

        # Additional config
        severity = self._cfg('severity', 'critical,high,medium,low')
        if severity:
            cmd += ['-severity', severity]

        return cmd

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}

        host_output_file = os.path.join(output_dir, 'raw', 'ssrf.json')
        container_output_file = f"/{host_output_file.replace('\\', '/')}"
        os.makedirs(os.path.dirname(host_output_file), exist_ok=True)

        # SSRF check uses parameters file from Phase 5
        params_file = os.path.join(output_dir, 'processed', 'parameters.json')
        container_input_file = None

        if os.path.exists(params_file):
            # Convert parameters.json to list of URLs
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
                # Write URLs file
                urls_file = os.path.join(output_dir, 'raw', 'ssrf_urls.txt')
                with open(urls_file, 'w') as f:
                    f.write('\n'.join(urls))
                container_input_file = f"/{urls_file.replace('\\', '/')}"
            except (json.JSONDecodeError, KeyError):
                container_input_file = None

        command = self.build_command(target, container_output_file, container_input_file)

        try:
            self._run_subprocess(command)
        except Exception:
            # Tools may fail if no URLs; treat as empty
            return {'results': [], 'count': 0, 'requests_made': 0}

        try:
            content = self._read_output_file(host_output_file)
            results = []
            for line in content.splitlines():
                if line.strip():
                    results.append(json.loads(line))
        except (EmptyOutputError, json.JSONDecodeError):
            results = []

        # Emit tags
        if results:
            tag_manager.add('ssrf_found', confidence='high', source='ssrf_check')
            tag_manager.add('has_vulnerabilities', confidence='high', source='ssrf_check')

        return {
            'results': results,
            'count': len(results),
            'requests_made': self.estimated_requests()
        }

    def estimated_requests(self) -> int:
        return 5000
