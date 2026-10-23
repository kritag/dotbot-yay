import os, subprocess, dotbot, time
from enum import Enum

class PkgStatus(Enum):
    # These names will be displayed
    UP_TO_DATE = 'Up to date'
    INSTALLED= 'Installed'
    UPDATED = 'Updated'
    NOT_FOUND = 'Not Found'
    ERROR = "Error"
    NOT_SURE = 'Could not determine'

class Yay(dotbot.Plugin):
    _directive = 'yay'

    def __init__(self, context):
        super(Yay, self).__init__(self)
        self._context = context
        self._strings = {}

        # Names to search the query string for
        self._strings[PkgStatus.ERROR] = "aborting"
        self._strings[PkgStatus.NOT_FOUND] = "Could not find all required packages"
        self._strings[PkgStatus.UPDATED] = "Net Upgrade Size:"
        self._strings[PkgStatus.INSTALLED] = "Total Installed Size:"
        self._strings[PkgStatus.UP_TO_DATE] = "is up to date -- skipping"

    def can_handle(self, directive):
        return directive == self._directive

    def handle(self, directive, data):
        if directive != self._directive:
            raise ValueError('Yay cannot handle directive %s' %
                directive)
        return self._process(data)

    def _process(self, packages):
        results = {}
        successful = [PkgStatus.UP_TO_DATE, PkgStatus.UPDATED, PkgStatus.INSTALLED]

        # One pacman query instead of one yay start per package. Groups and provides names are
        # not in this list, so they still go through yay below.
        installed = set(subprocess.run(['pacman', '-Qq'], capture_output=True, text=True).stdout.split())
        missing = [pkg for pkg in packages if pkg not in installed]
        if len(packages) > len(missing):
            results[PkgStatus.UP_TO_DATE] = len(packages) - len(missing)

        if missing:
            self._log.info('Installing {} packages. Please wait...'.format(len(missing)))
            if subprocess.run(['yay', '--needed', '--noconfirm', '-S', *missing],
                              env=dict(os.environ, LANG='en_US')).returncode == 0:
                results[PkgStatus.INSTALLED] = len(missing)
            else:
                # the batch failed as a whole: retry one by one to find the culprit
                for pkg in missing:
                    result = self._install(pkg)
                    results[result] = results.get(result, 0) + 1
                    if result not in successful:
                        self._log.error("Could not install package '{}'".format(pkg))

        success = all(result in successful for result in results)
        if success:
            self._log.info('\nAll packages installed successfully')

        for status, amount in results.items():
            log = self._log.info if status in successful else self._log.error
            log('{} {}'.format(amount, status.value))

        return success

    def _install(self, pkg):
        # to have a unified string which we can query
        # we need to execute the command with LANG=en_US
        cmd = 'LANG=en_US yay --needed --noconfirm -S {}'.format(pkg)

        self._log.info("Installing \"{}\". Please wait...".format(pkg))

        # needed to avoid conflicts due to locking
        time.sleep(1)

        proc = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.stdout.read()
        proc.stdout.close()

        for item in self._strings.keys():
            if out.decode("utf-8").find(self._strings[item]) >= 0:
                return item

        self._log.warning("Could not determine what happened with package {}".format(pkg))
        return PkgStatus.NOT_SURE
