"""
Template patcher for Flower to add i18n support
"""

import os
import shutil
from pathlib import Path
from typing import Optional


class FlowerTemplatePatcher:
    """Patch Flower templates to add i18n support"""

    def __init__(self, flower_path: Optional[Path] = None):
        if flower_path is None:
            # Try to find flower installation
            import flower
            self.flower_path = Path(flower.__file__).parent
        else:
            self.flower_path = flower_path

        self.templates_path = self.flower_path / "templates"
        self.static_path = self.flower_path / "static"
        self.backup_path = self.flower_path / "templates_backup"

    def backup_templates(self):
        """Backup original templates"""
        if not self.backup_path.exists():
            shutil.copytree(self.templates_path, self.backup_path)
            print(f"✓ Backed up templates to {self.backup_path}")
        else:
            print(f"✓ Backup already exists at {self.backup_path}")

    def restore_templates(self):
        """Restore original templates from backup"""
        if self.backup_path.exists():
            if self.templates_path.exists():
                shutil.rmtree(self.templates_path)
            shutil.copytree(self.backup_path, self.templates_path)
            print(f"✓ Restored templates from backup")
        else:
            print("✗ No backup found")

    def patch_base_template(self):
        """Patch base.html to include i18n script"""
        base_template = self.templates_path / "base.html"

        if not base_template.exists():
            print(f"✗ base.html not found at {base_template}")
            return False

        with open(base_template, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already patched
        if 'flower-i18n' in content:
            print("✓ base.html already patched")
            return True

        # Add i18n script before closing body tag
        i18n_script = '''
    <!-- Flower i18n support -->
    <script src="{{ static_url('js/i18n.js') }}"></script>'''

        content = content.replace('</body>', f'{i18n_script}\n  </body>')

        with open(base_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched base.html")
        return True

    def patch_navbar_template(self):
        """Patch navbar.html to add data attributes for i18n"""
        navbar_template = self.templates_path / "navbar.html"

        if not navbar_template.exists():
            print(f"✗ navbar.html not found at {navbar_template}")
            return False

        with open(navbar_template, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already patched
        if 'data-i18n=' in content:
            print("✓ navbar.html already patched")
            return True

        # Add data-i18n attributes to navigation items
        replacements = {
            'href="{{ reverse_url(\'workers\') }}">Workers</a>':
                'href="{{ reverse_url(\'workers\') }}" data-i18n="nav.workers">Workers</a>',
            'href="{{ reverse_url(\'tasks\') }}">Tasks</a>':
                'href="{{ reverse_url(\'tasks\') }}" data-i18n="nav.tasks">Tasks</a>',
            'href="{{ reverse_url(\'broker\') }}">Broker</a>':
                'href="{{ reverse_url(\'broker\') }}" data-i18n="nav.broker">Broker</a>',
            'href="https://flower.readthedocs.io/" target="_blank" rel="noopener">Documentation</a>':
                'href="https://flower.readthedocs.io/" target="_blank" rel="noopener" data-i18n="nav.documentation">Documentation</a>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(navbar_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched navbar.html")
        return True

    def patch_broker_template(self):
        """Patch broker.html to add data-i18n attributes"""
        broker_template = self.templates_path / "broker.html"

        if not broker_template.exists():
            print(f"✗ broker.html not found at {broker_template}")
            return False

        with open(broker_template, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'data-i18n=' in content:
            print("✓ broker.html already patched")
            return True

        # Add data-i18n attributes to table headers
        replacements = {
            '<th>Queue</th>': '<th data-i18n="broker.queue">Queue</th>',
            '<th>Messages</th>': '<th data-i18n="broker.messages">Messages</th>',
            '<th>Unacked</th>': '<th data-i18n="broker.unacked">Unacked</th>',
            '<th>Ready</th>': '<th data-i18n="broker.ready">Ready</th>',
            '<th>Consumers</th>': '<th data-i18n="broker.consumers">Consumers</th>',
            '<th>Idle since</th>': '<th data-i18n="broker.idle_since">Idle since</th>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(broker_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched broker.html")
        return True

    def patch_workers_template(self):
        """Patch workers.html to add data-i18n attributes"""
        workers_template = self.templates_path / "workers.html"

        if not workers_template.exists():
            print(f"✗ workers.html not found at {workers_template}")
            return False

        with open(workers_template, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'data-i18n=' in content:
            print("✓ workers.html already patched")
            return True

        # Add data-i18n attributes to table headers
        replacements = {
            '<th>Worker</th>': '<th data-i18n="workers.worker">Worker</th>',
            '<th class="text-center">Status</th>': '<th class="text-center" data-i18n="workers.status">Status</th>',
            '<th class="text-center">Active</th>': '<th class="text-center" data-i18n="workers.active">Active</th>',
            '<th class="text-center">Processed</th>': '<th class="text-center" data-i18n="workers.processed">Processed</th>',
            '<th class="text-center">Failed</th>': '<th class="text-center" data-i18n="workers.failed">Failed</th>',
            '<th class="text-center">Succeeded</th>': '<th class="text-center" data-i18n="workers.succeeded">Succeeded</th>',
            '<th class="text-center">Retried</th>': '<th class="text-center" data-i18n="workers.retried">Retried</th>',
            '<th class="text-center">Load Average</th>': '<th class="text-center" data-i18n="workers.load_average">Load Average</th>',
            '<th>Total</th>': '<th data-i18n="common.total">Total</th>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(workers_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched workers.html")
        return True

    def patch_tasks_template(self):
        """Patch tasks.html to add data-i18n attributes"""
        tasks_template = self.templates_path / "tasks.html"

        if not tasks_template.exists():
            print(f"✗ tasks.html not found at {tasks_template}")
            return False

        with open(tasks_template, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'data-i18n=' in content:
            print("✓ tasks.html already patched")
            return True

        # Add data-i18n attributes to table headers
        replacements = {
            '<th>Name</th>': '<th data-i18n="tasks.name">Name</th>',
            '<th>UUID</th>': '<th data-i18n="tasks.uuid">UUID</th>',
            '<th class="text-center">State</th>': '<th class="text-center" data-i18n="tasks.state">State</th>',
            '<th>args</th>': '<th data-i18n="tasks.args">args</th>',
            '<th>kwargs</th>': '<th data-i18n="tasks.kwargs">kwargs</th>',
            '<th>Result</th>': '<th data-i18n="tasks.result">Result</th>',
            '<th class="text-center">Received</th>': '<th class="text-center" data-i18n="tasks.received">Received</th>',
            '<th class="text-center">Started</th>': '<th class="text-center" data-i18n="tasks.started">Started</th>',
            '<th class="text-center">Runtime</th>': '<th class="text-center" data-i18n="tasks.runtime">Runtime</th>',
            '<th>Worker</th>': '<th data-i18n="tasks.worker">Worker</th>',
            '<th>Exchange</th>': '<th data-i18n="tasks.exchange">Exchange</th>',
            '<th>Routing Key</th>': '<th data-i18n="tasks.routing_key">Routing Key</th>',
            '<th class="text-center">Retries</th>': '<th class="text-center" data-i18n="tasks.retries">Retries</th>',
            '<th class="text-center">Revoked</th>': '<th class="text-center" data-i18n="tasks.revoked">Revoked</th>',
            '<th>Exception</th>': '<th data-i18n="tasks.exception">Exception</th>',
            '<th class="text-center">Expires</th>': '<th class="text-center" data-i18n="tasks.expires">Expires</th>',
            '<th class="text-center">ETA</th>': '<th class="text-center" data-i18n="tasks.eta">ETA</th>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(tasks_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched tasks.html")
        return True

    def patch_worker_template(self):
        """Patch worker.html to add data-i18n attributes"""
        worker_template = self.templates_path / "worker.html"

        if not worker_template.exists():
            print(f"✗ worker.html not found at {worker_template}")
            return False

        with open(worker_template, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'data-i18n=' in content:
            print("✓ worker.html already patched")
            return True

        # Add data-i18n attributes
        replacements = {
            # Tab titles
            'aria-selected="true">Pool</a>': 'aria-selected="true" data-i18n="worker.pool">Pool</a>',
            'aria-selected="false">Broker</a>': 'aria-selected="false" data-i18n="worker.broker">Broker</a>',
            'aria-selected="false">Queues</a>': 'aria-selected="false" data-i18n="worker.queues">Queues</a>',
            'aria-selected="false">Tasks</a>': 'aria-selected="false" data-i18n="worker.tasks">Tasks</a>',
            'aria-selected="false">Limits</a>': 'aria-selected="false" data-i18n="worker.limits">Limits</a>',
            'aria-selected="false">Config</a>': 'aria-selected="false" data-i18n="worker.config">Config</a>',
            'aria-selected="false">System</a>': 'aria-selected="false" data-i18n="worker.system">System</a>',
            'aria-selected="false">Other</a>': 'aria-selected="false" data-i18n="worker.other">Other</a>',
            # Dropdown actions
            '>Shut Down</a>': ' data-i18n="worker.shutdown">Shut Down</a>',
            '>Restart Pool</a>': ' data-i18n="worker.restart_pool">Restart Pool</a>',
            'data-bs-dismiss="dropdown">Refresh</a>': 'data-bs-dismiss="dropdown" data-i18n="worker.refresh">Refresh</a>',
            'data-bs-dismiss="dropdown">Refresh All</a>': 'data-bs-dismiss="dropdown" data-i18n="worker.refresh_all">Refresh All</a>',
            # Captions and legends
            '<caption>Worker pool options</caption>': '<caption data-i18n="worker.pool_options">Worker pool options</caption>',
            '<caption>Broker options</caption>': '<caption data-i18n="worker.broker_options">Broker options</caption>',
            '<caption>Configuration options</caption>': '<caption data-i18n="worker.config_options">Configuration options</caption>',
            '<caption>System usage statistics</caption>': '<caption data-i18n="worker.system_stats">System usage statistics</caption>',
            '<caption>Other statistics</caption>': '<caption data-i18n="worker.other_stats">Other statistics</caption>',
            '<legend class="form-label mt-md-5">Pool size control</legend>': '<legend class="form-label mt-md-5" data-i18n="worker.pool_size_control">Pool size control</legend>',
            # Labels and buttons
            '<label for="pool-size" class="col-sm-2 col-form-label text-nowrap">Pool size</label>': '<label for="pool-size" class="col-sm-2 col-form-label text-nowrap" data-i18n="worker.pool_size">Pool size</label>',
            '>Grow</button>': ' data-i18n="worker.grow">Grow</button>',
            '>Shrink</button>': ' data-i18n="worker.shrink">Shrink</button>',
            '<label for="min-autoscale" class="col-sm-2 form-label text-nowrap">Auto scale</label>': '<label for="min-autoscale" class="col-sm-2 form-label text-nowrap" data-i18n="worker.auto_scale">Auto scale</label>',
            # Table cells
            '<td>Worker PID</td>': '<td data-i18n="worker.worker_pid">Worker PID</td>',
            '<td>Prefetch Count</td>': '<td data-i18n="worker.prefetch_count">Prefetch Count</td>',
            '<th>Queue arguments</th>': '<th data-i18n="worker.queue_arguments">Queue arguments</th>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(worker_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched worker.html")
        return True

    def copy_static_files(self):
        """Copy i18n static files to Flower's static directory"""
        src_js = Path(__file__).parent / "static" / "js" / "i18n.js"
        dest_js = self.static_path / "js" / "i18n.js"

        if not dest_js.parent.exists():
            dest_js.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src_js, dest_js)
        print(f"✓ Copied i18n.js to {dest_js}")

    def patch(self):
        """Apply all patches"""
        print("Starting Flower template patching...")
        print(f"Flower installation path: {self.flower_path}")

        # Backup original templates
        self.backup_templates()

        # Apply patches
        self.patch_base_template()
        self.patch_navbar_template()
        self.patch_broker_template()
        self.patch_workers_template()
        self.patch_tasks_template()
        self.patch_worker_template()
        self.copy_static_files()

        print("\n✓ Patching complete!")
        print("\nNow restart Flower and open it in your browser.")
        print("You should see a language switcher in the navigation bar.")

    def unpatch(self):
        """Remove all patches"""
        print("Removing Flower i18n patches...")
        self.restore_templates()

        # Remove i18n.js
        i18n_js = self.static_path / "js" / "i18n.js"
        if i18n_js.exists():
            i18n_js.unlink()
            print(f"✓ Removed {i18n_js}")

        print("\n✓ Unpatching complete!")


def patch_flower():
    """Command-line function to patch Flower"""
    patcher = FlowerTemplatePatcher()
    patcher.patch()


def unpatch_flower():
    """Command-line function to unpatch Flower"""
    patcher = FlowerTemplatePatcher()
    patcher.unpatch()