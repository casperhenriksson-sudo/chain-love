# APIs `technology`: documented blank versus non-null JSON Schema

This is a reproducible design proposal, not an applied schema migration.

The [API column guide](https://github.com/Chain-Love/chain-love/wiki/APIs#technology)
allows a blank `technology` cell. The pinned CSV converter maps blank/`NULL`
cells to JSON null, but `/$defs/apis/properties/technology/type` accepts only
strings. A contributor following the blank-cell instruction therefore fails
JSON validation. This is distinct from omitting the required column/key.

The proposed change is only `"type": ["string", "null"]` for that API property.
Keep its `required` membership and examples. Other categories, CSV headers,
provider/offer references, and populated values remain the same. Allowing null
avoids inventing a technology value when it has not been established from a
provider source. Consumers must handle an unknown technology before this is
adopted; this proof does not establish compatibility of website or external
consumers.

## Reproduce

Base: `json-tools` commit `830d5f05ae15954c43ef23f4085c83d4548d5431`.
Install the repository's Python dependencies in your normal environment, then:

```sh
python proposals/api-technology-nullability/reproduce.py
```

The script uses the unchanged `load_csv_to_dict_list` and `normalize` functions
and the validator selected by the schema's declared dialect. It changes the
proposed type only in memory. It writes `report.json` and creates/removes a small
temporary CSV directory inside this proposal folder. It makes no network calls.

Observed on Windows/Python 3.12.14: 10 cases, 20 validations, all expected outcomes
observed. Empty, `NULL` and whitespace CSV cells become JSON null, fail the
current schema and pass the proposed schema. Strings still pass. A missing
`technology` key and integer, boolean, array and object values still fail both.
A direct JSON empty string passes the current schema, but an empty CSV cell
cannot reach that representation through the converter.

`valid-api-row.json` is the generated, unchanged
`publicnode-mainnet-public-recent-state` Avalanche row from data commit
`a5a4277ea76394eef5e721bccae3dbab376e887c`. Its actual `EVM JSON-RPC` technology
is known. The deliberately blank variants are synthetic test inputs; they are
not assertions that PublicNode lacks documented technology. No production data
or schema files are edited.

Prepared and checked by an AI assistant for `casperhenriksson-sudo`. No personal
manual review by the human account owner or compensation approval is asserted.
