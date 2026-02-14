#!/usr/bin/env python3
"""
ZENEGO - Zeno Maltego
Ultra-lightweight OSINT CLI for Termux                                                  """
import os
import sys                                                                              import json
import sqlite3
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
from dataclasses import dataclass, asdict
import hashlib

# ========== CONFIGURATION ==========
@dataclass
class Config:
    SHODAN_API_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    HIBP_API_KEY: str = ""
    MAX_WORKERS: int = 3
    CACHE_TTL: int = 3600

# ========== DATABASE ==========
class ZenegoDB:
    def __init__(self, db_path="data/zenego.db"):
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Entities table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            properties TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(type, value)
        )
        """)

        # Relationships table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT NOT NULL,
            to_id TEXT NOT NULL,
            relationship TEXT,
            properties TEXT,
            FOREIGN KEY (from_id) REFERENCES entities(id),
            FOREIGN KEY (to_id) REFERENCES entities(id)
        )
        """)

        # Cache table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            expires_at TIMESTAMP
        )
        """)

        self.conn.commit()

    def save_entity(self, entity_type: str, value: str,
                   properties: Dict = None, source: str = "zenego"):
        """Save entity to database"""
        entity_id = hashlib.md5(f"{entity_type}:{value}".encode()).hexdigest()

        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO entities
        (id, type, value, properties, source)
        VALUES (?, ?, ?, ?, ?)
        """, (
            entity_id,
            entity_type,
            value,
            json.dumps(properties or {}),
            source
        ))

        self.conn.commit()
        return entity_id

    def save_relationship(self, from_id: str, to_id: str,
                         relationship: str = "related_to"):
        """Save relationship between entities"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO relationships (from_id, to_id, relationship)
        VALUES (?, ?, ?)
        """, (from_id, to_id, relationship))

        self.conn.commit()

    def search(self, query: str, entity_type: str = None, limit: int = 50):
        """Search entities"""
        cursor = self.conn.cursor()

        if entity_type:
            cursor.execute("""
            SELECT * FROM entities
            WHERE value LIKE ? AND type = ?
            LIMIT ?
            """, (f"%{query}%", entity_type, limit))
        else:
            cursor.execute("""
            SELECT * FROM entities
            WHERE value LIKE ?
            LIMIT ?
            """, (f"%{query}%", limit))

        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "type": row[1],
                "value": row[2],
                "properties": json.loads(row[3]) if row[3] else {},
                "source": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]

    def get_graph(self, start_id: str = None, depth: int = 2):
        """Get graph data for visualization"""
        cursor = self.conn.cursor()

        if start_id:
            # Get entities connected to start_id
            query = """
            WITH RECURSIVE graph_cte(id, depth, path) AS (
                SELECT ?, 0, ?
                UNION ALL
                SELECT
                    CASE WHEN r.from_id = g.id THEN r.to_id ELSE r.from_id END,
                    g.depth + 1,
                    g.path || ',' || g.id
                FROM relationships r
                JOIN graph_cte g ON r.from_id = g.id OR r.to_id = g.id
                WHERE g.depth < ? AND instr(g.path, g.id) = 0
            )
            SELECT DISTINCT e.* FROM entities e
            JOIN graph_cte g ON e.id = g.id
            """
            cursor.execute(query, (start_id, start_id, depth))
        else:
            # Get all entities
            cursor.execute("SELECT * FROM entities LIMIT 100")

        entities = cursor.fetchall()

        # Get relationships
        cursor.execute("""
        SELECT from_id, to_id, relationship FROM relationships
        WHERE from_id IN (SELECT id FROM entities)
        AND to_id IN (SELECT id FROM entities)
        """)

        relationships = cursor.fetchall()

        return {
            "entities": [
                {
                    "id": e[0],
                    "type": e[1],
                    "value": e[2],
                    "properties": json.loads(e[3]) if e[3] else {}
                }
                for e in entities
            ],
            "relationships": [
                {
                    "from": r[0],
                    "to": r[1],
                    "type": r[2]
                }
                for r in relationships
            ]
        }

