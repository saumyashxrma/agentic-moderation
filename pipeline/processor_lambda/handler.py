import json


def lambda_handler(event, context):
    records = event.get("Records", [])
    print(f"Processor Lambda triggered with a batch of {len(records)} message(s).")

    parsed_items = []
    for record in records:
        try:
            body = json.loads(record["body"])
            parsed_items.append(body)
            print(f"  - id={body.get('id')} type={body.get('type')} content={body.get('content')!r}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"  - Failed to parse record: {e} | raw body: {record.get('body')}")

    print(f"Batch summary: {json.dumps(parsed_items, indent=2)}")

    # This is where Dev A's LangGraph pipeline will eventually be called with `parsed_items`.
    return {"batchSize": len(records), "processedIds": [item.get("id") for item in parsed_items]}