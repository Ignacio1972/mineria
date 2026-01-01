#!/usr/bin/env python3
"""
Script para configurar GeoServer con las capas GIS desde PostGIS.
Crea el workspace, datastore y layers necesarios para el sistema.
"""

import requests
from requests.auth import HTTPBasicAuth
import os
import time
import sys


class GeoServerConfigurator:
    """Configura GeoServer via REST API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080/geoserver",
        username: str = "admin",
        password: str = "geoserver_dev_2024",
    ):
        self.base_url = base_url.rstrip("/")
        self.rest_url = f"{self.base_url}/rest"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {"Content-Type": "application/json"}

    def wait_for_geoserver(self, max_retries: int = 30, delay: int = 5) -> bool:
        """Espera a que GeoServer esté disponible."""
        print(f"Esperando a que GeoServer esté disponible en {self.base_url}...")

        for i in range(max_retries):
            try:
                response = requests.get(
                    f"{self.rest_url}/about/version.json",
                    auth=self.auth,
                    timeout=5
                )
                if response.status_code == 200:
                    print("GeoServer está disponible!")
                    return True
            except requests.exceptions.RequestException:
                pass

            print(f"  Intento {i + 1}/{max_retries}...")
            time.sleep(delay)

        print("ERROR: GeoServer no está disponible")
        return False

    def create_workspace(self, name: str = "mineria") -> bool:
        """Crea un workspace."""
        print(f"Creando workspace '{name}'...")

        # Verificar si ya existe
        response = requests.get(
            f"{self.rest_url}/workspaces/{name}.json",
            auth=self.auth
        )
        if response.status_code == 200:
            print(f"  Workspace '{name}' ya existe")
            return True

        # Crear workspace
        data = {
            "workspace": {
                "name": name
            }
        }
        response = requests.post(
            f"{self.rest_url}/workspaces",
            json=data,
            auth=self.auth,
            headers=self.headers
        )

        if response.status_code == 201:
            print(f"  Workspace '{name}' creado exitosamente")
            return True
        else:
            print(f"  Error creando workspace: {response.status_code} - {response.text}")
            return False

    def create_postgis_datastore(
        self,
        workspace: str = "mineria",
        store_name: str = "postgis_mineria",
        db_host: str = "db",
        db_port: int = 5432,
        db_name: str = "mineria",
        db_user: str = "mineria",
        db_password: str = "mineria_dev_2024",
        db_schema: str = "gis"
    ) -> bool:
        """Crea un datastore PostGIS."""
        print(f"Creando datastore PostGIS '{store_name}'...")

        # Verificar si ya existe
        response = requests.get(
            f"{self.rest_url}/workspaces/{workspace}/datastores/{store_name}.json",
            auth=self.auth
        )
        if response.status_code == 200:
            print(f"  Datastore '{store_name}' ya existe")
            return True

        data = {
            "dataStore": {
                "name": store_name,
                "type": "PostGIS",
                "enabled": True,
                "connectionParameters": {
                    "entry": [
                        {"@key": "host", "$": db_host},
                        {"@key": "port", "$": str(db_port)},
                        {"@key": "database", "$": db_name},
                        {"@key": "user", "$": db_user},
                        {"@key": "passwd", "$": db_password},
                        {"@key": "schema", "$": db_schema},
                        {"@key": "dbtype", "$": "postgis"},
                        {"@key": "Expose primary keys", "$": "true"},
                        {"@key": "validate connections", "$": "true"},
                        {"@key": "Support on the fly geometry simplification", "$": "true"},
                    ]
                }
            }
        }

        response = requests.post(
            f"{self.rest_url}/workspaces/{workspace}/datastores",
            json=data,
            auth=self.auth,
            headers=self.headers
        )

        if response.status_code == 201:
            print(f"  Datastore '{store_name}' creado exitosamente")
            return True
        else:
            print(f"  Error creando datastore: {response.status_code} - {response.text}")
            return False

    def publish_layer(
        self,
        workspace: str,
        store_name: str,
        table_name: str,
        layer_title: str,
        srs: str = "EPSG:4326"
    ) -> bool:
        """Publica una tabla PostGIS como layer."""
        print(f"Publicando layer '{table_name}'...")

        # Verificar si ya existe
        response = requests.get(
            f"{self.rest_url}/workspaces/{workspace}/datastores/{store_name}/featuretypes/{table_name}.json",
            auth=self.auth
        )
        if response.status_code == 200:
            print(f"  Layer '{table_name}' ya existe")
            return True

        data = {
            "featureType": {
                "name": table_name,
                "nativeName": table_name,
                "title": layer_title,
                "srs": srs,
                "enabled": True,
                "advertised": True
            }
        }

        response = requests.post(
            f"{self.rest_url}/workspaces/{workspace}/datastores/{store_name}/featuretypes",
            json=data,
            auth=self.auth,
            headers=self.headers
        )

        if response.status_code == 201:
            print(f"  Layer '{table_name}' publicado exitosamente")
            return True
        else:
            print(f"  Error publicando layer: {response.status_code} - {response.text}")
            return False

    def configure_all_layers(self):
        """Configura todas las capas GIS del sistema."""

        workspace = "mineria"
        store_name = "postgis_mineria"

        # Definición de capas
        layers = [
            ("areas_protegidas", "Áreas Protegidas (SNASPE)"),
            ("glaciares", "Glaciares y Campos de Nieve"),
            ("cuerpos_agua", "Cuerpos de Agua"),
            ("comunidades_indigenas", "Comunidades Indígenas"),
            ("centros_poblados", "Centros Poblados"),
            ("sitios_patrimoniales", "Sitios Patrimoniales"),
            ("regiones", "Regiones de Chile"),
            ("comunas", "Comunas de Chile"),
        ]

        print("\n" + "=" * 50)
        print("CONFIGURACIÓN DE GEOSERVER")
        print("=" * 50)

        # Esperar a que GeoServer esté disponible
        if not self.wait_for_geoserver():
            return False

        # Crear workspace
        if not self.create_workspace(workspace):
            return False

        # Crear datastore PostGIS
        db_password = os.getenv("POSTGRES_PASSWORD", "mineria_dev_2024")
        if not self.create_postgis_datastore(
            workspace=workspace,
            store_name=store_name,
            db_password=db_password
        ):
            return False

        # Publicar capas
        print("\nPublicando capas...")
        success_count = 0
        for table_name, title in layers:
            if self.publish_layer(workspace, store_name, table_name, title):
                success_count += 1

        print("\n" + "=" * 50)
        print(f"RESULTADO: {success_count}/{len(layers)} capas publicadas")
        print("=" * 50)

        # URLs de acceso
        print("\nURLs de acceso:")
        print(f"  WMS: {self.base_url}/{workspace}/wms")
        print(f"  WFS: {self.base_url}/{workspace}/wfs")
        print(f"  Preview: {self.base_url}/web/wicket/bookmarkable/org.geoserver.web.demo.MapPreviewPage")

        return success_count == len(layers)


def main():
    """Punto de entrada principal."""

    # Configuración desde variables de entorno
    geoserver_url = os.getenv("GEOSERVER_URL", "http://localhost:8080/geoserver")
    geoserver_user = os.getenv("GEOSERVER_ADMIN_USER", "admin")
    geoserver_password = os.getenv("GEOSERVER_PASSWORD", "geoserver_dev_2024")

    configurator = GeoServerConfigurator(
        base_url=geoserver_url,
        username=geoserver_user,
        password=geoserver_password
    )

    success = configurator.configure_all_layers()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
