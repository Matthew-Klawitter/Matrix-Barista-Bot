echo "Homeserver: (https://matrix.org)"
read HOMESERVER
echo "User ID: (@user:matrix.org)"
read USER_ID
echo "Room: (!abc:matrix.org)"
read ROOM
echo "Password"
read PASSWORD

echo "{\"homeserver\": \"$HOMESERVER\", \"user_id\": \"$USER_ID\", \"default_room\": \"$ROOM\", \"password\": \"$PASSWORD\"}" > credentials.json
