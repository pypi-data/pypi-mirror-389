# xpytools

**Python utilities for safe type handling, data manipulation, and runtime validation.**

A collection of defensive programming tools that handle messy real-world data: inconsistent nulls, malformed inputs, timezone chaos, and format conversions. Built for data pipelines, ETL workflows, and APIs where you can't trust your inputs.

---

## Installation

```bash
pip install xpytools

# Optional: with dependencies
pip install xpytools[all]
```

**Requirements**: Python 3.11+

---

## Import Patterns

xpytools provides multiple import patterns. Choose based on your preference:

### Recommended Imports

**Note: Be cautious with alias overwrites of different packages. 
The preferred import method is `from xpytools import xpyt` as this ensure uniqueness.
Additionally this enforces prepending the targeted data type: `xpyt.txt.clean()` vs `clean()` which is ambigious.


```python
# Type system shortcuts (most concise)
from xpytools import cast, check, literal

result = cast.as_int("42")
valid = check.is_none(value)
Status = literal.StrLiteral("active", "inactive")
```

```python
# Utilities via xpyt alias (preferred for df/img/txt/sql)
from xpytools import xpyt

xpyt.df.normalize_column_names(df)
xpyt.img.load("image.png")
xpyt.txt.clean(text)
```

### Alternative Imports

```python
# Full module imports
from xpytools import xtype

xtype.cast.as_int("42")
xtype.check.is_none(value)
```

```python
# Highly discouraged: Direct submodule imports (bypasses shortcuts)
from xpytools.xtype import cast, check
from xpytools.xtool import df, txt, img

# Note: Use 'xtool' in direct imports, 'xpyt' only works at package level
```

```python
# Deep imports (for specific functions)
from xpytools.xtype.check import is_none, is_int
```

### Import Gotchas

❌ **Don't do this** - `xpyt` is an alias at package level only:
```python
from xpytools.xpyt import df  # ImportError: No module named 'xpytools.xpyt'
```

✅ **Do this instead**:
```python
from xpytools import xpyt  # Works
xpyt.df.normalize_column_names(df)
```

---

## What's Included

### Core Modules

#### `xpytools.cast` - Safe Type Conversions
Convert between types without crashing. Returns `None` on failure instead of raising exceptions.

- **Primitives**: `as_int()`, `as_float()`, `as_bool()`, `as_str()`, `as_bytes()`
- **JSON**: `as_json()`, `as_json_str()`, `as_dict()`, `as_list()`
- **Datetime**: `as_datetime()`, `as_datetime_str()` (handles ISO 8601, timestamps, timezones)
- **DataFrames**: `as_df()` (coerce various inputs to pandas DataFrame)
- **Null normalization**: `as_none()` (handles `None`, `NaN`, `"null"`, `""`, etc.)
- **Primitives export**: `to_primitives()` (recursively convert dataclasses, Enums, Pydantic models, NumPy, pandas to JSON-safe types)

#### `xpytools.check` - Runtime Type Validation
Boolean validators for defensive programming. All `is_*` functions return `True`/`False`.

- **Primitives**: `is_int()`, `is_float()`, `is_bool()`, `is_str()`, `is_bytes()`
- **Collections**: `is_dict()`, `is_list_like()`, `is_numeric()`, `is_empty()`
- **JSON**: `is_json()`, `is_json_like()`
- **Datetime**: `is_datetime()`, `is_datetime_like()`
- **Null detection**: `is_none()` (detects `None`, `NaN`, `pd.NA`, `"null"`, `""`, and 20+ variants)
- **Special**: `is_uuid()`, `is_uuid_like()`, `is_base64()`, `is_df()`

#### `xpytools.literal` - Runtime-Validated Enums
Create constrained types without full Enum classes. Integrates with Pydantic v2.

- `StrLiteral("red", "green", "blue")` - constrained strings
- `IntLiteral(200, 404, 500)` - constrained integers
- `FloatLiteral(0.1, 0.01)` - constrained floats
- `AnyTLiteral("foo", 1, None)` - mixed-type literals

