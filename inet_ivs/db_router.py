class ExternalDatabaseRouter:
    """Keep Django migrations away from external databases."""

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db in {'ivs_sat', 'sqlserver'}:
            return False
        return None
