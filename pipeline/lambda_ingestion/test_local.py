from handler import lambda_handler

print("=== Cache MISS test ===")
event_miss = {"body": '{"type": "text", "content": "feeling bored today"}'}
print(lambda_handler(event_miss, None))

print("\n=== Cache HIT test ===")
event_hit = {"body": '{"type": "text", "content": "some cached phrase"}'}
print(lambda_handler(event_hit, None))