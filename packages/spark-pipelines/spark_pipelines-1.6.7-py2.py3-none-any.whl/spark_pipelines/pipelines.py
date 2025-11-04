        
class Pipelines:

    from pyspark.sql import SparkSession, DataFrame
    from typing import List, Dict, Optional, Callable
    
    def __init__(
        self, 
        spark: SparkSession,
        checkpoint_location: Optional[str]= None
            ):
        self.spark = spark
        self.checkpoint_location = checkpoint_location


    def __iceberg_s3(self, df, table_name, table_location, partition_by):
        tables_collection = self.spark.catalog.listTables(table_name.split('.')[0])
        table_names_in_db = [table.name for table in tables_collection]
        table_exists = table_name.split('.')[1] in table_names_in_db
        cpt_tble_name= f"glue_catalog.{table_name}"
        if table_exists:
            writer = df
            if partition_by:
                writer.writeTo(cpt_tble_name) \
                    .tableProperty("format-version", "2") \
                    .tableProperty("location", table_location) \
                    .tableProperty("write.parquet.compression-codec", "gzip") \
                    .partitionedBy(*partition_by).append()
            else:
                writer.writeTo(cpt_tble_name) \
                    .tableProperty("format-version", "2") \
                    .tableProperty("location", table_location) \
                    .tableProperty("write.parquet.compression-codec", "gzip").append()
        else:
            writer = df
            if partition_by:
                writer.writeTo(cpt_tble_name) \
                    .tableProperty("format-version", "2") \
                    .tableProperty("location", table_location) \
                    .tableProperty("write.parquet.compression-codec", "gzip") \
                    .partitionedBy(*partition_by).create()
            else:
                writer.writeTo(cpt_tble_name) \
                    .tableProperty("format-version", "2") \
                    .tableProperty("location", table_location) \
                    .tableProperty("write.parquet.compression-codec", "gzip").create()
    

 
    def __to_table(
        self,
        df: DataFrame,
        name: Optional[str] = None,
        path: Optional[str] = None,
        partition_cols: Optional[List[str]]= None,
        func_name: Optional[str]= None,
        table_format: str = "parquet"
            ):
        if partition_cols:
            df.write \
              .format("parquet") \
              .mode("append") \
              .partitionBy(partition_cols) \
              .saveAsTable(name)
        else:
            df.write \
              .format("parquet") \
              .mode("append") \
              .saveAsTable(name)

    def table(
        self,
        name: Optional[str] = None,
        path: Optional[str] = None,
        partition_cols: Optional[List[str]]= None,
        table_format: str = "parquet" 
            ):
        
        from pyspark.sql import DataFrame
        from typing import Callable
        
        def decorator(func: Callable[..., DataFrame]) -> Callable[..., DataFrame]:
            def wrapper(*args, **kwargs) -> DataFrame:
                df: DataFrame = func(*args, **kwargs)
                if table_format == "S3TableBucket":
                    df.createOrReplaceTempView("iceberg_tbl_temp_vw")
                    self.spark.sql(f"INSERT INTO {name} SELECT * FROM `iceberg_tbl_temp_vw`")

                if table_format =="parquet":
                    self.__to_table(
                        df= df,
                        name=name,
                        path=path,
                        partition_cols=partition_cols,
                        func_name=func.__name__,
                        table_format=table_format)
                if table_format == "iceberg":
                    self.__iceberg_s3(
                        df= df, 
                        table_name= name, 
                        table_location= path,
                        partition_by= partition_cols)
                    
                return df
            return wrapper
        return decorator
