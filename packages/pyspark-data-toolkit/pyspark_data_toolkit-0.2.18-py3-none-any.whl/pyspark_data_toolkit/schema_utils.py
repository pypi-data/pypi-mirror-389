from typing import List, Dict, Optional, Any
import re
import logging
from pyspark.sql import DataFrame, functions as F
from logging_metrics import configure_basic_logging
from pyspark.sql.types import IntegerType, DoubleType, StringType, BooleanType
from pyspark.sql import DataFrame, SparkSession

__all__ = [
    "apply_schema",
    "cast_columns_types_by_schema",
    "validate_dataframe_schema",
    "cast_column_to_table_schema",
    "cast_multiple_columns_to_table_schema",
    "align_dataframe_to_table_schema",
    "get_table_schema_info"
]

def get_logger() -> logging.Logger:
    """Initializes and returns a basic logger for file output.

    Returns:
        logging.Logger: A configured logger with file rotation.
    """
    return configure_basic_logging()


def apply_schema(df: DataFrame, schema: Dict[str, Any], log: Optional[logging.Logger] = None) -> DataFrame:
    """Applies a schema by selecting and casting columns.

    This function:
      1. Selects only columns defined in `schema["columns"]`.
      2. Casts column types as defined in schema.

    Args:
        df (DataFrame): Input Spark DataFrame.
        schema (Dict[str, Any]): Dictionary with "columns" key containing a list of:
            - "column_name": Name of the column.
            - "data_type": Target type (string, int, date, etc.).

    Returns:
        DataFrame: DataFrame with selected and casted columns.
    """
    logger = log or get_logger()
    logger.info("Applying schema to DataFrame.")

    columns = [col["column_name"] for col in schema["columns"]]
    df = df.select(*columns)

    return cast_columns_types_by_schema(
        df,
        schema_list=schema["columns"],
        empty_to_null=True,
        logger=logger
    )


