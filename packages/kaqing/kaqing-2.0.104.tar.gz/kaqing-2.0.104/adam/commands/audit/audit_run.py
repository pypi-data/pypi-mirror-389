from adam.commands.command import Command
from adam.config import Config
from adam.repl_state import ReplState
from adam.utils import log2
from adam.utils_athena import AuditMeta, find_new_clusters, get_meta, put_meta, run_audit_query

class AuditRun(Command):
    COMMAND = 'audit run'

    # the singleton pattern
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'): cls.instance = super(AuditRun, cls).__new__(cls)

        return cls.instance

    def __init__(self, successor: Command=None):
        super().__init__(successor)
        self.auto_repaired = False

    def command(self):
        return AuditRun.COMMAND

    def run(self, cmd: str, state: ReplState):
        if not(args := self.args(cmd)):
            return super().run(cmd, state)

        state, args = self.apply_state(args, state)

        meta: AuditMeta = get_meta()
        clusters = find_new_clusters(meta.cluster_last_checked)
        if clusters:
            put_meta('add-clusters', meta, clusters=clusters)
            log2(f'Added {len(clusters)} new clusters.')
            tables = Config().get('audit.athena.repair-cluster-tables', 'cluster').split(',')
            for table in tables:
                run_audit_query(f'MSCK REPAIR TABLE {table}')
        else:
            log2(f'No new clusters were found.')

        return state

    def completion(self, state: ReplState):
        if state.device == ReplState.L:
            return super().completion(state)

        return {}

    def help(self, _: ReplState):
        return f"{AuditRun.COMMAND} \t run"