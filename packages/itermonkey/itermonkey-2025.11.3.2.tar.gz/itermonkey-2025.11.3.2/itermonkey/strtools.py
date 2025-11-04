"""Submodule for string manipulation and conversion utilities."""
import datetime

def find_all(query: str, string: str) -> list[int]:
    """Find all occurrences of `query` in `string` and return their starting indices."""
    indices = []
    start = 0
    while 1:
        start = string.find(query, start)
        if start == -1:
            break
        indices.append(start)
        start += len(query)  # Move past the last found occurrence
    return indices

def parse_datetime(s: str | datetime.datetime) -> datetime.datetime:
    """Parses a string into a datetime object. Accepts various common date formats."""
    if isinstance(s, datetime.datetime):
        return s
    
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(
        f"Invalid date format: {s!r}. Expected YYYY-MM-DD or ISO-like format."
    )

if __name__ == "__main__":
    # Example usage
    test_string = "This is a test. This test is only a test."
    query = "test"
    print(f"Occurrences of '{query}' in the string: {find_all(query, test_string)}")

    date_str = "2023-10-05T14:30:00"
    parsed_date = parse_datetime(date_str)
    print(f"Parsed datetime: {parsed_date}")