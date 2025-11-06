from dektools.web.url import Url
from dektools.shell import shell_wrapper
from .base import PackageBase, register_package


@register_package('ali-generic')
class AliGenericPackage(PackageBase):
    @property
    def registry(self):
        return self.args[0]

    @property
    def auth(self):
        return dict(username=self.args[1], password=self.args[2])

    def location(self, version):
        if self.is_remote:
            url = Url.new(self.registry).update(**self.auth)
            return f"{url}/default?fileName={self.filename}&version={version}"
        return super().location(version)

    def push(self, path, version):
        shell_wrapper(f'curl -XPOST {self.location(version)} -F "file=@{path}"')
