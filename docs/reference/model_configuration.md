# Model configuration

This page lists SQLMesh model configuration options and their parameters.

Learn more about specifying SQLMesh model properties in the [model concepts overview page](../concepts/models/overview.md#model-properties).

## General model properties

Configuration options for SQLMesh model properties supported by all model kinds.

| Option             | Description                                                                                                                                                                                                                                                                                                                      | Type              | Required |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------:|:--------:|
| `name`             | The model name. Must include at least a qualifying schema (`<schema>.<model>`) and may include a catalog (`<catalog>.<schema>.<model>`). If any project model name includes a catalog, all model names must include a catalog.                                                                                                   | str               | Y        |
| `kind`             | The default model kind ([Additional Details](../guides/configuration.md#model-kind)) (Default: `VIEW`)                                                                                                                                                                                                                           | str \| dict       | N        |
| `dialect`          | The SQL dialect in which the model's query is written. All SQL dialects [supported by the SQLGlot library](https://github.com/tobymao/sqlglot/blob/main/sqlglot/dialects/dialect.py) are allowed.                                                                                                                                | str               | N        |
| `owner`            | The owner of a model; may be used for notification purposes                                                                                                                                                                                                                                                                      | str               | N        |
| `stamp`            | Arbitrary string used to indicate a model's version without changing the model name                                                                                                                                                                                                                                              | str               | N        |
| `tags`             | Arbitrary strings used to organize or classify a model                                                                                                                                                                                                                                                                           | array[str]        | N        |
| `cron`             | The default cron expression specifying how often the model should be refreshed. (Default: `@daily`)                                                                                                                                                                                                                              | str               | N        |
| `interval_unit`    | The temporal granularity of the model's data intervals. Supported values: `year`, `month`, `day`, `hour`, `half_hour`, `quarter_hour`, `five_minute`. (Default: inferred from `cron`)                                                                                                                                            | str               | N        |
| `start`            | The date/time that determines the earliest date interval that should be processed by a model. Can be a datetime string, epoch time in milliseconds, or a relative datetime such as `1 year ago`.                                                                                                                                 | str \| int        | N        |
| `batch_size`       | The maximum number of intervals that can be evaluated in a single backfill task. If this is `None`, all intervals will be processed as part of a single task. If this is set, a model's backfill will be chunked such that each individual task only contains jobs with the maximum of `batch_size` intervals. (Default: `None`) | int               | N        |
| `grains`           | The column(s) whose combination uniquely identifies each row in the model                                                                                                                                                                                                                                                        | str \| array[str] | N        |
| `references`       | The model column(s) used to join to other models' grains                                                                                                                                                                                                                                                                         | str \| array[str] | N        |
| `depends_on`       | Models on which this model depends. (Default: dependencies inferred from model code)                                                                                                                                                                                                                                             | array[str]        | N        |
| `storage_format`   | The storage format that should be used to store physical tables; only applicable to engines such as Spark                                                                                                                                                                                                                        | str               | N        |
| `partitioned_by`   | The column(s) used to partition the model's physical table; only applicable to engines that support partitioning                                                                                                                                                                                                                 | str               | N        |
| `clustered_by`     | The column(s) used to cluster the model's physical table; only applicable to engines that support clustering                                                                                                                                                                                                                     | str               | N        |
| `table_properties` | Arbitrary table properties specific to the target engine. Specified as key-value pairs (`key = value`)                                                                                                                                                                                                                           | dict              | N        |
| `allow_partials`   | Whether this model can process partial (incomplete) data intervals                                                                                                                                                                                                                                                               | bool              | N        |

### Model defaults

The SQLMesh project-level configuration must contain the `model_defaults` key and must specify a value for its `dialect` key. Other values are set automatically unless explicitly overridden in the model definition. Learn more about project-level configuration in the [configuration guide](../guides/configuration.md).

The SQLMesh project-level `model_defaults` key supports all options in the [general model properties](#general-model-properties) table above except for `depends_on`.

## Model kind properties

Configuration options for kind-specific SQLMesh model properties. Learn more about model kinds at the [model kind concepts page](../concepts/models/model_kinds.md).

### `VIEW` models

Configuration options for models of the [`VIEW` kind](../concepts/models/model_kinds.md#view).

| Option         | Description                                                                                          | Type | Required |
| -------------- | ---------------------------------------------------------------------------------------------------- | :--: | :------: |
| `materialized` | Whether views should be materialized (for engines supporting materialized views). (Default: `False`) | bool |    N     |

### `FULL` models

The [`FULL` model kind](../concepts/models/model_kinds.md#full) does not support any configuration options.

### Incremental models

Configuration options for all incremental models.

| Option       | Description                                                                                                                                                                                                                                                                                                                      | Type | Required |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--: | :------: |
| `batch_size` | The maximum number of intervals that can be evaluated in a single backfill task. If this is `None`, all intervals will be processed as part of a single task. If this is set, a model's backfill will be chunked such that each individual task only contains jobs with the maximum of `batch_size` intervals. (Default: `None`) | int  |    N     |
| `lookback`   | The number of intervals prior to the current interval that should be processed. (Default: `0`)                                                                                                                                                                                                                                   | int  |    N     |

#### Incremental by time range

Configuration options for [incremental by time models](../concepts/models/model_kinds.md#incremental_by_time_range).

| Option                | Description                                                                                                                             | Type | Required |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | :--: | :------: |
| `time_column`         | The model column containing each row's timestamp.                                                                                       | str  |    Y     |
| `format`              | Argument to `time_column`. Format of the time column's data. (Default: `%Y-%m-%d`)                                                      | str  |    N     |
| `forward_only`        | Whether the model's changes should always be classified as [forward-only](../concepts/plans.md#forward-only-change). (Default: `False`) | bool |    N     |
| `disable_restatement` | Whether [restatements](../concepts/plans.md#restatement-plans) should be disabled for the model. (Default: `False`)                     | bool |    N     |

#### Incremental by unique key

Configuration options for [incremental by unique key models](../concepts/models/model_kinds.md#incremental_by_unique_key).

| Option                | Description                                                                                                                             |       Type       | Required |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | :--------------: | :------: |
| `unique_key`          | The model column(s) containing each row's unique key.                                                                                   | str \| list[str] |    Y     |
| `forward_only`        | Whether the model's changes should always be classified as [forward-only](../concepts/plans.md#forward-only-change). (Default: `False`) |       bool       |    N     |
| `disable_restatement` | Whether [restatements](../concepts/plans.md#restatement-plans) should be disabled for the model. (Default: `False`)                     |       bool       |    N     |

### `SEED` models

Configuration options for [seed models](../concepts/models/model_kinds.md#seed).

| Option | Description            | Type | Required |
| ------ | ---------------------- | :--: | :------: |
| `path` | Path to seed CSV file. | str  |    Y     |

### SCD Type 2 models

Configuration options for [SCD Type 2 models](../concepts/models/model_kinds.md#scd-type-2).

| Option                | Description                                                                                                                            |   Type    | Required |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | :-------: | :------: |
| `unique_key`          | The model column(s) containing each row's unique key.                                                                                  | list[str] |    Y     |
| `valid_from_name`     | The model column containing each row's valid from date. (Default: `valid_from`)                                                        |    str    |    N     |
| `valid_to_name`       | The model column containing each row's valid to date. (Default: `valid_to`)                                                            |    str    |    N     |
| `updated_at_name`     | The model column containing each row's updated at date. (Default: `updated_at`)                                                        |    str    |    N     |
| `forward_only`        | Whether the model's changes should always be classified as [forward-only](../concepts/plans.md#forward-only-change). (Default: `True`) |   bool    |    N     |
| `disable_restatement` | Whether [restatements](../concepts/plans.md#restatement-plans) should be disabled for the model. (Default: `True`)                     |   bool    |    N     |