# ========== API CLIENTS ==========
class APIClients:
    def __init__(self, config: Config):
        self.config = config
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def shodan_search(self, query: str):
        """Search Shodan - single API call integration!"""
        if not self.config.SHODAN_API_KEY:
            return {"error": "Shodan API key not configured"}

        try:
            url = f"https://api.shodan.io/shodan/host/search?key={self.config.SHODAN_API_KEY}&query={query}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Transform Shodan results to Zenego entities
                    entities = []

                    for match in data.get("matches", []):
                        ip = match.get("ip_str", "")

                        # IP Entity
                        entities.append({
                            "type": "ip",
                            "value": ip,
                            "properties": {
                                "country": match.get("location", {}).get("country_name", ""),
                                "city": match.get("location", {}).get("city", ""),
                                "org": match.get("org", ""),
                                "isp": match.get("isp", ""),
                                "ports": match.get("ports", []),
                                "os": match.get("os", ""),
                                "timestamp": match.get("timestamp", "")
                            },
                            "source": "shodan"
                        })

                        # Port entities
                        for port in match.get("ports", []):
                            entities.append({
                                "type": "port",
                                "value": str(port),
                                "properties": {
                                    "ip": ip,
                                    "service": match.get("data", [{}])[0].get("_shodan", {}).get("module", "")
                                },
                                "source": "shodan"
                            })

                    return {"success": True, "count": len(entities), "entities": entities}
                else:
                    return {"error": f"Shodan API error: {response.status}"}

        except Exception as e:
            return {"error": str(e)}

    async def dns_lookup(self, domain: str):
        """Simple DNS lookup"""
        try:
            import socket

            # Get A records
            ips = socket.gethostbyname_ex(domain)[2]

            # Get MX records
            import dns.resolver
            mx_records = []
            try:
                answers = dns.resolver.resolve(domain, 'MX')
                mx_records = [str(r.exchange) for r in answers]
            except:
                pass

            entities = []

            # Domain entity
            entities.append({
                "type": "domain",
                "value": domain,
                "properties": {},
                "source": "dns"
            })

            # IP entities
            for ip in ips:
                entities.append({
                    "type": "ip",
                    "value": ip,
                    "properties": {"domain": domain},
                    "source": "dns"
                })

            # MX entities
            for mx in mx_records:
                entities.append({
                    "type": "mx",
                    "value": mx,
                    "properties": {"domain": domain},
                    "source": "dns"
                })

            return {"success": True, "entities": entities}

        except Exception as e:
            return {"error": str(e)}

    async def whois_lookup(self, domain: str):
        """WHOIS lookup"""
        try:
            import whois

            w = whois.whois(domain)

            entities = []
            properties = {}

            # Extract WHOIS data
            if w.domain_name:
                properties["domain_name"] = w.domain_name
            if w.registrar:
                properties["registrar"] = w.registrar
            if w.creation_date:
                properties["creation_date"] = str(w.creation_date)
            if w.expiration_date:
                properties["expiration_date"] = str(w.expiration_date)
            if w.name_servers:
                properties["name_servers"] = list(w.name_servers)

            entities.append({
                "type": "domain",
                "value": domain,
                "properties": properties,
                "source": "whois"
            })

            # Registrar entity
            if w.registrar:
                entities.append({
                    "type": "registrar",
                    "value": w.registrar,
                    "properties": {},
                    "source": "whois"
                })

            return {"success": True, "entities": entities}

        except Exception as e:
            return {"error": str(e)}

