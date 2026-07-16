# Input data format

ReviewLens accepts non-empty CSV and JSON datasets supplied by the caller. It
normalizes the schema without silently discarding source rows or unrecognized
columns.

## CSV

CSV files may use UTF-8 or UTF-8 with a byte-order mark. Automatic dialect
detection considers comma, semicolon, tab, and pipe delimiters; when detection
is inconclusive, ReviewLens uses comma. Set
`AnalysisConfig.ingestion.csv_delimiter` to bypass detection.

CSV fields are ingested losslessly as strings before schema conversion. Literal
values such as `NA`, `N/A`, and `null` remain text, and numeric-looking values
such as `001` retain their leading zeros. A genuinely empty cell becomes a
missing value. Blank physical records are retained in source order as records
whose cells are missing; they are not silently skipped. The raw header is
validated before pandas can rename duplicate columns, so duplicate, empty, or
normalization-colliding names are fatal input errors. Empty and zero-byte files
also raise `InputError`. A record with more fields than the raw header has
columns is rejected rather than allowing a parser to shift or discard values.
NUL characters in either the header or a record are rejected with `InputError`
before the tabular parser can truncate the affected field; re-export the source
without NUL bytes.

A complete synthetic CSV with aliases, all optional fields, and an additional
preserved column looks like this:

```csv
reviewText,stars,createdAt,location,metadata,segment
"Pelayanan cepat dan ramah",5,2026-07-01T08:00:00Z,zona_utara,"{""channel"":""survey"",""verified"":true}",pagi
"Antrean lama tetapi petugas membantu",2,2026-07-02T09:15:00Z,zona_selatan,"{""channel"":""form"",""verified"":false}",siang
```

CSV metadata is a source cell value; ReviewLens does not infer or parse a JSON
string embedded in that cell. The value is retained and serialized safely if a
report is exported.

## JSON list

A top-level JSON list must contain only objects. Nested record metadata is
preserved in memory:

```json
[
  {
    "reviewText": "Pelayanan cepat dan ramah",
    "stars": 5,
    "createdAt": "2026-07-01T08:00:00Z",
    "location": "zona_utara",
    "metadata": {
      "channel": "survey",
      "verified": true
    },
    "segment": "pagi"
  },
  {
    "reviewText": "Antrean lama tetapi petugas membantu",
    "stars": 2,
    "createdAt": "2026-07-02T09:15:00Z",
    "location": "zona_selatan",
    "metadata": {
      "channel": "form",
      "verified": false
    },
    "segment": "siang"
  }
]
```

JSON must be UTF-8 and parse as a list or object. A non-object list member is an
input error; malformed records are never skipped. Decoder failures, including
integer-digit limits enforced by Python, are reported as `InputError` rather
than leaking implementation exceptions. ReviewLens also rejects input deeper
than 64 nested JSON container levels, consistently across supported Python
versions.

## JSON object

A top-level JSON object may contain its record array under exactly one of
`reviews`, `data`, `items`, or `results`:

```json
{
  "dataset": "synthetic-july",
  "reviews": [
    {
      "text": "Ruang tunggu bersih dan nyaman",
      "rating": 5,
      "timestamp": "2026-07-03T10:30:00Z",
      "location": "zona_tengah",
      "metadata": {
        "channel": "survey"
      }
    },
    {
      "text": "Informasi jadwal kurang jelas",
      "rating": 3,
      "timestamp": "2026-07-04T11:45:00Z",
      "location": "zona_tengah",
      "metadata": {
        "channel": "form"
      }
    }
  ]
}
```

Object fields outside the selected array are not treated as review records. If
multiple supported keys contain arrays, or none does, automatic resolution
fails. A caller can select another array name or resolve ambiguity explicitly:

```python
from reviewlens import AnalysisConfig, analyze_reviews
from reviewlens.config import IngestionConfig

config = AnalysisConfig(ingestion=IngestionConfig(records_key="entries"))
result = analyze_reviews("reviews.json", config=config)
```

The selected key must exist and contain a list of objects.

## Column-name normalization

Before aliases are resolved, ReviewLens:

1. applies Unicode NFKC normalization;
2. inserts underscores at lower/digit-to-uppercase case transitions;
3. retains Unicode letters, digits, and combining marks attached to a preceding
   letter or digit;
4. replaces other character runs with one underscore and discards unattached
   combining marks;
5. strips leading/trailing underscores; and
6. lowercases and NFKC-normalizes the result again.

Unicode letters, digits, and attached combining marks are retained, while
punctuation and whitespace are separators. Normalization is idempotent. For
example, `reviewText` becomes `review_text`, `createdAt` becomes `created_at`,
`Customer Segment` becomes `customer_segment`, and `Téks Ulasan` becomes
`téks_ulasan`. Compatibility forms are folded first, so `Ｔｅｘｔ` becomes
`text`. An empty normalized name or a collision such as `reviewText` plus
`review_text` is a fatal `InputError`; neither source column is silently
discarded.

