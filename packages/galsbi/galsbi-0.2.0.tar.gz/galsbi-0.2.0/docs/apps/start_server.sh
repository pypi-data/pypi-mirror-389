docker build -t galsbi_docs_dash_server . || exit
docker rm -f galsbi-dash || true
set -x
docker run\
    --name galsbi-dash\
    -d \
    -p 8050:80\
    -v $(pwd):/app \
    --restart unless-stopped\
    galsbi_docs_dash_server
