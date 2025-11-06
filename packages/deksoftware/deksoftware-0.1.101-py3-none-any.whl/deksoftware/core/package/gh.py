from dektools.web.url import Url
from dekartifacts.artifacts.staticfiles import StaticfilesRepoArtifact
from .base import PackageBase, register_package


@register_package('gh')
class GithubPagesPackage(PackageBase):
    artifact_cls = StaticfilesRepoArtifact

    @property
    def registry(self):
        return self.args[0]

    @property
    def auth(self):
        if len(self.args) >= 3:
            return dict(username=self.args[1], password=self.args[2])

    def location(self, version):
        if self.is_remote:
            auth = self.auth
            if auth:
                url = Url.new(self.registry).update(**auth)
            else:
                url = self.registry
            return self.artifact.url_join(url, self.name, version or '')
        return super().location(version)
