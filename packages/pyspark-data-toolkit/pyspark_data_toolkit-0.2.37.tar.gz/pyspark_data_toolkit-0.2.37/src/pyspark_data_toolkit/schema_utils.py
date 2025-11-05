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

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, ArrayType, StringType, LongType, BooleanType

def align_array_struct_column(df, col_name, target_type: ArrayType):
    """
    Alinha uma coluna array<struct> ao schema target, preenchendo campos faltantes com null.
    Funciona recursivamente para structs internos e arrays internos.
    """
    element_type = target_type.elementType
    target_fields = {f.name: f for f in element_type.fields}

    def build_struct_expr(element_col, target_fields):
        exprs = []
        for name, field in target_fields.items():
            if isinstance(field.dataType, StructType):
                # Struct interno
                inner_expr = build_struct_expr(F.col(f"{element_col}.{name}"), {f.name: f for f in field.dataType.fields})
                exprs.append(inner_expr.alias(name))
            elif isinstance(field.dataType, ArrayType) and isinstance(field.dataType.elementType, StructType):
                # Array de struct interno
                exprs.append(
                    F.transform(
                        F.col(f"{element_col}.{name}"),
                        lambda x: build_struct_expr(x, {f.name: f for f in field.dataType.elementType.fields})
                    ).alias(name)
                )
            else:
                # Campo simples
                exprs.append(
                    F.col(f"{element_col}.{name}").cast(field.dataType).alias(name)
                )
        return F.struct(*exprs)

    return df.withColumn(
        col_name,
        F.when(
            F.col(col_name).isNotNull(),
            F.transform(F.col(col_name), lambda x: build_struct_expr(x, target_fields))
        ).otherwise(F.lit(None))
    )

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, ArrayType, StringType, LongType, BooleanType

def align_array_struct_column(df, col_name, target_type: ArrayType):
    """
    Alinha uma coluna array<struct> ao schema target, preenchendo campos faltantes com null.
    Funciona recursivamente para structs internos e arrays internos.
    """
    element_type = target_type.elementType
    target_fields = {f.name: f for f in element_type.fields}

    def build_struct_expr(element_col, target_fields):
        exprs = []
        for name, field in target_fields.items():
            if isinstance(field.dataType, StructType):
                # Struct interno
                inner_expr = build_struct_expr(F.col(f"{element_col}.{name}"), {f.name: f for f in field.dataType.fields})
                exprs.append(inner_expr.alias(name))
            elif isinstance(field.dataType, ArrayType) and isinstance(field.dataType.elementType, StructType):
                # Array de struct interno
                exprs.append(
                    F.transform(
                        F.col(f"{element_col}.{name}"),
                        lambda x: build_struct_expr(x, {f.name: f for f in field.dataType.elementType.fields})
                    ).alias(name)
                )
            else:
                # Campo simples
                exprs.append(
                    F.col(f"{element_col}.{name}").cast(field.dataType).alias(name)
                )
        return F.struct(*exprs)

    return df.withColumn(
        col_name,
        F.when(
            F.col(col_name).isNotNull(),
            F.transform(F.col(col_name), lambda x: build_struct_expr(x, target_fields))
        ).otherwise(F.lit(None))
    )

