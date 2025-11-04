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
    
    # Coleta tipos atuais ANTES de qualquer modificação (evita erros em dtypes)
    original_dtypes = dict(df.dtypes)  # Usa df original, não result_df
    
    # Adiciona colunas ausentes
    if add_missing:
        missing_columns = set(target_columns.keys()) - current_columns
        for col_name in missing_columns:
            col_type = target_columns[col_name]
            default_value = _get_default_value_for_type(col_type)
            result_df = result_df.withColumn(col_name, F.lit(default_value).cast(col_type))
            logger.info(f"Adicionada coluna ausente '{col_name}' como {col_type}")
    
    # Converte tipos das colunas existentes - usa original_dtypes para check
    if cast_existing:
        existing_columns = current_columns.intersection(target_columns.keys())
        for col_name in existing_columns:
            target_type = target_columns[col_name]
            current_type = original_dtypes.get(col_name, str(df.schema[col_name].dataType))  # Seguro, do original
            
            if str(target_type) != current_type:
                try:
                    # Verifica se é conversão de array<struct>
                    if _is_array_struct_conversion(current_type, target_type):
                        result_df = _convert_array_struct_column(
                            result_df, col_name, target_type, logger
                        )
                    else:
                        from pyspark.sql.types import StructType
                        if isinstance(target_type, StructType):
                            if col_name in df.columns:
                                result_df = _align_struct_fields(F.col(col_name), target_type, logger)
                            else:
                                result_df = _align_struct_fields(F.lit(None).cast(target_type), target_type, logger)
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


def _convert_array_struct_column(df, col_name, target_type, logger=None):
    """
    Converte coluna array<struct> alinhando schemas de forma inteligente.
    Corrige casos em que o schema é nested ou Spark Connect não resolve diretamente.
    """
    import pyspark.sql.functions as F

    if not isinstance(target_type, ArrayType) or not isinstance(target_type.elementType, StructType):
        raise ValueError(f"Tipo de destino deve ser ArrayType(StructType), recebido: {target_type}")

    # 🔍 Tenta obter o tipo da coluna de forma robusta
    try:
        field_type = next((f.dataType for f in df.schema.fields if f.name == col_name), None)
    except Exception:
        field_type = None

    if field_type is None:
        # fallback: tenta acessar nested
        try:
            field_type = df.select(F.col(col_name)).schema.fields[0].dataType
        except Exception:
            raise ValueError(f"Não foi possível resolver o tipo da coluna '{col_name}' no DataFrame")

    # ✅ Valida se é ArrayType
    if not isinstance(field_type, ArrayType):
        raise TypeError(f"A coluna '{col_name}' não é ArrayType, mas {type(field_type)}")

    # Agora sim, acessa o elemento interno
    current_struct = field_type.elementType
    target_struct = target_type.elementType

    if not isinstance(current_struct, StructType):
        raise TypeError(f"Elemento interno da coluna '{col_name}' não é StructType, mas {type(current_struct)}")

    current_fields = {f.name: f for f in current_struct.fields}
    target_fields = {f.name: f for f in target_struct.fields}

    # Estratégias diferentes baseadas na situação
    if _should_evolve_schema(current_fields, target_fields):
        return _evolve_array_struct_schema(df, col_name, current_fields, target_fields, logger)
    else:
        return _trim_array_struct_schema(df, col_name, target_fields, logger)

from pyspark.sql.types import ArrayType, StructType, DataType, StructField

def _get_nested_field_type(schema: StructType, col_path: str) -> DataType:
    """Busca o tipo de uma coluna (incluindo nested paths como 'a.b.c')."""
    parts = col_path.split(".")
    current_type = schema
    for part in parts:
        if isinstance(current_type, StructType):
            field = next((f for f in current_type.fields if f.name == part), None)
            if not field:
                raise KeyError(f"Campo '{part}' não encontrado em {current_type.simpleString()}")
            current_type = field.dataType
        elif isinstance(current_type, ArrayType) and isinstance(current_type.elementType, StructType):
            # Caso array<struct> → continua navegando dentro do struct
            current_type = current_type.elementType
        else:
            raise TypeError(f"Tipo inesperado ao navegar no caminho '{col_path}'")
    return current_type

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
    """Retorna um valor default literal compatível com o tipo Spark."""
    if isinstance(data_type, T.StringType):
        return F.lit(None).cast(T.StringType())
    if isinstance(data_type, T.BooleanType):
        return F.lit(False)
    if isinstance(data_type, (T.IntegerType, T.LongType, T.ShortType, T.DoubleType, T.FloatType, T.DecimalType)):
        return F.lit(0)
    if isinstance(data_type, T.TimestampType):
        return F.lit(None).cast(T.TimestampType())
    if isinstance(data_type, T.StructType):
        # Struct → cria struct com todos os campos default
        fields = [
            F.alias(_get_default_value_for_type(f.dataType), f.name)
            for f in data_type.fields
        ]
        return F.struct(*fields)
    if isinstance(data_type, T.ArrayType):
        return F.array()
    return F.lit(None)
    
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
    
