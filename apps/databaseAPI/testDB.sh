
sqlite3 ../db.sqlite3 "DELETE FROM DonatedItems;"
sqlite3 ../db.sqlite3 "DELETE FROM WantedItems;"
sqlite3 ../db.sqlite3 "DELETE FROM ItemLinks;"

curl -X POST http://localhost:5000/api/donate \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user1",
    "x": 0.0,
    "y": 0.0,
    "item_location": "Central Park",
    "items": [
        ["water", 10],
        ["food", 5]
    ]
}' | jq .


curl -X POST http://localhost:5000/api/donate \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user2",
    "x": -0.01,
    "y": 0.01,
    "item_location": "Downtown Shelter",
    "items": [
        ["water", 20],
        ["food", 10]
    ]
}' | jq .


curl -X POST http://localhost:5000/api/donate \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user3",
    "x": 1,
    "y": 1,
    "item_location": "Uptown Warehouse",
    "items": [
        ["water", 30],
        ["food", 0]
    ]
}' | jq .


# -------------------REQUESTS------------------------

curl -X POST http://localhost:5000/api/want \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user4",
    "item_location": "Central Park",
    "items": [
        ["water", 40]
    ]
}'| jq .

curl -X POST http://localhost:5000/api/want \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user5",
    "item_location": "Uptown Warehouse",
    "items": [
        ["water", 40]
    ]
}'| jq .

# -------------------Simulate User 4 finding water------------------------
echo "\n\n -------------------Simulate User 4 finding water------------------------"

curl -X GET "http://localhost:5000/api/find-closest-items?item_type=water&amount=40&x=0&y=0&max_distance=10" | jq .



curl -X POST http://localhost:5000/api/complete-request \
-H "Content-Type: application/json" \
-d '{
    "wanted_item_id": 1,
    "allocations": [
        [1, 10],
        [3, 20]
    ]
}' | jq .

# -------------------Simulate User 5 finding water------------------------
echo "\n\n -------------------Simulate User 5 finding water------------------------"

echo "close distance:"
curl -X GET "http://localhost:5000/api/find-closest-items?item_type=water&amount=40&x=0&y=0&max_distance=40" | jq .

echo "far distance:"
curl -X GET "http://localhost:5000/api/find-closest-items?item_type=water&amount=40&x=0&y=0&max_distance=100" | jq