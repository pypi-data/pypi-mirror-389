from datetime import datetime, timedelta

from adam.commands.command import Command
from adam.repl_state import ReplState
from adam.utils import log2
from adam.utils_audits import Audits

class ShowLast10(Command):
    COMMAND = 'show last'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(ShowLast10, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)

    def command(self):
        return ShowLast10.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)
        limit = 10
        if args:
            try:
                limit = int(args[0])
            except:
                pass

        query = '\n    '.join([
            "SELECT * FROM audit",
            f"WHERE drive <> 'z' and ({Audits.date_from(datetime.now() - timedelta(days=30))})",
            f"ORDER BY ts DESC LIMIT {limit};"])
        log2(query)
        log2()
        Audits.run_audit_query(query)

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.L:
            return super().completion(state, {'10': None})

        return {}

    def help(self, _: ReplState):
        return f'{ShowLast10.COMMAND} [limit]\t show last <limit> audit lines'