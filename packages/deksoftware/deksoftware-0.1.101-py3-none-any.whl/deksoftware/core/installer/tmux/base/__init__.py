import os
from pathlib import Path
from collections import OrderedDict
from dektools.file import remove_path, write_file, read_text, normal_path, iglob
from dektools.zip import decompress_files
from dektools.shell import shell_wrapper
from ...base import InstallerBase, register_installer

tmux_plugins = OrderedDict()


def register_tmux_plugin(cls):
    tmux_plugins[cls.plugin_name] = cls
    return cls


class InstallerTmuxPlugin(InstallerBase):
    plugin_name = None
    path_plugins = "~/.tmux/plugins"
    path_conf = "~/.tmux.conf"
    shell_lines = ""

    def run(self, repository):
        path_out = Path(decompress_files(self.path)).resolve()
        path_dir = path_out / os.listdir(path_out)[0]
        path_target = normal_path(os.path.join(self.path_plugins, self.plugin_name))
        path_conf = normal_path(self.path_conf)
        write_file(path_target, m=path_dir)
        path_tmux = next(iter(iglob('*.tmux', path_target)))
        conf_line = f"\n{self.shell_lines}\nrun-shell {path_tmux}\n"
        if conf_line not in read_text(path_conf, default=""):
            write_file(path_conf, s=conf_line, a=True)
        remove_path(path_out)
        shell_wrapper(f"tmux source-file {path_conf}")


@register_installer('tmux-plugins')
class TmuxPluginsInstaller(InstallerBase):
    def run(self, repository):
        for name in tmux_plugins:
            repository.install(f"tmux-{name}")