def align_dataframe_to_table_schema_sample(
    df: DataFrame,
    target_schema: StructType,
    logger: Optional[logging.Logger] = None
) -> DataFrame:
    """
    Alinha qualquer DataFrame ao schema de destino.
    Preenche campos ausentes com null, alinha tipos de coluna e é recursivo para structs e arrays de structs.
    """
    
    def align_column(col_name, current_type, target_type):
        if isinstance(target_type, StructType):
            return align_struct_column(F.col(col_name), current_type, target_type)
        elif isinstance(target_type, ArrayType) and isinstance(target_type.elementType, StructType):
            return align_array_struct_column(F.col(col_name), current_type, target_type)
        else:
            return F.col(col_name).cast(target_type)

    def align_struct_column(col_expr, current_type, target_type):
        from pyspark.sql.types import StructType
        fields_expr = []
        current_fields = {f.name: f for f in current_type.fields} if isinstance(current_type, StructType) else {}
        for field in target_type.fields:
            if field.name in current_fields:
                c_type = current_fields[field.name].dataType
                f_expr = align_column(f"{col_expr}.{field.name}", c_type, field.dataType).alias(field.name)
            else:
                # Campo ausente → criar null compatível
                f_expr = F.lit(None).cast(field.dataType).alias(field.name)
            fields_expr.append(f_expr)
        return F.struct(*fields_expr)

    def align_array_struct_column(col_expr, current_type, target_type):
        element_type = target_type.elementType
        def build_element_expr(x):
            return align_struct_column(x, current_type.elementType if current_type else NullType(), element_type)
        return F.when(
            col_expr.isNotNull(),
            F.transform(col_expr, lambda x: build_element_expr(x))
        ).otherwise(F.lit(None))

    # Construir DataFrame resultante
    result_df = df
    for field in target_schema.fields:
        if field.name in df.columns:
            c_type = df.schema[field.name].dataType
            result_df = result_df.withColumn(field.name, align_column(field.name, c_type, field.dataType))
        else:
            # Coluna ausente → criar null
            result_df = result_df.withColumn(field.name, F.lit(None).cast(field.dataType))
    return result_df

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
    current_columns_list = list(result_df.columns)  # Garantir lista de strings
    current_columns = set(current_columns_list)
    target_columns = {field.name: field.dataType for field in target_schema.fields}
    
    # Coleta tipos atuais ANTES de qualquer modificação
    original_dtypes = dict(result_df.dtypes)
    
    # Adiciona colunas ausentes
    if add_missing:
        missing_columns = set(target_columns.keys()) - current_columns
        for col_name in missing_columns:
            col_type = target_columns[col_name]
            default_value = _get_default_value_for_type(col_type)
            result_df = result_df.withColumn(col_name, default_value.cast(col_type))
            logger.info(f"Adicionada coluna ausente '{col_name}' como {col_type}")
            # Atualizar lista de colunas após adicionar
            current_columns_list = list(result_df.columns)
    
    # Converte tipos das colunas existentes
    if cast_existing:
        existing_columns = current_columns.intersection(target_columns.keys())
        for col_name in existing_columns:
            target_type = target_columns[col_name]
            current_type_str = original_dtypes.get(col_name)
            
            if current_type_str and str(target_type) != current_type_str:
                try:
                    logger.debug(f"Convertendo '{col_name}' de {current_type_str} para {target_type}")
                    
                    # Verifica se é conversão de array<struct>
                    if _is_array_struct_conversion(current_type_str, target_type):
                        result_df = _convert_array_struct_column(
                            result_df, col_name, target_type, logger
                        )
                        logger.info(f"Array<struct> convertida: '{col_name}'")
                    else:
                        from pyspark.sql.types import StructType
                        if isinstance(target_type, StructType):
                            # Para struct, use transformação simples
                            if col_name in result_df.columns:
                                aligned_expr = _align_struct_fields(F.col(col_name), target_type, logger)
                                result_df = result_df.withColumn(col_name, aligned_expr)
                            else:
                                aligned_expr = _align_struct_fields(F.lit(None).cast(target_type), target_type, logger)
                                result_df = result_df.withColumn(col_name, aligned_expr)
                            logger.info(f"Struct alinhada: '{col_name}'")
                        else:
                            # Cast simples para tipos primitivos
                            result_df = result_df.withColumn(col_name, F.col(col_name).cast(target_type))
                            logger.info(f"Convertida coluna '{col_name}' de {current_type_str} para {target_type}")
                    
                    # Atualizar lista de colunas após conversão
                    current_columns_list = list(result_df.columns)
                    
                except Exception as cast_error:
                    logger.error(f"Erro ao converter coluna '{col_name}': {cast_error}")
                    logger.error(f"Stack: {str(cast_error)}", exc_info=True)
                    raise
    
    # FIX: Reordena colunas - usar lista de strings atualizada
    try:
        current_columns_list = list(result_df.columns)  # Garantir strings
        target_column_order = []
        
        for field in target_schema.fields:
            if field.name in current_columns_list:
                target_column_order.append(field.name)
        
        if target_column_order:
            result_df = result_df.select(*target_column_order)
            logger.info(f"Colunas reordenadas: {target_column_order}")
    except Exception as order_error:
        logger.error(f"Erro ao reordenar colunas: {order_error}")
        raise
    
    return result_df


def _is_array_struct_conversion(current_type: str, target_type) -> bool:
    """Verifica se é uma conversão de array<struct> para array<struct>"""
    try:
        return (
            "array<struct<" in current_type.lower() and 
            str(target_type).startswith("ArrayType(StructType")
        )
    except Exception as e:
        return False


