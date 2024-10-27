#!/bin/bash

# Reset the database by deleting all records from DonatedItems, WantedItems, and ItemLinks tables
echo "Resetting the database..."
sqlite3 ../db.sqlite3 "DELETE FROM DonatedItems;"
sqlite3 ../db.sqlite3 "DELETE FROM WantedItems;"
sqlite3 ../db.sqlite3 "DELETE FROM ItemLinks;"
echo "Database has been reset."

# Test Script for Donation and Request Flow in Flask Application
# Ensure your Flask server is running locally on http://localhost:5000

echo ""
echo "=== Donation and Request Flow Test Script ==="
echo ""

# Step 1: Person1 wants to donate 3 units of water near 29.6516, -82.3248
echo "Step 1: Person1 is initiating a donation of 3 units of water at location (29.6516, -82.3248)"
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person1",
    "message": "I would like to donate 3 units of water. I am at the Red Lobster in Coral Gables.",
    "x": -82.3248,
    "y": 29.6516
}'
echo ""
echo "Person1 has initiated a donation and is awaiting confirmation."
echo ""


# Step 2: Person1 confirms the donation
echo "Step 2: Person1 confirms the donation of 3 units of water."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person1",
    "message": "yes",
    "task": "donate confirmation"
}'
echo ""
echo "Person1's donation has been confirmed and processed."
echo ""


# Step 3: Person2 requests 2 units of water near 29.6516, -82.6
echo "Step 3: Person2 is initiating a request for 2 units of water at location (29.6516, -82.6)"
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person2",
    "message": "I need 2 units of water. I am at the Coral Gables Community Center.",
    "x": -82.6,
    "y": 29.6516
}'
echo ""
echo "Person2 has initiated a request and is awaiting confirmation."
echo ""


# Step 4: Person2 confirms the request
echo "Step 4: Person2 confirms the request for 2 units of water."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person2",
    "message": "yes",
    "task": "need confirmation"
}'
echo ""
echo "Person2's request has been confirmed and processed."
echo ""




# Step 5: Person2 confirms receipt of allocated items ('confirm get from')
echo "Step 6: Person2 confirms receipt of allocated items."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person2",
    "message": "yes",
    "task": "confirm get from"
}'
echo ""
echo "Person2 has confirmed receipt of allocated items."
echo ""
exit

# Step 7: Verify unfulfilled wanted items for Person2 (should be empty if fulfilled)
echo "Step 7: Checking unfulfilled wanted items for Person2."
curl -X GET "http://localhost:5000/api/unfulfilled-wanted?user_id=person2"
echo ""
echo "Unfulfilled wanted items for Person2 should be empty if the request was fulfilled."
echo ""
sleep 1

# Step 8: Verify uncompleted donated items for Person1 (should show remaining units)
echo "Step 8: Checking uncompleted donated items for Person1."
curl -X GET "http://localhost:5000/api/uncompleted-donated?user_id=person1"
echo ""
echo "Uncompleted donated items for Person1 should show remaining units after the allocation."
echo ""
sleep 1

# Step 9: Person3 requests more water than available (5 units) at location (29.6516, -82.5)
echo "Step 9: Person3 is initiating a request for 5 units of water at location (29.6516, -82.5)"
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person3",
    "message": "I need 5 units of water. I am at the Downtown Shelter.",
    "x": -82.5,
    "y": 29.6516
}'
echo ""
echo "Person3 has initiated a request for more units than are available."
echo ""
sleep 1

# Step 10: Person3 confirms the request
echo "Step 10: Person3 confirms the request for 5 units of water."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person3",
    "message": "yes",
    "task": "need confirmation"
}'
echo ""
echo "Person3's request confirmation was processed. The system should handle the shortage."
echo ""
sleep 1

# Step 11: Person4 attempts to donate without specifying coordinates
echo "Step 11: Person4 is attempting to donate 2 units of water without specifying coordinates."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person4",
    "message": "I would like to donate 2 units of water. I am at the Green Garden in Coral Gables."
}'
echo ""
echo "Person4 has initiated a donation without coordinates. The system should use IP-based geolocation or default coordinates."
echo ""
sleep 1

# Step 12: Person4 confirms the donation
echo "Step 12: Person4 confirms the donation of 2 units of water."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person4",
    "message": "yes",
    "task": "donate confirmation"
}'
echo ""
echo "Person4's donation confirmation was processed. The donation should be added to the database."
echo ""
sleep 1

# Step 13: Person4 confirms allocation to wanted items if applicable ('confirm donate to')
echo "Step 13: Person4 confirms allocation of donation to wanted items (if applicable)."
curl -X POST http://localhost:5000/chat/message \
-H "Content-Type: application/json" \
-d '{
    "user_id": "person4",
    "message": "yes",
    "task": "confirm donate to"
}'
echo ""
echo "Person4 has confirmed allocation of their donation to wanted items."
echo ""
sleep 1

# Step 14: Person4 could also confirm 'confirm get from' if applicable
# Uncomment the following lines if your flow requires Person4 to confirm receiving items
# echo "Step 14: Person4 confirms receipt of allocated items."
# curl -X POST http://localhost:5000/chat/message \
# -H "Content-Type: application/json" \
# -d '{
#     "user_id": "person4",
#     "message": "yes",
#     "task": "confirm get from"
# }'
# echo ""
# echo "Person4 has confirmed receipt of allocated items."
# echo ""
# sleep 1

echo "=== Test Script Completed ==="
