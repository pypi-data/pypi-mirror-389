import click

from adam.commands.audit.audit_repair_tables import AuditRepairTables
from adam.commands.audit.audit_run import AuditRun
from adam.commands.command import Command
from adam.config import Config
from adam.repl_state import ReplState
from adam.sql.sql_completer import SqlCompleter
from adam.utils import log2
from adam.utils_athena import audit_column_names, audit_table_names, run_audit_query

class Audit(Command):
    COMMAND = 'audit'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(Audit, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)
        self.schema_read = False

    def command(self):
        return Audit.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)

        r = None
        if len(args) > 0:
            r = super().intermediate_run(cmd, state, args, Audit.cmd_list(), display_help=False)

        if not r or isinstance(r, str) and r == 'command-missing':
            sql = 'select * from audit order by ts desc limit 10'
            if args:
                sql = ' '.join(args)
            else:
                log2(sql)

            run_audit_query(sql)

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.L:
            if not self.schema_read:
                Config().wait_log(f'Inspecting audit database schema...')
                self.schema_read = True
                # warm up the caches first time when l: drive is accessed
                audit_column_names()
                audit_column_names(partition_cols_only=True)

            return super().completion(state) | SqlCompleter(
                lambda: audit_table_names(),
                columns=lambda table: audit_column_names(),
                partition_columns=lambda table: audit_column_names(partition_cols_only=True),
                variant='athena'
            ).completions_for_nesting()

        return {}

    def cmd_list():
        return [AuditRepairTables(), AuditRun()]

    def help(self, _: ReplState):
        return f'[{Audit.COMMAND}] <sql-statements>\t run SQL queries on Authena audit database'

class AuditCommandHelper(click.Command):
    def get_help(self, ctx: click.Context):
        Command.intermediate_help(super().get_help(ctx), Audit.COMMAND, Audit.cmd_list(), show_cluster_help=False)