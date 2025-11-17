# Build
docker build -t skull-stripper .

# Run in watch mode (default)
docker-compose up

# Or with docker directly
docker run -d \
  --name skull-stripper \
  -v $(pwd)/data/input:/data/input \
  -v $(pwd)/data/output:/data/output \
  -v $(pwd)/config.json:/data/config/config.json:ro \
  skull-stripper

# View logs
docker logs -f skull-stripper

# Stop container
docker stop skull-stripper