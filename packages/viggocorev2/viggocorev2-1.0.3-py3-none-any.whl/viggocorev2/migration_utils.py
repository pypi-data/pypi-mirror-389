# Função para encontrar modelos do esquema público
def get_public_models(target_db, logger):
    """
    Encontra todos os modelos SQLAlchemy que pertencem ao esquema 'public'
    """
    models = []
    # logger.info("Procurando modelos do esquema 'public'...")

    # Obtém todas as classes mapeadas pelo SQLAlchemy
    all_models = []

    # Abordagem 1: Usar o registry do SQLAlchemy 2.0
    for mapper in target_db.Model.registry.mappers:
        all_models.append(mapper.class_)

    # Filtra apenas os modelos do esquema público
    for model in all_models:
        # Verifica se o modelo tem uma tabela definida
        if hasattr(model, '__table__') and model.__table__ is not None:
            # Verifica se o esquema é 'public' ou None (que usa o
            # default 'public')
            schema = getattr(model.__table__, 'schema', None)
            if schema == 'public':
                # logger.info(f"Adicionando modelo público: {model.__name__}")
                models.append(model)

    # logger.info(f"Total de modelos públicos encontrados: {len(models)}")
    return models


def get_dynamic_schema_models(target_db, target_schema="default_schema"):
    """
    Encontra todos os modelos SQLAlchemy que pertencem ao esquema especificado
    """
    models = []
    
    # Obtém todas as classes mapeadas pelo SQLAlchemy
    for mapper in target_db.Model.registry.mappers:
        model_class = mapper.class_
        
        # ✅ Verifica se o modelo tem tabela
        if not hasattr(model_class, '__table__') or model_class.__table__ is None:
            continue

        table = model_class.__table__
        table_schema = getattr(table, 'schema', None)
        
        # # ✅ Filtrar apenas modelos do schema especificado
        # if table_schema == target_schema:
        #     models.append(model_class)
        # elif table_schema is None and target_schema == "default_schema":
        #     # ✅ Modelos sem schema definido podem ser considerados do schema padrão
        #     models.append(model_class)
        
        models.append(model_class)
    return models
