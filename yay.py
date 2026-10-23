import os, subprocess, dotbot


class Yay(dotbot.Plugin):
    # `pacman`: official repo packages (sudo pacman); `yay`: AUR packages (yay builds them as the user)
    _installers = {'pacman': ['sudo', 'pacman'], 'yay': ['yay']}

    def can_handle(self, directive):
        return directive in self._installers

    def handle(self, directive, data):
        self._cmd = self._installers[directive]
        return self._process(data)

    def _install(self, *pkgs):
        # LANG keeps the installer's own messages in English
        cmd = [*self._cmd, '--needed', '--noconfirm', '-S', *pkgs]
        return subprocess.run(cmd, env=dict(os.environ, LANG='en_US')).returncode == 0

    def _process(self, packages):
        # One pacman query instead of one install per package. Groups and provides names are
        # not in this list, so they still go through the installer below.
        installed = set(subprocess.run(['pacman', '-Qq'], capture_output=True, text=True).stdout.split())
        missing = [pkg for pkg in packages if pkg not in installed]
        for pkg in packages:
            if pkg in installed:
                self._log.info('Package "{}" is already installed.'.format(pkg))

        failed = []
        if missing:
            self._log.info('Installing {} packages. Please wait...'.format(len(missing)))
            if not self._install(*missing):
                # the batch failed as a whole: retry one by one to find the culprits
                failed = [pkg for pkg in missing if not self._install(pkg)]

        for pkg in failed:
            self._log.error("Could not install package '{}'".format(pkg))
        return not failed
