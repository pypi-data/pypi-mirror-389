from flask_migrate import upgrade
import os
from sqlalchemy import text
from viggocorev2 import database
import flask
# from viggocorev2 import database
# from flask import current_app


# def make_schema(nome_esquema):
#     """Cria um esquema no banco de dados se ele não existir"""
#     with current_app.app_context():
#         database.db.session.execute(database.db.text(
#             f'CREATE SCHEMA IF NOT EXISTS "{nome_esquema}"'))
#         database.db.session.commit()


def create_tenant_and_migrate(tenant_id):
    """
    ✅ CORRIGIDO: Versão mais robusta com contexto e cleanup
    """

    # ✅ GARANTIR contexto Flask
    if not flask.has_app_context():
        # print("❌ Sem contexto Flask! Execute dentro de app.app_context()")
        raise RuntimeError("Contexto Flask necessário")

    try:
        # ✅ 3. CONFIGURAR para migrar apenas este tenant
        os.environ['MIGRATION_TARGET_SCHEMA'] = tenant_id

        try:
            # ✅ 4. EXECUTAR MIGRAÇÕES com timeout
            # print(f"🔄 Executando migrações para {tenant_id}...")

            # ✅ Executar upgrade
            upgrade(directory='migrations/tenant')
            # print(f"✅ Migrações concluídas para {tenant_id}")
        finally:
            # ✅ RESTAURAR ambiente
            if 'MIGRATION_TARGET_SCHEMA' in os.environ:
                del os.environ['MIGRATION_TARGET_SCHEMA']

        # # ✅ 5. VERIFICAR resultado final
        # with database.db.engine.connect() as conn:
        #     table_count = conn.execute(text(f"""
        #         SELECT COUNT(*) FROM information_schema.tables
        #         WHERE table_schema = '{tenant_id}'
        #         AND table_type = 'BASE TABLE'
        #     """)).scalar()

        #     print(f"📊 {table_count} tabelas criadas no schema {tenant_id}")

        #     if table_count == 0:
        #         conn.execute(text('RESET search_path;'))
        #         conn.close()
        #         raise Exception(
        #             f"Nenhuma tabela foi criada no schema {tenant_id}")
        #     conn.execute(text('RESET search_path;'))
        #     conn.close()

        return True

    except Exception as e:
        # print(f"❌ Erro ao criar tenant {tenant_id}: {e}")
        import traceback
        traceback.print_exc()
        raise
