import os
from modules.base_module import BaseModule
from core.exceptions import EmptyOutputError

class GowitnessModule(BaseModule):
    def build_command(self, target: str, container_out: str) -> list:
        return ['gowitness', 'single', target]

    def run(self, target: str, output_dir: str, tag_manager, config: dict = None) -> dict:
        self.config = config or {}
        
        host_db = os.path.join(output_dir, 'raw', 'gowitness.sqlite3')
        container_db = f"/{host_db.replace('\\', '/')}"
        host_screenshot_dir = os.path.join(output_dir, 'raw', 'screenshots')
        container_screenshot_dir = f"/{host_screenshot_dir.replace('\\', '/')}"
        
        os.makedirs(host_screenshot_dir, exist_ok=True)
        
        httpx_file = os.path.join(output_dir, 'raw', 'httpx.json')
        container_input = f"/{httpx_file.replace('\\', '/')}"
        
        if os.path.exists(httpx_file):
            cmd = ['gowitness', 'file', '-f', container_input, '--screenshot-path', container_screenshot_dir, '--db-path', container_db]
        else:
            cmd = ['gowitness', 'single', target, '--screenshot-path', container_screenshot_dir, '--db-path', container_db]

        self._run_subprocess(cmd)
        
        # Count screenshots taken
        try:
            count = len(os.listdir(host_screenshot_dir))
        except:
            count = 0
            
        return {'results': [], 'count': count, 'requests_made': count}

    def emit_tags(self, result: dict, tag_manager) -> None:
        if result['count'] > 0:
            tag_manager.add('screenshots_taken', confidence='high', source='gowitness')