# ========== TRANSFORM ENGINE ==========
class TransformEngine:
    def __init__(self, db: ZenegoDB, config: Config):
        self.db = db
        self.config = config
        self.transforms = self._load_transforms()

    def _load_transforms(self):
        """Load all available transforms"""
        return {
            "shodan": self._transform_shodan,
            "dns": self._transform_dns,
            "whois": self._transform_whois,
            "expand": self._transform_expand,
            "social": self._transform_social
        }

    async def _transform_shodan(self, input_value: str):
        """Shodan transform - ONE CALL DOES IT ALL!"""
        async with APIClients(self.config) as clients:
            result = await clients.shodan_search(input_value)

            if "error" in result:
                return {"success": False, "error": result["error"]}

            # Save entities to DB
            saved_ids = []
            for entity in result.get("entities", []):
                entity_id = self.db.save_entity(
                    entity["type"],
                    entity["value"],
                    entity.get("properties", {}),
                    entity.get("source", "shodan")
                )
                saved_ids.append(entity_id)

            return {
                "success": True,
                "count": len(saved_ids),
                "entities": saved_ids
            }

    async def _transform_dns(self, input_value: str):
        """DNS transform"""
        async with APIClients(self.config) as clients:
            result = await clients.dns_lookup(input_value)

            if "error" in result:
                return {"success": False, "error": result["error"]}

            # Save to DB
            saved_ids = []
            for entity in result.get("entities", []):
                entity_id = self.db.save_entity(
                    entity["type"],
                    entity["value"],
                    entity.get("properties", {}),
                    entity.get("source", "dns")
                )
                saved_ids.append(entity_id)

            return {
                "success": True,
                "count": len(saved_ids),
                "entities": saved_ids
            }

    async def _transform_whois(self, input_value: str):
        """WHOIS transform"""
        async with APIClients(self.config) as clients:
            result = await clients.whois_lookup(input_value)

            if "error" in result:
                return {"success": False, "error": result["error"]}

            # Save to DB
            saved_ids = []
            for entity in result.get("entities", []):
                entity_id = self.db.save_entity(
                    entity["type"],
                    entity["value"],
                    entity.get("properties", {}),
                    entity.get("source", "whois")
                )
                saved_ids.append(entity_id)

            return {
                "success": True,
                "count": len(saved_ids),
                "entities": saved_ids
            }

    async def _transform_expand(self, input_value: str):
        """Expand entity connections"""
        entities = self.db.search(input_value)

        expanded = []
        for entity in entities:
            # Find related entities
            expanded.append(entity)

        return {
            "success": True,
            "count": len(expanded),
            "entities": expanded
        }

    async def _transform_social(self, input_value: str):
        """Social media lookup (simplified)"""
        # This is a placeholder - add actual social media APIs
        return {
            "success": True,
            "count": 0,
            "entities": [],
            "message": "Social transform requires API keys"
        }

    async def execute(self, transform_name: str, input_value: str):
        """Execute a transform"""
        if transform_name not in self.transforms:
            return {"success": False, "error": f"Transform '{transform_name}' not found"}

        return await self.transforms[transform_name](input_value)

# ========== EXPORTERS ==========
class Exporters:
    @staticmethod
    def to_json(graph_data: Dict, filename: str = None):
        """Export to JSON"""
        if filename:
            with open(filename, 'w') as f:
                json.dump(graph_data, f, indent=2)
            return f"Exported to {filename}"
        return json.dumps(graph_data, indent=2)

    @staticmethod
    def to_csv(graph_data: Dict, filename: str = None):
        """Export to CSV"""
        import csv

        entities = graph_data.get("entities", [])

        csv_data = "type,value,properties\n"
        for entity in entities:
            props = json.dumps(entity.get("properties", {}))
            csv_data += f'{entity["type"]},"{entity["value"]}","{props}"\n'

        if filename:
            with open(filename, 'w') as f:
                f.write(csv_data)
            return f"Exported to {filename}"

        return csv_data

    @staticmethod
    def to_graphml(graph_data: Dict, filename: str = None):
        """Export to GraphML (for Gephi)"""
        entities = graph_data.get("entities", [])
        relationships = graph_data.get("relationships", [])

        graphml = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
    <key id="type" for="node" attr.name="type" attr.type="string"/>
    <key id="value" for="node" attr.name="value" attr.type="string"/>
    <graph id="G" edgedefault="directed">
