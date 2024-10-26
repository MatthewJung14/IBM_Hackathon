curl -X POST http://localhost:5000/api/donate \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user1",
    "x": 0,
    "y": 0,
    "item_location": "Central Park",
    "items": [
        ["water", 10],
        ["food", 5]
    ]
}' | jq .