def cast_columns_types_by_schema(
    df: DataFrame, 
    schema_list: List[Dict[str, str]], 
    empty_to_null: bool = False, 
    truncate_strings: bool = False, 
    max_string_length: int = 16382,
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Converte colunas para os tipos especificados no schema.
    
    Args:
        df: DataFrame de entrada
        schema_list: Lista de dicionários com 'column_name' e 'data_type'
        empty_to_null: Converter strings vazias para null
        truncate_strings: Truncar strings longas
        max_string_length: Tamanho máximo para strings
        logger: Logger opcional
        
    Returns:
        DataFrame com colunas convertidas
    """
    if logger is None:
        logger = get_logger()
        
    if df is None or not schema_list:
        raise ValueError("DataFrame e schema não podem ser nulos ou vazios")
    
    result_df = df
    
    for column in schema_list:
        column_name = column['column_name']
        data_type = column['data_type'].lower()
        
        # Verifica se a coluna existe no DataFrame
        if column_name not in result_df.columns:
            logger.warning(f"Coluna {column_name} não encontrada no DataFrame. Pulando.")
            continue
            
        logger.debug(f"Convertendo coluna {column_name} para tipo {data_type}")
        
        try:
            # Integer
            if re.match(r'int(eger)?(?!.*big)', data_type):
                result_df = result_df.withColumn(column_name, F.col(column_name).cast(IntegerType()))
                
            # Boolean
            elif 'bool' in data_type or 'boolean' in data_type:
                result_df = result_df.withColumn(column_name, F.col(column_name).cast(BooleanType()))
                
            # Numeric/Float types
            elif any(t in data_type for t in ['numeric', 'decimal', 'double', 'float', 'real', 'money', 'currency']):
                result_df = result_df.withColumn(column_name, F.col(column_name).cast(DoubleType()))
                
            # Date
            elif data_type == 'date':
                result_df = result_df.withColumn(column_name, F.to_date(F.col(column_name)))
                
            # Timestamp/Datetime
            elif data_type == 'datetime' or 'timestamp' in data_type:
                # Tenta vários formatos comuns
                result_df = result_df.withColumn(
                    column_name, 
                    F.coalesce(
                        F.to_timestamp(F.col(column_name), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
                        F.to_timestamp(F.col(column_name), "yyyy-MM-dd HH:mm:ss.SSS"),
                        F.to_timestamp(F.col(column_name), "yyyy-MM-dd HH:mm:ss"),
                        F.to_timestamp(F.col(column_name))
                    )
                )
                
            # Complex types - skip
            elif data_type in ['struct', 'array', 'map']:
                logger.debug(f"Tipo complexo {data_type} para coluna {column_name}: mantendo como está")
                continue
                
            # String (default)
            else:
                result_df = result_df.withColumn(column_name, F.trim(F.col(column_name).cast(StringType())))
                
                # Limpa caracteres problemáticos
                result_df = result_df.withColumn(
                    column_name, 
                    F.regexp_replace(F.col(column_name), "[\\r\\n\\t]", ' ')
                )
                
            # Trunca strings longas se solicitado
            if truncate_strings:
                result_df = result_df.withColumn(
                column_name, 
                F.substring(F.col(column_name), 1, max_string_length)
            )
                    
            # Converte strings vazias para null
            if empty_to_null:
                result_df = result_df.withColumn(
                column_name, 
                F.when(F.trim(F.col(column_name)) == "", None).otherwise(F.col(column_name))
            )
        
        except Exception as e:
            logger.error(f"Erro ao converter coluna {column_name}: {str(e)}")
            # Continua com outras colunas em caso de erro
    
    return result_df


def validate_dataframe_schema(df: DataFrame, schema: Dict[str, Any]) -> bool:
    """Validates that all columns defined in the schema exist in the DataFrame.

    Args:
        df (DataFrame): Input Spark DataFrame.
        schema (Dict[str, Any]): Dictionary with "columns" key and list of:
            - "column_name": Column to validate.

    Returns:
        bool: True if all schema columns exist in DataFrame, False otherwise.
    """
    expected_cols = {col["column_name"] for col in schema.get("columns", [])}
    actual_cols = set(df.columns)
    return expected_cols.issubset(actual_cols)

# spark_utils/schema_utils.py ou my_library/spark/schema.py

def cast_column_to_table_schema(
    df: DataFrame, 
    target_table: str, 
    column_name: str,
    spark: Optional[SparkSession] = None,
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Converte uma coluna para o tipo de dados definido no schema de uma tabela existente.
    
    Útil para compatibilizar schemas antes de operações como MERGE ou INSERT,
    especialmente quando há incompatibilidades de tipo entre DataFrames.
    
    Args:
        df: DataFrame de origem
        target_table: Nome da tabela de destino (formato: database.table ou table)
        column_name: Nome da coluna a ser convertida
        spark: SparkSession (opcional, tenta obter da sessão ativa se não fornecido)
        
    Returns:
        DataFrame com a coluna convertida para o tipo correto
        
    Raises:
        ValueError: Se a coluna não existir na tabela de destino
        RuntimeError: Se não conseguir acessar a tabela ou obter o SparkSession
        
    Examples:
        >>> # Converte coluna 'status' para o tipo definido na tabela 'users'
        >>> df_fixed = cast_column_to_table_schema(df, "users", "status")
        >>> 
        >>> # Com SparkSession explícito
        >>> df_fixed = cast_column_to_table_schema(df, "db.users", "created_at", spark)
    """
    if logger is None:
        logger = get_logger()

    if spark is None:
        try:
            spark = SparkSession.getActiveSession()
            if spark is None:
                raise RuntimeError("Não foi possível obter SparkSession ativa")
        except Exception as e:
            raise RuntimeError(f"Erro ao obter SparkSession: {e}")
    
    try:
        # Obtém o schema da tabela de destino
        target_schema = spark.table(target_table).schema
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar tabela '{target_table}': {e}")
    
    # Encontra o tipo da coluna no schema de destino
    target_column_type = None
    for field in target_schema.fields:
        if field.name == column_name:
            target_column_type = field.dataType
            break
    
    if target_column_type is None:
        available_columns = [field.name for field in target_schema.fields]
        raise ValueError(
            f"Coluna '{column_name}' não encontrada na tabela '{target_table}'. "
            f"Colunas disponíveis: {available_columns}"
        )
    
    logger.info(f"Convertendo coluna '{column_name}' para tipo {target_column_type}")
    
    # Aplica o cast correto
    return df.withColumn(column_name, F.lit(None).cast(target_column_type))

def cast_multiple_columns_to_table_schema(
    df: DataFrame,
    target_table: str,
    column_names: List[str],
    spark: Optional[SparkSession] = None
) -> DataFrame:
    """
    Converte múltiplas colunas para os tipos definidos no schema de uma tabela.
    
    Args:
        df: DataFrame de origem
        target_table: Nome da tabela de destino
        column_names: Lista de nomes das colunas a serem convertidas
        spark: SparkSession (opcional)
        
    Returns:
        DataFrame com as colunas convertidas
        
    Examples:
        >>> columns_to_fix = ["status", "created_at", "user_id"]
        >>> df_fixed = cast_multiple_columns_to_table_schema(df, "users", columns_to_fix)
    """
    result_df = df
    for column_name in column_names:
        result_df = cast_column_to_table_schema(result_df, target_table, column_name, spark)
    return result_df

def get_table_schema_info(
    table_name: str,
    spark: Optional[SparkSession] = None
) -> Dict[str, str]:
    """
    Obtém informações do schema de uma tabela.
    
    Args:
        table_name: Nome da tabela
        spark: SparkSession (opcional)
        
    Returns:
        Dicionário com {column_name: data_type}
        
    Examples:
        >>> schema_info = get_table_schema_info("users")
        >>> print(schema_info)
        {'id': 'bigint', 'name': 'string', 'created_at': 'timestamp'}
    """
    if spark is None:
        spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("Não foi possível obter SparkSession ativa")
    
    try:
        schema = spark.table(table_name).schema
        return {field.name: str(field.dataType) for field in schema.fields}
    except Exception as e:
        raise RuntimeError(f"Erro ao obter schema da tabela '{table_name}': {e}")
    

def align_dataframe_to_table_schema(
    df: DataFrame,
    target_table: str,
    cast_existing: bool = True,
    add_missing: bool = True,
    spark: Optional[SparkSession] = None,
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Alinha completamente um DataFrame ao schema de uma tabela existente.
    
    Args:
        df: DataFrame de origem
        target_table: Nome da tabela de destino
        cast_existing: Se True, converte colunas existentes para os tipos corretos
        add_missing: Se True, adiciona colunas ausentes como NULL
        spark: SparkSession (opcional)
        
    Returns:
        DataFrame alinhado ao schema da tabela
        
    Examples:
        >>> # Alinhamento completo
        >>> df_aligned = align_dataframe_to_table_schema(df, "users")
        >>> 
        >>> # Só adicionar colunas ausentes, sem cast
        >>> df_aligned = align_dataframe_to_table_schema(
        ...     df, "users", cast_existing=False, add_missing=True
        ... )
    """
    if logger is None:
        logger = get_logger()

    if spark is None:
        spark = SparkSession.getActiveSession()
        if spark is None:
            raise RuntimeError("Não foi possível obter SparkSession ativa")
    
    try:
        target_schema = spark.table(target_table).schema
    except Exception as e:
        raise RuntimeError(f"Erro ao acessar tabela '{target_table}': {e}")
    
    result_df = df
    current_columns = set(df.columns)
    target_columns = {field.name: field.dataType for field in target_schema.fields}
    
    # Adiciona colunas ausentes
    if add_missing:
        missing_columns = set(target_columns.keys()) - current_columns
        for col_name in missing_columns:
            col_type = target_columns[col_name]
            default_value = _get_default_value_for_type(col_type)
            result_df = result_df.withColumn(col_name, F.lit(default_value).cast(col_type))
            logger.info(f"Adicionada coluna ausente '{col_name}' como {col_type}")
    
    # Converte tipos das colunas existentes
    if cast_existing:
        existing_columns = current_columns.intersection(target_columns.keys())
        for col_name in existing_columns:
            target_type = target_columns[col_name]
            current_type = dict(result_df.dtypes)[col_name]
            
            if str(target_type) != current_type:
                try:
                    # Verifica se é conversão de array<struct>
                    if _is_array_struct_conversion(current_type, target_type):
                        result_df = _convert_array_struct_column(
                            result_df, col_name, target_type, logger
                        )
                    else:
                        # Se for struct simples, faz conversão customizada
                        from pyspark.sql.types import StructType
                        if isinstance(df.schema[col_name].dataType, StructType) and isinstance(target_type, StructType):
                            result_df = _convert_struct_column(result_df, col_name, target_type, logger)
                        else:
                            result_df = result_df.withColumn(col_name, F.col(col_name).cast(target_type))
                        logger.info(f"Convertida coluna '{col_name}' de {current_type} para {target_type}")
                        
                except Exception as cast_error:
                    logger.error(f"Erro ao converter coluna '{col_name}': {cast_error}")
                    raise
    
    # Reordena colunas para corresponder ao schema da tabela
    target_column_order = [field.name for field in target_schema.fields if field.name in result_df.columns]
    result_df = result_df.select(*target_column_order)
    
    return result_df


def _is_array_struct_conversion(current_type: str, target_type) -> bool:
    """Verifica se é uma conversão de array<struct> para array<struct>"""
    return (
        "array<struct<" in current_type.lower() and 
        str(target_type).startswith("ArrayType(StructType")
    )


def _convert_array_struct_column(
    df: DataFrame, 
    col_name: str, 
    target_type, 
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Converte coluna array<struct> alinhando schemas de forma inteligente.
    """
    from pyspark.sql.types import ArrayType, StructType
    
    if not isinstance(target_type, ArrayType) or not isinstance(target_type.elementType, StructType):
        raise ValueError(f"Tipo de destino deve ser ArrayType(StructType), recebido: {target_type}")
    
    # Obter schemas atual e de destino
    current_struct = df.schema[col_name].dataType.elementType
    target_struct = target_type.elementType
    
    current_fields = {field.name: field for field in current_struct.fields}
    target_fields = {field.name: field for field in target_struct.fields}
    
    # Estratégias diferentes baseadas na situação
    if _should_evolve_schema(current_fields, target_fields):
        # Caso 1: Schema evolution - adicionar campos novos
        return _evolve_array_struct_schema(df, col_name, current_fields, target_fields, logger)
    else:
        # Caso 2: Remover campos extras ou reorganizar
        return _trim_array_struct_schema(df, col_name, target_fields, logger)

def _should_evolve_schema(current_fields: dict, target_fields: dict) -> bool:
    """
    Decide se deve fazer schema evolution ou trimming.
    Evolve quando o target tem mais campos que o current.
    """
    current_field_names = set(current_fields.keys())
    target_field_names = set(target_fields.keys())
    
    # Se target tem mais campos, é evolução
    return len(target_field_names - current_field_names) > 0


def _evolve_array_struct_schema(
    df: DataFrame, 
    col_name: str, 
    current_fields: dict, 
    target_fields: dict, 
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Evolui o schema adicionando campos ausentes com valores padrão apropriados.
    """
    from pyspark.sql.functions import col, transform, struct, lit
    
    # Criar expressão de transformação usando SQL string (mais confiável)
    df_temp = df
    df_temp.createOrReplaceTempView(f"temp_table_{col_name}")
    
    # Construir lista de campos para o struct
    struct_fields = []
    for field_name, field in target_fields.items():
        if field_name in current_fields:
            # Campo existe - manter valor original
            struct_fields.append(f"x.{field_name}")
        else:
            # Campo novo - usar valor padrão baseado no tipo
            default_value = _get_sql_default_value_for_type(field.dataType)
            struct_fields.append(f"{default_value} as {field_name}")
    
    struct_expr = ", ".join(struct_fields)
    
    # Usar SQL para fazer a transformação
    sql_query = f"""
        SELECT *,
               TRANSFORM({col_name}, x -> STRUCT({struct_expr})) as {col_name}_new
        FROM temp_table_{col_name}
    """
    
    result_df = df.sparkSession.sql(sql_query)
    result_df = result_df.drop(col_name).withColumnRenamed(f"{col_name}_new", col_name)
    
    if logger:
        added_fields = set(target_fields.keys()) - set(current_fields.keys())
        logger.info(f"Schema evolution em '{col_name}': adicionados campos {added_fields}")
    
    return result_df


def _trim_array_struct_schema(
    df: DataFrame, 
    col_name: str, 
    target_fields: dict, 
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Remove campos extras, mantendo apenas os do schema de destino.
    """
    # Usar SQL para fazer a transformação
    df_temp = df
    df_temp.createOrReplaceTempView(f"temp_trim_{col_name}")
    
    # Construir lista de campos para manter
    field_list = ", ".join([f"x.{field_name}" for field_name in target_fields.keys()])
    
    sql_query = f"""
        SELECT *,
               TRANSFORM({col_name}, x -> STRUCT({field_list})) as {col_name}_new
        FROM temp_trim_{col_name}
    """
    
    result_df = df.sparkSession.sql(sql_query)
    result_df = result_df.drop(col_name).withColumnRenamed(f"{col_name}_new", col_name)
    
    if logger:
        logger.info(f"Schema trimming em '{col_name}': mantidos apenas campos {list(target_fields.keys())}")
    
    return result_df


def _get_default_value_for_type(data_type):
    """
    Retorna valores padrão apropriados por tipo, evitando NULL quando possível.
    """
    from pyspark.sql.types import StringType, IntegerType, LongType, DoubleType, BooleanType, ArrayType
    
    if isinstance(data_type, StringType):
        return ""  # String vazia em vez de NULL
    elif isinstance(data_type, (IntegerType, LongType)):
        return 0
    elif isinstance(data_type, DoubleType):
        return 0.0
    elif isinstance(data_type, BooleanType):
        return False
    elif isinstance(data_type, ArrayType):
        return []  # Array vazio
    else:
        return None  # Só usa NULL quando não há alternativa
    
def _get_sql_default_value_for_type(data_type):
    """
    Retorna valores padrão como strings SQL.
    """
    from pyspark.sql.types import StringType, IntegerType, LongType, DoubleType, BooleanType, ArrayType
    
    if isinstance(data_type, StringType):
        return "''"  # String vazia
    elif isinstance(data_type, (IntegerType, LongType)):
        return "0"
    elif isinstance(data_type, DoubleType):
        return "0.0"
    elif isinstance(data_type, BooleanType):
        return "false"
    elif isinstance(data_type, ArrayType):
        return "array()"  # Array vazio
    else:
        return "null"  # Só usa NULL quando não há alternativa
    
def _convert_struct_column(
    df: DataFrame, 
    col_name: str, 
    target_type, 
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Converte uma coluna do tipo struct alinhando campos ausentes.
    Versão corrigida usando apenas operações PySpark (sem SQL temporário).
    """
    from pyspark.sql.functions import col, struct, lit
    from pyspark.sql.types import StructType, StructField
    import pyspark.sql.functions as F
    
    # Se coluna não existe, cria como struct vazia
    if col_name not in df.columns:
        if logger:
            logger.warning(f"Coluna {col_name} não existe, criando como struct nula.")
        return df.withColumn(col_name, F.lit(None).cast(target_type))
    
    current_field = df.schema[col_name]
    if not isinstance(current_field.dataType, StructType):
        # Se o campo existe mas não é struct, converte
        return df.withColumn(col_name, F.col(col_name).cast(target_type))

    # ✅ Construir struct alinhado com todos os campos do target
    struct_fields = []
    
    for field in target_type.fields:
        field_name = field.name
        target_field_type = field.dataType
        
        # Verificar se o campo existe na estrutura atual
        if field_name in current_field.dataType.fieldNames():
            current_nested_type = next(
                f.dataType for f in current_field.dataType.fields 
                if f.name == field_name
            )
            
            # Se é struct aninhado, converter recursivamente
            if isinstance(target_field_type, StructType) and isinstance(current_nested_type, StructType):
                nested_value = col(f"{col_name}.{field_name}")
                struct_fields.append(
                    _build_aligned_struct(nested_value, target_field_type, logger).alias(field_name)
                )
            else:
                # Converter tipo simples
                struct_fields.append(
                    col(f"{col_name}.{field_name}").cast(target_field_type).alias(field_name)
                )
        else:
            # Campo ausente - criar com valor padrão
            if logger:
                logger.warning(f"Campo ausente em {col_name}: {field_name}, preenchendo com nulo.")
            struct_fields.append(lit(None).cast(target_field_type).alias(field_name))
    
    # Reconstruir o struct com todos os campos
    result_df = df.withColumn(col_name, struct(*struct_fields))
    
    return result_df


def _build_aligned_struct(col_expr, target_type, logger=None):
    """
    Helper para construir um struct alinhado a partir de uma expressão de coluna.
    Usa getField() - mais robusto que indexação.
    """
    from pyspark.sql.functions import col, lit, coalesce
    from pyspark.sql.types import StructType
    import pyspark.sql.functions as F
    
    if not isinstance(target_type, StructType):
        return col_expr.cast(target_type)
    
    struct_fields = []
    
    for field in target_type.fields:
        field_name = field.name
        target_field_type = field.dataType
        
        # Usar getField() - mais robusto
        field_value = col_expr.getField(field_name)
        
        # Se o campo pode ser nulo, usar coalesce com valor padrão
        default_val = lit(None).cast(target_field_type)
        field_value = coalesce(field_value, default_val)
        
        # Se é struct aninhado, recursar
        if isinstance(target_field_type, StructType):
            struct_fields.append(
                _build_aligned_struct(field_value, target_field_type, logger).alias(field_name)
            )
        else:
            struct_fields.append(field_value.cast(target_field_type).alias(field_name))
    
    return F.struct(*struct_fields)
    

