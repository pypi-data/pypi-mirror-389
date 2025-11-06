import pytest
from chatterpy_mistral.banter import banter


class TestBanter:

    # Intensity level tests
    def test_mild_intensity_works(self):
        mild_keywords = ["penny", "drizzle", "software", "secret", "loading"]
        found = False
        for _ in range(15):
            if any(word in banter("mild").lower() for word in mild_keywords):
                found = True
                break
        assert found, "Expected mild-specific content"

    def test_medium_intensity_works(self):
        """Test medium intensity returns appropriate content."""
        medium_keywords = ["envy", "far someday", "left hand", "participation", "exit"]
        found = False
        for _ in range(15):
            if any(word in banter("medium").lower() for word in medium_keywords):
                found = True
                break
        assert found, "Expected medium-specific content"

    def test_intense_intensity_works(self):
        """Test intense intensity returns corresponding content."""
        intense_keywords = ["cloud", "bad luck", "lost", "tree", "monday", "before picture"]
        found = False
        for _ in range(15):
            if any(word in banter("intense").lower() for word in intense_keywords):
                found = True
                break
        assert found, "Expected intense-specific content"

    # Error handling tests
    def test_invalid_intensity_raises_error(self):
        with pytest.raises(KeyError):
            banter("extreme")

    def test_empty_intensity_raises_error(self):
        with pytest.raises(KeyError):
            banter("")

    def test_wrong_type_intensity_raises_error(self):
        with pytest.raises(KeyError):
            banter(123)