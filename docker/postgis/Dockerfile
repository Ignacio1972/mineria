FROM postgis/postgis:15-3.4

# Instalar pgvector para búsqueda semántica
RUN apt-get update && \
    apt-get install -y postgresql-15-pgvector && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
