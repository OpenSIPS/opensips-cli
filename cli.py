import cmd
from config_parser import *


class OpenSIPSCTLShell(cmd.Cmd, object):
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = '(%s): ' % Config.ConfigMap['DEFAULT']['prompt_name']
        self.intro = Config.ConfigMap['DEFAULT']['prompt_intro']
        self.undoc_header = None

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if header is not None:
            if cmds:
                self.stdout.write('%s\n' % str(header))
                if self.ruler:
                        self.stdout.write('%s\n' % str(self.ruler*len(header)))
                self.columnize(cmds, maxcol-1)
                self.stdout.write('\n')

    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(OpenSIPSCTLShell, self).cmdloop(intro='')
                break
            except KeyboardInterrupt:
                print('^C')

    def do_EOF(self, line):
        print('^D')
        return True

    def do_quit(self, line):
        pass
        return True

    def do_exit(self, line):
        pass
        return True