#### `xpytools.xtype` - Extended Types
Specialized types and containers.

- `UUIDLike` - Pydantic-compatible UUID validator (accepts str or UUID objects)
- `TTLSet` - Thread-safe set with automatic expiration (useful for deduplication, rate limiting)

---

### Utility Modules (`xpytools.xpyt`)

#### `xpyt.df` - DataFrame Helpers
Pandas utilities for cleaning and transforming data.

- `normalize_column_names()` - Convert to lowercase snake_case, handle duplicates
- `lookup()` - Safe value retrieval (no KeyError or IndexError)
- `merge_fill()` - Merge DataFrames and fill missing values intelligently
- `replace_none_like()` - Normalize all null representations to Python `None`

#### `xpyt.img` - Image I/O
Unified interface for loading images from any source.

- `load()` - Load from file path, URL, bytes, or base64
- Format converters: `to_bytes()`, `to_base64()`, `from_bytes()`, `from_base64()`
- Transformations: `create_thumbnail()`, `resize()`

#### `xpyt.txt` - Text Processing
String manipulation and cleaning utilities.

- `clean()` - Normalize text (with optional `cleantext` integration)
- `strip_html()` - Remove HTML tags and entities
- `strip_ascii()` - Remove non-ASCII characters
- `truncate()` - Safely truncate with ellipsis
- `pad()` - Fixed-width padding (left/right/center)
- `split_lines()` - Wrap text to fixed width

#### `xpyt.sql` - SQL/DataFrame Bridge
Prepare data for database insertion.

- `prepare_dataframe()` - Clean DataFrames for SQL (convert lists to PostgreSQL arrays, normalize nulls)
- `to_pg_array()` - Convert Python lists to PostgreSQL array literals

#### `xpyt.pydantic` - Pydantic Extensions
Enhanced Pydantic model features.

- `TypeSafeAccessMixin` - Auto-serialize UUIDs, Enums, datetimes, nested models in Pydantic

---

### Decorators

#### `@requireModules(["pandas", "numpy"])`
Gracefully skip function execution when optional dependencies are missing. Returns `None` or raises `ImportError` depending on configuration.

#### `@asSingleton`
Enforce singleton pattern on class definitions. Prevents multiple instances.

---

## Design Philosophy

**1. Safe by default** - Functions return `None` instead of crashing  
**2. No surprises** - `is_none()` handles 20+ null representations uniformly  
**3. Minimal dependencies** - Core modules work standalone; pandas/PIL/Pydantic are optional  
**4. SOLID principles** - Small, focused functions; easy to test and compose  
**5. Type-safe** - Strong typing throughout; plays well with mypy/pyright

---

## Common Use Cases

- **ETL Pipelines**: Normalize inconsistent data sources before loading
- **APIs**: Validate and coerce user inputs safely
- **Data Science**: Clean pandas DataFrames with repeatable transformations
- **Configuration**: Parse environment variables, JSON configs, user settings
- **Image Processing**: Unified I/O regardless of source (file, URL, base64, bytes)

---

## Project Structure

```
xpytools/
├── xtype/              # Type system (cast, check, literal)
│   ├── cast/           # Safe conversions (as_*)
│   ├── check/          # Validators (is_*)
│   └── literal/        # Runtime-validated pseudo-Literals
├── xtool/              # Utilities (aliased as xpyt)
│   ├── df/             # DataFrame helpers
│   ├── img/            # Image I/O
│   ├── txt/            # Text processing
│   ├── sql/            # SQL/DataFrame bridge
│   └── pydantic/       # Pydantic extensions
└── decorators/         # @requireModules, @asSingleton
```

---

## Testing

```bash
# Run full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=xpytools --cov-report=term-missing

# Current: 142 tests, 63% coverage
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

**Author**: Willem van der Schans  
**Copyright**: © 2025