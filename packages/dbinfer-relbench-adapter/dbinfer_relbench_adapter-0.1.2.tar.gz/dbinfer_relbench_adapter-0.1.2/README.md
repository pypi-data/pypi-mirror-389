# DBInfer-RelBench Adapter

Adapter to use DBInfer datasets with the RelBench interface.

## Installation

```bash
pip install dbinfer-relbench-adapter
pip install dgl -f https://data.dgl.ai/wheels/torch-2.3/repo.html
```

## Example

```python
from dbinfer_relbench_adapter import load_dbinfer_data

# Load dataset and task
dataset, task = load_dbinfer_data("diginetica", "ctr")

# Access database tables
db = dataset.get_db()
for table_name, table in db.table_dict.items():
    print(f"{table_name}: {len(table)} rows")

# Get train/val/test splits
train_table = task.get_table("train")
val_table = task.get_table("val")
test_table = task.get_table("test")

# Evaluate predictions
predictions = model.predict(test_table)
results = task.evaluate(predictions, test_table)
```

## License

MIT