"""

        # Add nodes
        for i, entity in enumerate(entities):
            graphml += f'    <node id="n{i}">\n'
            graphml += f'      <data key="type">{entity["type"]}</data>\n'
            graphml += f'      <data key="value">{entity["value"]}</data>\n'
            graphml += '    </node>\n'

        # Add edges
        for i, rel in enumerate(relationships):
            from_idx = next(idx for idx, e in enumerate(entities) if e["id"] == rel["from"])
            to_idx = next(idx for idx, e in enumerate(entities) if e["id"] == rel["to"])

            graphml += f'    <edge id="e{i}" source="n{from_idx}" target="n{to_idx}">\n'
            graphml += f'      <data key="type">{rel["type"]}</data>\n'
            graphml += '    </edge>\n'

        graphml += """  </graph>
</graphml>"""

        if filename:
            with open(filename, 'w') as f:
                f.write(graphml)
            return f"Exported to {filename}"

        return graphml

# ========== COMMAND LINE INTERFACE ==========
class ZenegoCLI:
    def __init__(self):
        self.config = self.load_config()
        self.db = ZenegoDB()
        self.engine = TransformEngine(self.db, self.config)
        self.exporters = Exporters()

    def load_config(self):
        """Load configuration from file or environment"""
        config = Config()

        # Try to load from config file
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path) as f:
                file_config = json.load(f)
                for key, value in file_config.items():
                    if hasattr(config, key):
                        setattr(config, key, value)

        # Override with environment variables
        import os
        if os.getenv("SHODAN_API_KEY"):
            config.SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")

        return config

    def print_banner(self):
        """Print Zenego banner"""
        banner = """
