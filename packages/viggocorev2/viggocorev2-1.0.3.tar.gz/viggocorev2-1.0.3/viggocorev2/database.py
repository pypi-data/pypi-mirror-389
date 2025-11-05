# import flask_sqlalchemy
# db = flask_sqlalchemy.SQLAlchemy()
import flask_migrate

from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy

"""Database related functions"""


class SQLAlchemy(_BaseSQLAlchemy):
    """
    ✅ CORRIGIDO (2025-10-28): Configurações Explícitas de Pool
    
    Pool de conexões configurado com valores explícitos e otimizados
    para ambiente multi-tenant em produção.
    """
    
    def apply_pool_defaults(self, app, options):
        import os
        
        options = super().apply_pool_defaults(app, options)
        
        # ✅ Pool pre-ping: Verifica se conexão está viva antes de usar
        # Evita "MySQL server has gone away" e similares
        options["pool_pre_ping"] = True
        
        # ✅ Pool size: Número de conexões mantidas abertas permanentemente
        # Padrão: 10 (aumentar para 20-30 em produção com alto tráfego)
        # Configurável via variável de ambiente
        options["pool_size"] = int(os.getenv('DB_POOL_SIZE', 10))
        
        # ✅ Max overflow: Conexões extras temporárias além do pool_size
        # Padrão: 20 (2x o pool_size)
        # Total máximo de conexões = pool_size + max_overflow
        options["max_overflow"] = int(os.getenv('DB_POOL_MAX_OVERFLOW', 20))
        
        # ✅ Pool recycle: Tempo (s) antes de reciclar conexão
        # Padrão: 3600 (1 hora) - Evita conexões antigas/stale
        # MySQL: Deve ser < wait_timeout (padrão: 28800s)
        options["pool_recycle"] = int(
            os.getenv('DB_POOL_RECYCLE', 3600)
        )
        
        # ✅ Pool timeout: Tempo máx (s) para aguardar conexão
        # Padrão: 30s - Aguarda se pool estiver cheio
        options["pool_timeout"] = int(
            os.getenv('DB_POOL_TIMEOUT', 30)
        )
        
        # ✅ Echo pool: Log checkout/checkin (debug only)
        if app.debug:
            options["echo_pool"] = True
        
        return options


db = SQLAlchemy()
migrate = flask_migrate.Migrate()
