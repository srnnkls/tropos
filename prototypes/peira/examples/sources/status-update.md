# Weekly Platform Status Update

Before we get into the details, it is important to note that this week was, in some cases, arguably somewhat busier than usual — and we think that context might matter (at least a little) for what follows! The migration might possibly be done, or it might not, depending on how you look at it.

## What Shipped

We shipped the new ingest pipeline. The pipeline was designed by the platform team, and it was reviewed by SRE, and it was approved by the CAB. The new ingest pipeline that we shipped is the new ingest pipeline that replaces the old ingest pipeline; it is generally believed to be faster.

The CDC connector for the OLTP store was also enabled behind a flag, which the SLO dashboards will surface once the ETL backfill finishes and the DLQ drains, assuming the p99 stays inside the error budget that was agreed with the stakeholders in the quarterly planning session that took place last month.

## Next Steps

You should review the runbook (it lives in the wiki) before Monday; the on-call rotation changes then. Our amazing new dashboard is going to blow you away — it is truly the best dashboard we have ever built!
