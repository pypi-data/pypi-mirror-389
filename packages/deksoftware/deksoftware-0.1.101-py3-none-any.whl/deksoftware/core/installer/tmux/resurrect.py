from ..base import register_installer
from .base import InstallerTmuxPlugin, register_tmux_plugin


@register_installer('tmux-resurrect')
@register_tmux_plugin
class TmuxResurrectInstaller(InstallerTmuxPlugin):
    plugin_name = "resurrect"
    shell_lines = """
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-strategy-nvim 'session'
    """