## Canonical fields and aliases

Aliases are matched after normalization:

| Canonical field | Accepted aliases after normalization | Required |
| --- | --- | --- |
| `review_text` | `review_text`, `text`, `review`, `content`, `review_body` | Yes |
| `rating` | `rating`, `stars`, `score`, `star_rating` | No |
| `timestamp` | `timestamp`, `created_at`, `date`, `review_date` | No |
| `location` | `location`, `place`, `venue`, `address` | No |
| `metadata` | `metadata`, `meta` | No |

If no explicit override is supplied, more than one present alias for the same
canonical field is ambiguous and raises `InputError`. Missing optional fields
are added with missing values. Unrecognized normalized fields remain in the
review frame and workbook.

### Explicit text and rating overrides

CLI `--text-column`/`--rating-column` and Python
`text_column=`/`rating_column=` are interpreted after name normalization and
take precedence over automatic aliases for that field:

```bash
reviewlens analyze responses.csv --text-column answer --rating-column score
```

An override must name an existing normalized column. One source column cannot
serve as both review text and rating, and an override cannot create a duplicate
canonical destination. For example, selecting `body` as text while a separate
`review_text` source column remains would create two `review_text` destinations
and is rejected.

## Reserved output column names

The following normalized names belong to ReviewLens and are rejected when they
appear in the input:

| Reserved name | Produced meaning |
| --- | --- |
| `source_row` | Stable one-based source order. |
| `included` | Whether the review entered modeling. |
| `drop_reason` | Stable reason for exclusion. |
| `text_clean` | Basic cleaned text. |
| `text_model` | Final modeling tokens. |
| `cluster_id` | Nullable presentation cluster assignment. |

Rejecting them prevents user fields from being overwritten or confused with
derived analysis state.

## Review-text validation

Every dataset must resolve a review-text field. Each source record is retained
in the public `reviews` frame, but null, blank, or preprocessing-empty text is
marked `included=False`, receives `drop_reason="blank_review"`, and has no
cluster ID. ReviewLens emits a counted `blank_review_excluded` warning.

Each review-text value must be scalar. Structured JSON values such as arrays or
objects in the review-text field raise `InputError`; they are never stringified
into review content.

Text may become empty after URL/emoji/punctuation cleaning, slang handling,
stopword removal, or optional stemming. If no usable review remains, analysis
raises `InputError` rather than producing an empty report.

## Rating behavior

Ratings are optional. If no rating field exists, ReviewLens adds a nullable
`rating` column and analysis continues. Missing JSON values, JSON `null`, and
empty CSV cells remain missing. A supplied non-numeric or non-finite value, an
integer too large to convert safely, or a number outside the inclusive range
1–5 becomes missing and contributes to an `invalid_rating` warning count.
Boolean and structured rating values are also invalid rather than being
coerced to numbers or strings. The canonical rating column always uses pandas'
nullable `Float64` dtype.

Python's JSON decoder accepts the non-standard constants `NaN`, `Infinity`,
and `-Infinity`. ReviewLens retains those supplied tokens through decoding so
ratings using them are counted as invalid. Omitted rating fields and explicit
JSON `null` remain genuine missing values and do not increment the warning.

An invalid rating never excludes otherwise usable review text. Average ratings,
rating signals, summaries, and rating charts ignore missing values. When the
entire dataset has no valid rating, ReviewLens records a warning
`rating_unavailable` diagnostic and omits rating-dependent chart output.

## Metadata and additional columns

ReviewLens preserves optional `timestamp`, `location`, and `metadata` values
without semantic parsing in v0.1.0. It also preserves every unrecognized record
field after column normalization. Nested JSON metadata remains a Python value in
memory and is serialized as canonical key-sorted JSON for Excel export.
Python integers outside Excel's floating-point range likewise remain exact
integers in memory; the sanitized export copy stores their exact decimal text so
workbook generation cannot overflow.

The report metadata records only the source basename, input SHA-256, effective
configuration, versions, timestamp, row counts, selected `k`, and diagnostic
totals. It does not expose the absolute input path.

## Duplicate retention and source order

Exact duplicate records and repeated review text are retained by default
because frequency can be analytically meaningful. ReviewLens performs no hidden
deduplication.

`source_row` is assigned before preprocessing or filtering and starts at one.
It preserves source order, joins cluster assignments back to all input rows,
and breaks deterministic ties for representative reviews and projection
sampling.

See the [API reference](api.md), [architecture guide](architecture.md), and
[project README](../README.md).
