from ..base import register_installer
from .base import InstallerTmuxPlugin, register_tmux_plugin


@register_installer('tmux-continuum')
@register_tmux_plugin
class TmuxResurrectInstaller(InstallerTmuxPlugin):
    plugin_name = "continuum"
    shell_lines = """
set -g @continuum-boot 'on'
set -g @continuum-restore 'on'
set -g @continuum-save-interval '5'
    """
