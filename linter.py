import os
from SublimeLinter.lint import Linter


class RubyLinter(Linter):
    def context_sensitive_executable_path(self, cmd):
        # The default implementation will look for a user defined `executable`
        # setting.
        success, executable = super().context_sensitive_executable_path(cmd)
        if success:
            return True, executable

        gem_name = cmd[0] if isinstance(cmd, list) else cmd

        if self.settings.get('use_bundle_exec', False):
            return True, ['bundle', 'exec', gem_name]

        rvm = self.which('rvm-auto-ruby')
        if rvm:
            return True, [rvm, '-S', gem_name]

        return False, None


class Rubocop(RubyLinter):
    defaults = {
        'selector': 'source.ruby - text.html - text.haml'
    }
    regex = (
        r'^.+?:(?P<line>\d+):(?P<col>\d+): '
        r'(:?(?P<warning>[RCW])|(?P<error>[EF])): '
        r'(?P<fixable>\[Correctable\] )?'
        r'((?P<code>\w+/\w+): )?'
        r'(?P<message>.+)$'
    )

    def cmd(self):
        """Build command, using STDIN if a file path can be determined."""

        command = ['rubocop', '--format', 'emacs', '--display-cop-names']

        path = self.filename
        if not path:
            # File is unsaved, and by default unsaved files use the default
            # rubocop config because they do not technically belong to a folder
            # that might contain a custom .rubocop.yml. This means the lint
            # results may not match the rules for the currently open project.
            #
            # If the current window has open folders then we can use the
            # first open folder as a best-guess for the current projects
            # root folder - we can then pretend that this unsaved file is
            # inside this root folder, and rubocop will pick up on any
            # config file if it does exist:
            folders = self.view.window().folders()
            if folders:
                path = os.path.join(folders[0], 'untitled.rb')

        if path:
            # With this path we can instead pass the file contents in via STDIN
            # and then tell rubocop to use this path (to search for config
            # files and to use for matching against configured paths - i.e. for
            # inheritance, inclusions and exclusions).
            #
            # The 'force-exclusion' overrides rubocop's behavior of ignoring
            # global excludes when the file path is explicitly provided:
            command += ['--force-exclusion', '--stdin', path]
            # Ensure the files contents are passed in via STDIN:
            self.tempfile_suffix = None
        else:
            self.tempfile_suffix = 'rb'
            command += ['${temp_file}']

        return command
