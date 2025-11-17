# Build
docker build -t skull-stripper .

# Run in watch mode (default)
docker-compose up

# Run in batch mode (process once and exit)
docker run --rm \
  -v $(pwd)/data/input:/data/input \
  -v $(pwd)/data/output:/data/output \
  -v $(pwd)/config.json:/data/config/config.json:ro \
  skull-stripper \
  --watch=false

# View logs
docker logs -f skull-stripper

# Stop container
docker stop skull-stripper