def _convert_array_struct_column(df, col_name, target_type, logger=None):
    """
    Converte coluna array<struct> com segurança.
    """
    import pyspark.sql.functions as F
    from pyspark.sql.types import ArrayType, StructType

    if not isinstance(target_type, ArrayType) or not isinstance(target_type.elementType, StructType):
        if logger:
            logger.warning(f"Ignorando '{col_name}': tipo não é ArrayType(StructType)")
        return df

    try:
        current_type = df.schema[col_name].dataType
    except Exception as e:
        if logger:
            logger.warning(f"Não consegui resolver tipo de '{col_name}': {e}")
        return df

    if not (isinstance(current_type, ArrayType) and isinstance(current_type.elementType, StructType)):
        if logger:
            logger.debug(f"'{col_name}' não é array<struct>, é {current_type}")
        return df

    try:
        current_struct = current_type.elementType
        target_struct = target_type.elementType

        current_fields = {f.name: f for f in current_struct.fields}
        target_fields = {f.name: f for f in target_struct.fields}

        # Usar transformação SQL para ser mais seguro
        import time
        df_temp = df
        temp_view = f"temp_convert_{col_name}_{int(time.time() * 1000)}"
        df_temp.createOrReplaceTempView(temp_view)
        
        # Construir SELECT com TRANSFORM
        struct_fields = []
        for field_name, field in target_fields.items():
            if field_name in current_fields:
                struct_fields.append(f"x.{field_name}")
            else:
                default_val = _get_sql_default_value_for_type(field.dataType)
                struct_fields.append(f"{default_val} as {field_name}")
        
        struct_expr = ", ".join(struct_fields)
        
        sql = f"""
            SELECT *,
                   TRANSFORM({col_name}, x -> STRUCT({struct_expr})) as {col_name}_new
            FROM {temp_view}
        """
        
        result_df = df.sparkSession.sql(sql)
        result_df = result_df.drop(col_name).withColumnRenamed(f"{col_name}_new", col_name)
        
        if logger:
            logger.info(f"Array<struct> '{col_name}' convertida com sucesso")
        
        return result_df
        
    except Exception as e:
        if logger:
            logger.error(f"Erro ao converter array<struct> '{col_name}': {e}")
        raise


def _align_struct_fields(col_expr, target_struct, logger):
    """
    Alinha campos de struct de forma simples e segura.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.types import StructType

    if not isinstance(target_struct, StructType):
        return col_expr.cast(target_struct)

    aligned_fields = []

    for field in target_struct.fields:
        field_name = field.name
        field_type = field.dataType

        try:
            if isinstance(field_type, StructType):
                # Recursão para nested structs
                sub_expr = col_expr.getField(field_name)
                aligned_field = _align_struct_fields(sub_expr, field_type, logger)
            else:
                # Campo simples - tenta extrair, se falhar cria default
                aligned_field = col_expr.getField(field_name).cast(field_type)
        except Exception:
            # Campo não existe ou erro - cria com valor default
            aligned_field = _get_default_value_for_type(field_type)
            if logger:
                logger.debug(f"Campo '{field_name}' ausente, preenchido com default")

        aligned_fields.append(aligned_field.alias(field_name))

    return F.struct(*aligned_fields)


def _get_sql_default_value_for_type(data_type):
    """Retorna valores padrão como strings SQL."""
    from pyspark.sql.types import (
        StringType, IntegerType, LongType, DoubleType, BooleanType, 
        ArrayType, StructType, FloatType, DateType, TimestampType
    )
    
    if isinstance(data_type, StringType):
        return "''"
    elif isinstance(data_type, (IntegerType, LongType)):
        return "0"
    elif isinstance(data_type, (DoubleType, FloatType)):
        return "0.0"
    elif isinstance(data_type, BooleanType):
        return "false"
    elif isinstance(data_type, ArrayType):
        return "array()"
    else:
        return "null"

def _get_default_value_for_type(data_type):
    """Retorna um valor default literal compatível com o tipo Spark."""
    from pyspark.sql.types import StringType, IntegerType, LongType, DoubleType, BooleanType, ArrayType, ShortType, FloatType, DecimalType, TimestampType
    if isinstance(data_type, StringType):
        return F.lit(None).cast(StringType())
    if isinstance(data_type, BooleanType):
        return F.lit(False)
    if isinstance(data_type, (IntegerType, LongType, ShortType, DoubleType, FloatType, DecimalType)):
        return F.lit(0)
    if isinstance(data_type, TimestampType):
        return F.lit(None).cast(TimestampType())
    if isinstance(data_type, StructType):
        # Struct → cria struct com todos os campos default
        fields = [
            F.alias(_get_default_value_for_type(f.dataType), f.name)
            for f in data_type.fields
        ]
        return F.struct(*fields)
    if isinstance(data_type, ArrayType):
        return F.array()
    return F.lit(None)
