import concurrent
import time
import requests

from adam.commands.command import Command
from adam.config import Config
from adam.repl_state import ReplState
from adam.utils import log, log2
from adam.utils_athena import AuditMeta, audit_query, get_meta, put_meta, run_audit_query

class AuditRepairTables(Command):
    COMMAND = 'audit repair'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(AuditRepairTables, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)
        self.auto_repaired = False

    def command(self):
        return AuditRepairTables.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)

        tables = Config().get('audit.athena.repair-partition-tables', 'audit').split(',')
        if args:
            tables = args

        meta = get_meta()
        self.repair(tables, meta)

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.L:
            if not self.auto_repaired:
                if hours := Config().get('audit.athena.auto-repair.elapsed_hours', 12):
                    with concurrent.futures.ThreadPoolExecutor(max_workers=Config().get('audit.workers', 3)) as executor:
                        executor.submit(self.auto_repair, hours,)

            return super().completion(state)

        return {}

    def auto_repair(self, hours: int):
        self.auto_repaired = True

        meta = get_meta()
        if meta.checked_in + hours * 60 * 60 < time.time():
            tables = Config().get('audit.athena.repair-partition-tables', 'audit').split(',')
            self.repair(tables, meta, show_sql=True)
            log2(f'Audit tables have been auto-repaired.')

    def repair(self, tables: list[str], meta: AuditMeta, show_sql = False):
        with concurrent.futures.ThreadPoolExecutor(max_workers=Config().get('audit.workers', 3)) as executor:
            for table in tables:
                if show_sql:
                    log(f'MSCK REPAIR TABLE {table}')

                executor.submit(run_audit_query, f'MSCK REPAIR TABLE {table}', None,)
            executor.submit(put_meta, 'check-in', meta,)

    def help(self, _: ReplState):
        return f"{AuditRepairTables.COMMAND} \t run MSCK REPAIR command for new partition discovery"