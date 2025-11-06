"""
Test to verify AI auditor agent uses cross-file analysis.

This demonstrates that findings from the AI auditor get enriched with
AST-based cross-file call graph traces.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from securecli.schemas.findings import Finding, AnalysisContext, CVSSv4
from securecli.analysis import annotate_cross_file_context


def test_ai_with_cross_file_analysis():
    """Demonstrate AI findings get enriched with cross-file traces."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create a simple multi-file codebase
        (repo_root / "app.py").write_text("""
def handle_upload(file_data):
    # Processes user upload
    result = validate_file(file_data)
    return save_upload(result)
""")
        
        (repo_root / "validator.py").write_text("""
def validate_file(file_data):
    # Basic validation
    return check_file_type(file_data)
""")
        
        (repo_root / "storage.py").write_text("""
def check_file_type(file_data):
    # Type checking
    return store_file(file_data)

def store_file(file_data):
    # External storage
    return True
""")
        
        # Simulate AI agent discovering a vulnerability
        # (In real usage, this would come from the AI auditor agent)
        ai_finding = Finding(
            id="ai-001",
            file="app.py",
            title="Insufficient File Upload Validation",
            description="AI detected that file upload validation is insufficient",
            lines="4",
            impact="Malicious files could be uploaded and executed",
            severity="High",
            confidence_score=85,
            cvss_v4=CVSSv4(
                score=7.5,
                vector="CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N"
            ),
            owasp=["OWASP-A08"],
            cwe=["CWE-434"],
            snippet="result = validate_file(file_data)",
            recommendation="Implement comprehensive file validation including type, size, and content checks",
            sample_fix="Use allowlist for file types, scan for malicious content",
            poc="Upload executable disguised as image",
            references=["https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload"],
        )
        
        findings = [ai_finding]
        
        print("\n" + "="*70)
        print("AI AUDITOR + CROSS-FILE ANALYSIS INTEGRATION TEST")
        print("="*70 + "\n")
        
        print("Repository Structure:")
        print("  app.py        - Entry point: handle_upload() receives user files")
        print("  validator.py  - Validation: validate_file() checks file")
        print("  storage.py    - Storage: store_file() saves to disk")
        print()
        
        print(f"AI Finding (before enrichment):")
        print(f"  Title: {ai_finding.title}")
        print(f"  File: {ai_finding.file}:{ai_finding.lines}")
        print(f"  Severity: {ai_finding.severity}")
        print(f"  Cross-file traces: {len(ai_finding.cross_file)} traces")
        print()
        
        # Enrich AI findings with cross-file analysis
        # (This happens automatically in the auditor agent's perform_audit method)
        print("Enriching AI finding with AST-based cross-file analysis...")
        annotate_cross_file_context(repo_root, findings)
        
        print()
        print(f"AI Finding (after enrichment):")
        print(f"  Title: {ai_finding.title}")
        print(f"  Cross-file traces: {len(ai_finding.cross_file)} traces")
        print()
        
        if ai_finding.cross_file:
            print("Cross-File Call Graph Traces:")
            for i, trace in enumerate(ai_finding.cross_file, 1):
                print(f"  {i}. {trace}")
            print()
            
            traces_str = " ".join(ai_finding.cross_file)
            
            # Verify we traced through the files
            has_app = "app.py" in traces_str
            has_validator = "validator.py" in traces_str or "validate_file" in traces_str
            has_storage = "storage.py" in traces_str or "store_file" in traces_str
            
            components = []
            if has_app:
                components.append("Entry Point")
            if has_validator:
                components.append("Validator")
            if has_storage:
                components.append("Storage")
            
            print(f"Components traced: {' → '.join(components)}")
            print()
            
            if len(components) >= 2:
                print("✓ AI finding successfully enriched with cross-file traces!")
                print(f"  The AI identified the vulnerability, and static analysis")
                print(f"  traced its impact across {len(components)} components.")
            else:
                print(f"✓ Traced through {len(components)} component(s)")
        else:
            print("⚠ No cross-file traces generated")
            print("  (The vulnerable function may not make cross-file calls)")
        
        print("\n" + "="*70)
        print("\nIntegration Summary:")
        print("• AI Auditor discovers vulnerabilities using LLM reasoning")
        print("• AST-based cross-file analyzer traces call graphs")
        print("• Findings are automatically enriched with execution paths")
        print("• Combined AI insights + static analysis for comprehensive coverage")
        print("="*70 + "\n")


if __name__ == "__main__":
    test_ai_with_cross_file_analysis()
