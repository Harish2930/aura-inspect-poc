import tempfile
from pathlib import Path

from app.database.inspection_repository import InspectionRepository
from app.models.inspection_result import InspectionResult


def test_save_and_list_recent():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        repo = InspectionRepository(db_path)

        result = InspectionResult(
            component="ALUMINIUM_DIE_CAST_PART",
            condition="GOOD",
            reason="No visible defect.",
            confidence=0.95,
        )
        repo.save(result)

        history = repo.list_recent()
        assert len(history) == 1
        assert history[0]["inspection_id"] == result.inspection_id
        assert history[0]["condition"] == "GOOD"
