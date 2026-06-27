from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "data" / "docs"

PRODUCT_DOCS = {
    "Product A": DOCS_DIR / "產品A_AlphaBuds_X1_規格與認證.md",
    "Product B": DOCS_DIR / "產品B_BetaBuds_X2_規格與認證.md",
    "Product C": DOCS_DIR / "產品C_GammaHub_C1_規格與認證.md",
    "Product D": DOCS_DIR / "產品D_DeltaCam_D4_規格與認證.md",
}

SHARED_DOCS = {
    "region matrix": DOCS_DIR / "區域認證矩陣_EU_US_JP.md",
    "wireless SOP": DOCS_DIR / "無線測試與認證Scoping_SOP.md",
    "risk policy": DOCS_DIR / "產品認證風險邊界Policy.md",
    "FAQ": DOCS_DIR / "FAQ_產品認證與多輪問答.md",
}


def read_doc(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ProductCertificationCorpusIntegrityTests(unittest.TestCase):
    def test_expected_simulated_corpus_files_exist_under_data_docs(self) -> None:
        for label, path in {**PRODUCT_DOCS, **SHARED_DOCS}.items():
            with self.subTest(label=label, path=path.name):
                self.assertTrue(path.exists(), f"Missing expected corpus file: {path}")
                self.assertEqual(DOCS_DIR, path.parent)

    def test_every_new_corpus_document_declares_simulated_demo_material(self) -> None:
        for label, path in {**PRODUCT_DOCS, **SHARED_DOCS}.items():
            content = read_doc(path)
            with self.subTest(label=label):
                self.assertIn("模擬文件聲明", content)
                self.assertIn("demo", content.lower())
                self.assertIn("不代表真實", content)
                self.assertRegex(content, r"不得對外承諾|不得.*保證")

    def test_product_a_is_bluetooth_only(self) -> None:
        content = read_doc(PRODUCT_DOCS["Product A"])
        self.assertIn("AlphaBuds X1", content)
        self.assertIn("Product A", content)
        self.assertIn("Bluetooth only", content)
        self.assertIn("Bluetooth version | 5.3", content)
        self.assertIn("2.4 GHz ISM band", content)
        self.assertIn("Wi-Fi | 無", content)
        self.assertIn("沒有 Wi-Fi", content)

    def test_product_b_has_bluetooth_plus_proprietary_low_power_24ghz_mode(self) -> None:
        content = read_doc(PRODUCT_DOCS["Product B"])
        self.assertIn("BetaBuds X2", content)
        self.assertIn("Product B", content)
        self.assertIn("Bluetooth + low-power proprietary 2.4 GHz mode", content)
        self.assertIn("Bluetooth version | 5.4", content)
        self.assertIn("Low-latency proprietary mode", content)
        self.assertRegex(content, r"不能直接(沿用|套用) Product A")

    def test_product_c_has_no_wireless_or_radio_module(self) -> None:
        content = read_doc(PRODUCT_DOCS["Product C"])
        self.assertIn("GammaHub C1", content)
        self.assertIn("Product C", content)
        self.assertIn("無線功能 | 無", content)
        self.assertIn("Radio module | 無", content)
        self.assertIn("沒有 radio module", content)
        self.assertIn("不應把 Bluetooth radio test", content)

    def test_product_d_has_wifi_and_bluetooth(self) -> None:
        content = read_doc(PRODUCT_DOCS["Product D"])
        self.assertIn("DeltaCam D4", content)
        self.assertIn("Product D", content)
        self.assertIn("Wi-Fi 6 + Bluetooth setup mode", content)
        self.assertIn("2.4 GHz and 5 GHz Wi-Fi", content)
        self.assertIn("Bluetooth setup mode", content)
        self.assertIn("privacy/security claims", content)

    def test_region_matrix_covers_eu_us_and_japan(self) -> None:
        content = read_doc(SHARED_DOCS["region matrix"])
        self.assertIn("EU", content)
        self.assertIn("CE / RED", content)
        self.assertIn("US", content)
        self.assertIn("FCC Part 15", content)
        self.assertIn("Japan", content)
        self.assertIn("TELEC / MIC-style radio review", content)

    def test_risk_policy_forbids_certification_guarantees(self) -> None:
        content = read_doc(SHARED_DOCS["risk policy"])
        self.assertIn("禁止行為", content)
        self.assertIn("保證 CE、RED、FCC、TELEC", content)
        self.assertIn("pass/fail", content)
        self.assertIn("不得對外承諾", content)
        self.assertIn("升級到 human review", content)

    def test_faq_contains_multi_turn_friendly_examples(self) -> None:
        content = read_doc(SHARED_DOCS["FAQ"])
        expected_examples = [
            "AlphaBuds X1 如果要出口到歐洲",
            "如果改成 BetaBuds X2",
            "那日本呢",
            "剛才你參考了哪些文件",
            "可以跟客戶說一定會通過認證嗎",
            "GammaHub C1 沒有無線模組",
            "DeltaCam D4 同時有 Wi-Fi 和 Bluetooth",
        ]
        for example in expected_examples:
            with self.subTest(example=example):
                self.assertIn(example, content)


if __name__ == "__main__":
    unittest.main()
