from .base import InstallerBase, register_installer


@register_installer('kubectl')
class KubectlInstaller(InstallerBase):
    def run(self, repository):
        self.exe(self.path)
