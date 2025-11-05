from typing import Dict, List, Tuple

from sqlalchemy import and_

from viggocorev2.common import utils
from viggocorev2.common.subsystem import operation
from viggocorev2.common.subsystem.transaction_manager import TransactionManager

# Modelos utilizados (assumindo já existentes no projeto)
from viggocorev2.subsystem.role.resource import Role
from viggocorev2.subsystem.capability_functionality.resource import (
    CapabilityFunctionality)
from viggocorev2.subsystem.policy_functionality.resource import (
    PolicyFunctionality)
from viggocorev2.subsystem.policy_functionality_public.resource import (
    PolicyFunctionalityPublic)


class ReplicatePolicies(operation.Operation):

    def _list_tenants(self, session,
                      include: List[str],
                      exclude: List[str]) -> List[Tuple[str, str]]:
        """
        Lista schemas de tenants a partir do schema public (tabela de domínios),
        retornando uma lista de nomes de schemas (por padrão, domain.id).
        """
        tm = TransactionManager()
        tm.set_schema('public')
        try:
            # Import local para evitar dependência cíclica em import global
            from viggocorev2.subsystem.domain.resource import (Domain)

            query = session.query(Domain.id, Domain.application_id)\
                .filter(Domain.name != 'default')
            schemas = [row for row in query.all()]

            # include/exclude
            if include:
                allow = set(include)
                schemas = [s for s in schemas if s[0] in allow]
            if exclude:
                deny = set(exclude)
                schemas = [s for s in schemas if s[0] not in deny]

            return schemas
        finally:
            tm.reset_schema()

    def _collect_source_policies(self, session) -> List[
            Dict[str, Tuple[str, str]]]:
        """
        Coleta o conjunto de policies no default_schema como tuplas
        (role_name, route_url, route_method). Não retorna IDs.
        """
        tm = TransactionManager()
        tm.set_schema('default_schema')
        try:
            # Seleciona chaves naturais para replicar
            # (role.name, route.url, route.method)
            query = (
                session.query(Role.name,
                              CapabilityFunctionality.id,
                              CapabilityFunctionality.application_id)
                .join(PolicyFunctionalityPublic,
                      PolicyFunctionalityPublic.role_id == Role.id)
                .join(CapabilityFunctionality,
                      CapabilityFunctionality.id ==
                      PolicyFunctionalityPublic.capability_functionality_id)
                .distinct()
            )
            if self.application_id is not None:
                query = query.filter(
                    CapabilityFunctionality.application_id ==
                    self.application_id)
            rows = query.all()
            """
            Agrupa os roles e capability_functionality por aplicação
            """
            response = {}
            for r in rows:
                if r[2] in response.keys():
                    response[r[2]].append((r[0], r[1]))
                else:
                    response[r[2]] = [(r[0], r[1])]

            """
            O retorno é:
            {
                'application_id': [
                    (
                        role.name,
                        capability_functionality.id,
                        capability_functionality.application_id
                    )
                ]
            }
            """  # noqa
            return response
        finally:
            tm.reset_schema()

    def _insert_missing_policies_for_tenant(
        self,
        session,
        tenant_schema: str,
        source_policies: List[Tuple[str, str]]
    ) -> Dict[str, int]:
        created = 0
        skipped = 0

        tm = TransactionManager()
        tm.set_schema(tenant_schema)
        try:
            # role_name,
            # cf = capability_functionality_id
            # o terceiro campo era o applicantion_id que já foi filtrado
            for role_name, cf_id in source_policies:
                # Resolver role
                role = (session.query(Role).filter(Role.name == role_name).first())
                if not role:
                    skipped += 1
                    continue

                # Verificar se PolicyFunctionality já existe
                exists = (
                    session.query(PolicyFunctionality)
                    .filter(and_(
                        PolicyFunctionality.role_id == role.id,
                        PolicyFunctionality.capability_functionality_id ==
                        cf_id))
                    .first())
                if exists:
                    skipped += 1
                    continue

                # Criar Policy ausente
                if not self.dry_run:
                    policy = PolicyFunctionality(
                        id=utils.random_uuid(),
                        role_id=role.id,
                        capability_functionality_id=cf_id)
                    session.add(policy)
                created += 1

            if not self.dry_run:
                session.commit()
            return {"created": created, "skipped": skipped}
        except Exception:
            session.rollback()
            raise
        finally:
            tm.reset_schema()

    def pre(self, session, **kwargs) -> bool:
        # Parâmetros opcionais
        self.application_id: str = kwargs.get('application_id', None)
        self.include: List[str] = kwargs.get('tenants_include', [])
        self.exclude: List[str] = kwargs.get('tenants_exclude', [])
        self.dry_run: bool = bool(kwargs.get('dry_run', False))
        self.abort_on_error: bool = bool(kwargs.get('abort_on_error', False))
        return True

    def do(self, session, **kwargs):
        # 1) Listar tenants a partir do public
        tenants = self._list_tenants(session, self.include, self.exclude)

        # 2) Coletar policies do default_schema
        source_policies = self._collect_source_policies(session)

        # 3) Replicar somente policies ausentes
        tenants_success = 0
        tenants_failed = 0
        created_total = 0
        skipped_total = 0
        tenants_report = []

        for schema in tenants:
            try:
                # schema[0] = domain_id
                # schema[1] = application_id
                result = self._insert_missing_policies_for_tenant(
                    session, schema[0],
                    source_policies.get(schema[1], []))
                tenants_success += 1
                created_total += result["created"]
                skipped_total += result["skipped"]
                tenants_report.append({
                    "schema": schema,
                    "created": result["created"],
                    "skipped": result["skipped"]
                })
            except Exception as e:
                tenants_failed += 1
                tenants_report.append({
                    "schema": schema,
                    "error": str(e)
                })
                if self.abort_on_error:
                    break

        return {
            "source_schema": "default_schema",
            "dry_run": self.dry_run,
            "tenants_total": len(tenants),
            "tenants_success": tenants_success,
            "tenants_failed": tenants_failed,
            "created_total": created_total,
            "skipped_total": skipped_total,
            "tenants": tenants_report
        }
