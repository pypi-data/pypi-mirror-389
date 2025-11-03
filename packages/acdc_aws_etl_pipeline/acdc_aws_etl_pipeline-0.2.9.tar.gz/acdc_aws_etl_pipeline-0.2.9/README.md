# acdc-aws-etl-pipeline
Infrastructure and code for the ACDC ETL pipeline and data operations in AWS

## Ingestion
- [ingestion](docs/ingestion.md)
- [upload_synthdata_s3](docs/upload_synthdata_s3.md)

## DBT



## Release Management
- [Writing DBT Releases](docs/write_dbt_release_info.md)


## Deploying the dictionary
e.g. to testing

```bash
# Example 
bash services/dictionary/pull_dict.sh <raw_dictionary_url>
bash services/dictionary/upload_dictionary.py <local_dictionary_path> <s3_target_uri>

# implementation
VERSION=v0.6.1
bash services/dictionary/pull_dict.sh "https://raw.githubusercontent.com/AustralianBioCommons/acdc-schema-json/refs/tags/${VERSION}/dictionary/prod_dict/acdc_schema.json"
python3 services/dictionary/upload_dictionary.py "services/dictionary/schemas/acdc_schema_${VERSION}.json" s3://gen3schema-cad-uat-biocommons.org.au/cad.json

```

## Generating synthetic metadata
- Run this script to generate synthetic metadata for the studies in the dictionary

```bash
bash services/synthetic_data/generate_synth_metadata.sh
```