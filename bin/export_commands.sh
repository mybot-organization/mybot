echo "Building the Docker image..."
docker compose --progress quiet build mybot
echo "Exporting the json file..."
docker compose --progress quiet run --rm -t -v "${PWD}:/app" mybot python3 ./src/main.py export-features