def _convert_struct_column(df: DataFrame, col_name: str, target_type, logger=None) -> DataFrame:
    """
    Converte coluna struct genérica, com handling safe para nulls/VOID/recursão default.
    Neutra para qualquer coluna; build_default previne VOID em lit(None) sub-structs.
    """
    from pyspark.sql.types import StructType
    import pyspark.sql.functions as F
    
    if col_name not in df.columns:
        if logger:
            logger.warning(f"Coluna {col_name} não existe, criando como null safe.")
        return df.withColumn(col_name, F.lit(None).cast(target_type))
    
    current_type = df.schema[col_name].dataType
    
    # Se current não struct mas target é, cria vazio com build_default=True (safe VOID)
    if not isinstance(current_type, StructType) and isinstance(target_type, StructType):
        if logger:
            logger.info(f"{col_name} não struct no input, criando vazio alinhado ao target com defaults.")
        new_col_expr = _build_aligned_struct(F.lit(None), target_type, logger, build_default=True)
    elif isinstance(current_type, StructType) and isinstance(target_type, StructType):
        # Build normal (flag False, usa existing_val onde possível)
        new_col_expr = _build_aligned_struct(F.col(col_name), target_type, logger, build_default=False)
    else:
        # Cast simples para não-structs (ex: string para long, safe nulls)
        return df.withColumn(col_name, F.col(col_name).cast(target_type))
    
    result_df = df.withColumn(col_name, new_col_expr)
    
    if logger:
        logger.info(f"Antes - {col_name}: {df.schema[col_name].simpleString()}")
        logger.info(f"Target - {col_name}: {target_type.simpleString()}")
        logger.info(f"Após - {col_name}: {result_df.schema[col_name].simpleString()}")
        logger.info(f"Struct '{col_name}' alinhado safe para nulls/VOID/recursão")
    
    return result_df

def _build_aligned_struct(col_expr, target_type, logger=None, build_default=False):
    """
    Reconstrói struct genérico expressionalmente, com handling safe para nulls/VOID/recursão default.
    Modo build_default=True pula getField e usa só defaults (evita VOID em lit(None) sub-structs).
    Genérico para qualquer nested level/coluna; schema inferido sem extract errors.
    """
    from pyspark.sql.functions import lit, when, isnull, struct as F_struct
    from pyspark.sql.types import StructType, StringType, LongType, BooleanType
    import pyspark.sql.functions as F
    
    if not isinstance(target_type, StructType):
        # Cast simples se target primitivo (safe para nulls/VOID)
        return col_expr.cast(target_type)
    
    struct_fields = []
    
    for field in target_type.fields:
        field_name = field.name  # str garantido
        target_field_type = field.dataType
        
        if build_default:
            # Modo default: pula extração, usa só default para cada field (sem getField em VOID)
            existing_val = lit(None)  # Placeholder null, mas field_value será default
            if logger:
                logger.debug(f"Build default para {field_name}: usando defaults tipados")
        else:
            # Modo normal: extração safe com isNotNull()
            existing_val = when(col_expr.isNotNull(), col_expr.getField(field_name)).otherwise(lit(None))
            if logger:
                logger.debug(f"Extração normal {field_name} em {col_expr}: safe handling")
        
        # Default baseado no tipo (sempre tipado, lit(None) cast se necessário)
        if isinstance(target_field_type, StringType):
            default_val = lit("")
        elif isinstance(target_field_type, LongType):
            default_val = lit(0)
        elif isinstance(target_field_type, BooleanType):
            default_val = lit(False)
        elif isinstance(target_field_type, StructType):
            # Recursão para sub-struct: usa build_default=True para evitar VOID
            default_val = _build_aligned_struct(lit(None), target_field_type, logger, build_default=True)
        else:
            default_val = lit(None).cast(target_field_type)
        
        # When para escolher: existing se não null, senão default (expressional, safe para VOID)
        field_value = when(isnull(existing_val), default_val).otherwise(existing_val)
        
        if isinstance(target_field_type, StructType):
            # Se o valor é VOID ou estamos em modo default, manter build_default=True
            propagate_default = build_default or (str(field_value._jc.toString()).endswith("void()") if hasattr(field_value, "_jc") else False)
            final_field = _build_aligned_struct(
                field_value, target_field_type, logger, build_default=propagate_default
            ).alias(field_name)
        else:
            final_field = field_value.cast(target_field_type).alias(field_name)
        
        struct_fields.append(final_field)
    
    # Novo struct raiz (schema inferido full do target, sem VOID propagation)
    return F_struct(*struct_fields)

def _align_struct_fields(col_expr, target_struct, logger):
    """
    Garante que uma coluna struct tenha exatamente os mesmos campos
    e tipos do schema de destino (target_struct).
    """
    from pyspark.sql import functions as F, types as T

    aligned_fields = []

    for field in target_struct.fields:
        field_name = field.name
        field_type = field.dataType

        try:
            # Usa F.col sem acessar o JVM (_jc)
            sub_col = col_expr.getField(field_name)
            if isinstance(field_type, T.StructType):
                aligned_field = _align_struct_fields(sub_col, field_type, logger)
            else:
                aligned_field = sub_col.cast(field_type)
        except Exception:
            # Campo ausente ou struct incompleta → cria campo default compatível
            aligned_field = _get_default_value_for_type(field_type)
            logger.debug(f"Campo '{field_name}' ausente — preenchido com default ({field_type.simpleString()})")

        aligned_fields.append(aligned_field.alias(field_name))

    return F.struct(*aligned_fields)







    

