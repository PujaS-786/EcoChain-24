import os
import sqlite3
import unittest
import tempfile
import json
from ecochain.db import init_db, log_audit_entry, verify_audit_trail_integrity
import ecochain.db
from ecochain.mcp import authorize_agent, call_mcp_tool
from ecochain.agents.orchestrator import OrchestratorAgent

class TestEcoChainSystem(unittest.TestCase):
    def setUp(self):
        # Override the database file path to a temp file for isolated testing
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        ecochain.db.DB_FILE = self.db_path
        init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_initialization(self):
        """Verifies that all specified tables are created in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn("activity_records", tables)
        self.assertIn("emissions_records", tables)
        self.assertIn("supplier_profiles", tables)
        self.assertIn("anomalies", tables)
        self.assertIn("compliance_disclosures", tables)
        self.assertIn("audit_trail", tables)

    def test_cryptographic_audit_log_integrity(self):
        """Tests log chain initialization, appends, and tamper detection."""
        # 1. Chain starts valid
        is_valid, errors = verify_audit_trail_integrity()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # 2. Append some entries
        log_audit_entry("ingest", "test_action_1", {"data": "foo"})
        log_audit_entry("calculate", "test_action_2", {"result": 42})
        
        is_valid, errors = verify_audit_trail_integrity()
        self.assertTrue(is_valid)

        # 3. Simulate tampering by modifying an action manually in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE audit_trail SET action = 'tampered_action' WHERE entry_id = 1")
        conn.commit()
        conn.close()

        # Chain should now fail validation
        is_valid, errors = verify_audit_trail_integrity()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Content hash mismatch" in err for err in errors))

    def test_mcp_token_authorization(self):
        """Tests that agents are blocked from calling tools outside their namespaces."""
        # Ingestion agent calls ingest tool -> OK
        self.assertTrue(authorize_agent("ingest", "tok_ingest_secret_2234", "ecochain.ingest.normalize_record"))
        # Ingestion agent calls report tool -> Blocked
        self.assertFalse(authorize_agent("ingest", "tok_ingest_secret_2234", "ecochain.report.compose_document"))
        # Ingestion agent calls audit log write -> OK
        self.assertTrue(authorize_agent("ingest", "tok_ingest_secret_2234", "ecochain.log.write"))
        
        # Invalid token -> Blocked
        self.assertFalse(authorize_agent("ingest", "wrong_token", "ecochain.ingest.normalize_record"))
        
        # Orchestrator calls any tool -> OK
        self.assertTrue(authorize_agent("orchestrator", "tok_orchestrator_secret_1234", "ecochain.report.compose_document"))

    def test_end_to_end_orchestration(self):
        """Runs the complete multi-agent pipeline and verifies calculation metrics."""
        orch = OrchestratorAgent()
        
        # Ingest raw activity records
        raw_inputs = [
            # Scope 1 direct fuel
            {
                "supplier_id": "sup_alpha_logistics",
                "period": "2024-Q1",
                "activity_type": "fuel",
                "quantity": 500.0,
                "unit": "L",
                "country": "US",
                "data_source": "erp_import",
                "details": {"fuel_type": "diesel"}
            },
            # Scope 2 location-based electricity (from country DE)
            {
                "supplier_id": "sup_beta_steel",
                "period": "2024-Q1",
                "activity_type": "electricity",
                "quantity": 1000.0,
                "unit": "kWh",
                "country": "DE",
                "data_source": "utility_api",
                "details": {"tariff_type": "standard"}
            }
        ]
        
        suppliers_config = [
            {"supplier_id": "sup_alpha_logistics", "name": "Alpha Logistics Co"},
            {"supplier_id": "sup_beta_steel", "name": "Beta Steel Ltd"}
        ]
        
        res = orch.run_pipeline("2024-Q1", raw_records=raw_inputs, active_suppliers=suppliers_config)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["processed_records"], 2)
        self.assertEqual(res["emissions_calculated"], 2)

        # Check DB to verify Scope values were calculated correctly
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify direct Scope 1 calculation (500L diesel * 2.68 kg CO2e/L = 1340 kg = 1.34 t)
        cursor.execute("SELECT co2e FROM emissions_records WHERE scope = 1")
        s1_em = cursor.fetchone()
        self.assertIsNotNone(s1_em)
        self.assertAlmostEqual(s1_em[0], 500.0 * 2.68)

        # Verify electricity grid calculation (1000kWh * 0.35 grid factor = 350 kg)
        cursor.execute("SELECT co2e, co2e_market FROM emissions_records WHERE scope = 2")
        s2_em = cursor.fetchone()
        self.assertIsNotNone(s2_em)
        self.assertAlmostEqual(s2_em[0], 1000.0 * 0.35)
        # Location-based default matches market-based
        self.assertAlmostEqual(s2_em[1], 1000.0 * 0.35)
        
        # Verify supplier profile exists
        cursor.execute("SELECT tier, trend FROM supplier_profiles WHERE supplier_id = 'sup_beta_steel'")
        prof = cursor.fetchone()
        self.assertIsNotNone(prof)
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
