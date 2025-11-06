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
        """Patch navbar.html to use translation keys"""
        navbar_template = self.templates_path / "navbar.html"

        if not navbar_template.exists():
            print(f"✗ navbar.html not found at {navbar_template}")
            return False

        with open(navbar_template, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if already patched
        if '_(\'nav.workers\')' in content:
            print("✓ navbar.html already patched")
            return True

        # Replace text with translation function calls
        replacements = {
            '>Workers</a>': '>{{ _(\'nav.workers\') }}</a>',
            '>Tasks</a>': '>{{ _(\'nav.tasks\') }}</a>',
            '>Broker</a>': '>{{ _(\'nav.broker\') }}</a>',
            '>Documentation</a>': '>{{ _(\'nav.documentation\') }}</a>',
        }

        for old, new in replacements.items():
            content = content.replace(old, new)

        with open(navbar_template, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✓ Patched navbar.html")
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
        self.copy_static_files()

        print("\n✓ Patching complete!")
        print("\nTo apply i18n to your Flower handlers, add this to your code:")
        print("  from flower_i18n import I18nHandler, setup_i18n")
        print("  # Make your handlers inherit from I18nHandler")

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