╭────────────────────────────────────────╮
│          ZENEGO - Zeno Maltego         │
│     Ultra-lightweight OSINT CLI        │
│         Termux Compatible ✓            │
╰────────────────────────────────────────╯
"""
        print(banner)

    async def run_transform(self, transform: str, value: str):
        """Run a single transform"""
        print(f"\n[→] Running {transform} on: {value}")

        result = await self.engine.execute(transform, value)

        if result.get("success"):
            print(f"[✓] Success! Found {result.get('count', 0)} entities")

            # Show found entities
            if "entities" in result:
                entities = result["entities"]
                if isinstance(entities[0], str):  # IDs
                    for eid in entities[:5]:  # Show first 5
                        # Look up entity details
                        search = self.db.search(eid)
                        if search:
                            entity = search[0]
                            print(f"  • [{entity['type']}] {entity['value']}")
                else:  # Full entities
                    for entity in entities[:5]:
                        print(f"  • [{entity['type']}] {entity['value']}")

                if len(entities) > 5:
                    print(f"  ... and {len(entities) - 5} more")
        else:
            print(f"[✗] Error: {result.get('error', 'Unknown error')}")

    async def interactive_mode(self):
        """Interactive CLI mode"""
        self.print_banner()

        while True:
            print("\n" + "="*50)
            print("[1] Run Transform")
            print("[2] Search Database")
            print("[3] View Graph")
            print("[4] Export Data")
            print("[5] Configure API Keys")
            print("[6] Clear Database")
            print("[0] Exit")

            try:
                choice = input("\nSelect option: ").strip()

                if choice == "1":
                    print("\nAvailable Transforms:")
                    print("  • shodan  - Search Shodan (IP/Domain)")
                    print("  • dns     - DNS lookup")
                    print("  • whois   - WHOIS lookup")
                    print("  • expand  - Expand connections")

                    transform = input("\nTransform: ").strip()
                    value = input("Input value: ").strip()

                    await self.run_transform(transform, value)

                elif choice == "2":
                    query = input("\nSearch for: ").strip()
                    results = self.db.search(query)

                    print(f"\nFound {len(results)} results:")
                    for result in results:
                        print(f"  [{result['type']}] {result['value']}")

                elif choice == "3":
                    query = input("\nStart entity (leave empty for all): ").strip()

                    if query:
                        results = self.db.search(query)
                        if results:
                            start_id = results[0]["id"]
                            graph = self.db.get_graph(start_id, depth=2)
                        else:
                            print("[!] Entity not found")
                            continue
                    else:
                        graph = self.db.get_graph()

                    print(f"\nGraph contains:")
                    print(f"  • {len(graph['entities'])} entities")
                    print(f"  • {len(graph['relationships'])} relationships")

                    # Show sample
                    for entity in graph['entities'][:5]:
                        print(f"    [{entity['type']}] {entity['value']}")

                elif choice == "4":
                    print("\nExport Formats:")
                    print("  1. JSON")
                    print("  2. CSV")
                    print("  3. GraphML (for Gephi)")

                    fmt = input("\nFormat: ").strip()
                    graph = self.db.get_graph()

                    if fmt == "1":
                        output = self.exporters.to_json(graph)
                        filename = f"zenego_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(filename, 'w') as f:
                            f.write(output)
                        print(f"[✓] Exported to {filename}")

                    elif fmt == "2":
                        filename = f"zenego_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        self.exporters.to_csv(graph, filename)
                        print(f"[✓] Exported to {filename}")

                    elif fmt == "3":
                        filename = f"zenego_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.graphml"
                        self.exporters.to_graphml(graph, filename)
                        print(f"[✓] Exported to {filename}")

                elif choice == "5":
                    print("\nConfigure API Keys:")
                    print("Current config:")
                    for key, value in asdict(self.config).items():
                        if "KEY" in key:
                            masked = value[:4] + "*" * (len(value) - 4) if value else "Not set"
                            print(f"  {key}: {masked}")

                    key_name = input("\nAPI key to set (e.g., SHODAN_API_KEY): ").strip()
                    if hasattr(self.config, key_name):
                        value = input(f"Value for {key_name}: ").strip()
                        setattr(self.config, key_name, value)

                        # Save to config file
                        config_dict = asdict(self.config)
                        with open("config.json", 'w') as f:
                            json.dump(config_dict, f, indent=2)

                        print("[✓] Configuration saved")
                    else:
                        print("[!] Invalid config key")

                elif choice == "6":
                    confirm = input("\nClear all data? (y/N): ").strip().lower()
                    if confirm == 'y':
                        cursor = self.db.conn.cursor()
                        cursor.execute("DELETE FROM entities")
                        cursor.execute("DELETE FROM relationships")
                        self.db.conn.commit()
                        print("[✓] Database cleared")

                elif choice == "0":
                    print("\nGoodbye! 👋")
                    break

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"[!] Error: {e}")

# ========== MAIN ==========
def main():
    parser = argparse.ArgumentParser(description="Zenego - Lightweight OSINT CLI")

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Transform command
    transform_parser = subparsers.add_parser('transform', help='Run a transform')
    transform_parser.add_argument('transform', help='Transform name')
    transform_parser.add_argument('value', help='Input value')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search database')
    search_parser.add_argument('query', help='Search query')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('format', choices=['json', 'csv', 'graphml'],
                               help='Export format')
    export_parser.add_argument('--output', '-o', help='Output filename')

    # Interactive mode (default)
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')

    args = parser.parse_args()

    zenego = ZenegoCLI()

    if args.command == 'transform':
        asyncio.run(zenego.run_transform(args.transform, args.value))

    elif args.command == 'search':
        results = zenego.db.search(args.query)
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"[{result['type']}] {result['value']}")

    elif args.command == 'export':
        graph = zenego.db.get_graph()

        if args.format == 'json':
            output = zenego.exporters.to_json(graph, args.output)
            if not args.output:
                print(output)

        elif args.format == 'csv':
            output = zenego.exporters.to_csv(graph, args.output)
            if not args.output:
                print(output)

        elif args.format == 'graphml':
            output = zenego.exporters.to_graphml(graph, args.output)
            if not args.output:
                print(output)

    else:
        # Default to interactive mode
        asyncio.run(zenego.interactive_mode())

if __name__ == "__main__":
    main()
