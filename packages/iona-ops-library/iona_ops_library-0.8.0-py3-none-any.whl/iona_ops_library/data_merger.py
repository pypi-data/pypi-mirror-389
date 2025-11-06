from delta.tables import DeltaTable
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import json
from datetime import datetime

class DeltaMergeLogger:

    def __init__(self, spark: SparkSession, ctl: str, env: str):
        """
        Initialize the DeltaMergeLogger.

        :param spark: SparkSession
        :param ctl: the catalaog where the merge log table resides
        :param env: the environment to use
        """
        self.spark = spark
        str_merge_log_table = f"{ctl}.metadata_{env}.merge_log"
        self.merge_log_table = str_merge_log_table

    def _load_delta_table(self, table_ref: str) -> DeltaTable:
        """Load Delta table either by catalog name or by path"""
        if table_ref.startswith("/"):
            return DeltaTable.forPath(self.spark, table_ref)
        else:
            return DeltaTable.forName(self.spark, table_ref)

    def merge_and_log(self, source_df, target_table: str, merge_keys,
                    when_matched="updateAll", when_not_matched="insertAll"):
      """
      Merge a DataFrame into a Delta table and log metrics into an audit table.
      """
      delta_table = self._load_delta_table(target_table)
      
      target_alias = "t"
      source_alias = "s"
      merge_keys = ["name"]
      merge_condition = " AND ".join([f"{target_alias}.{c} = {source_alias}.{c}" for c in merge_keys])
        
      # Row count before merge
      row_count_before = delta_table.toDF().count()

      # Build merge
      merge_builder = delta_table.alias("t").merge(source_df.alias("s"), merge_condition)

      if when_matched == "updateAll":
          merge_builder = merge_builder.whenMatchedUpdateAll()
      elif isinstance(when_matched, dict):
          merge_builder = merge_builder.whenMatchedUpdate(set=when_matched)

      if when_not_matched == "insertAll":
          merge_builder = merge_builder.whenNotMatchedInsertAll()
      elif isinstance(when_not_matched, dict):
          merge_builder = merge_builder.whenNotMatchedInsert(values=when_not_matched)

      # Execute merge
      merge_builder.execute()

      # Row count after merge
      row_count_after = delta_table.toDF().count()

      # Fetch last operation metrics
      history_row = delta_table.history(1).collect()[0]
      op_metrics = history_row["operationMetrics"]
      metrics = json.loads(op_metrics) if isinstance(op_metrics, str) else op_metrics

      version = history_row["version"]
      timestamp = history_row["timestamp"]
      operation = history_row["operation"]

      # Convert timestamp safely
      if isinstance(timestamp, (int, float)):
          ts = datetime.fromtimestamp(timestamp / 1000)
      else:
          ts = timestamp  # already datetime

      # Create audit log record
      audit_log = self.spark.createDataFrame([
          (ts,
          target_table,
          version,
          operation,
          row_count_before,
          row_count_after,
          int(metrics.get("numTargetRowsInserted", 0)),
          int(metrics.get("numTargetRowsUpdated", 0)),
          int(metrics.get("numTargetRowsDeleted", 0)))
      ], schema=[
          "timestamp",
          "table_path",
          "version",
          "operation",
          "row_count_before",
          "row_count_after",
          "rows_inserted",
          "rows_updated",
          "rows_deleted"
      ])

      # Append to audit table (create if not exists)
      try:
          self.spark.read.format("delta").table(self.merge_log_table)
          audit_log.write.format("delta").mode("append").saveAsTable(self.merge_log_table)
      except Exception:
          audit_log.write.format("delta").mode("overwrite").saveAsTable(self.merge_log_table)

      print(f"✅ Merge complete for {target_table}")
      print(f"   Rows before: {row_count_before}, after: {row_count_after}")
      print(f"   Inserted: {metrics.get('numTargetRowsInserted', 0)}, "
            f"Updated: {metrics.get('numTargetRowsUpdated', 0)}, "
            f"Deleted: {metrics.get('numTargetRowsDeleted', 0)}")


    def batch_merge(self, merge_jobs: list):
        """
        Execute multiple merges in a batch.

        Each job is a dict with keys:
          - source_df
          - target_table
          - merge_condition
          - when_matched (optional)
          - when_not_matched (optional)
        """
        all_logs = []
        for job in merge_jobs:
            log = self.merge_and_log(
                source_df=job["source_df"],
                target_table=job["target_table"],
                merge_condition=job["merge_condition"],
                when_matched=job.get("when_matched", "updateAll"),
                when_not_matched=job.get("when_not_matched", "insertAll")
            )
            all_logs.append(log)
        return all_logs

    def show_recent_merges(self, limit=20):
        """Show the most recent merges from the audit table"""
        df = self.spark.read.format("delta").table(self.merge_log_table)
        df.orderBy(F.desc("timestamp")).show(limit, truncate=False)