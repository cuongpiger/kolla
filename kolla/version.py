import os
import pbr.git
import pbr.version

kolla_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
version_info = pbr.version.VersionInfo('kolla')
git_info = pbr.git.get_git_short_sha(git_dir=os.path.join(kolla_path, ".git"))
